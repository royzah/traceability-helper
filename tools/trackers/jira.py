"""Jira: Cloud (REST v3, ADF) and Data Center (REST v2). Basic or bearer auth."""

from __future__ import annotations

import logging
import os

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")


class JiraTracker(Tracker):
    name = "jira"
    target_envs = {
        "in_review": ("JIRA_TRANSITION_IN_REVIEW", "TRACKER_STATE_IN_REVIEW"),
        "done": ("JIRA_TRANSITION_DONE", "TRACKER_STATE_DONE"),
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = (os.environ.get("JIRA_BASE_URL") or "").rstrip("/")
        self.api_version = os.environ.get("JIRA_API_VERSION", "3")
        email = os.environ.get("JIRA_USER_EMAIL")
        token = os.environ.get("JIRA_API_TOKEN")
        if not self.base_url or not token:
            raise RuntimeError("JIRA_BASE_URL and JIRA_API_TOKEN are required")

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if os.environ.get("JIRA_AUTH", "basic").lower() == "bearer":
            headers["Authorization"] = f"Bearer {token}"
            auth = None
        else:
            auth = (email, token)
        self.session = make_session(headers=headers, auth=auth)

    def _api(self, path: str) -> str:
        return f"{self.base_url}/rest/api/{self.api_version}/{path}"

    def issue_exists(self, key: str) -> bool:
        try:
            resp = self.session.get(self._api(f"issue/{key}"), timeout=self.timeout)
            return resp.status_code == 200
        except Exception as exc:
            logger.error("verify %s failed: %s", key, exc)
            return False

    def link_pr(self, key: str, pr: PRContext) -> bool:
        url = self._api(f"issue/{key}/remotelink")
        global_id = f"github-pr-{pr.repo}-{pr.number}"
        payload = {
            "globalId": global_id,
            "relationship": "Pull Request",
            "object": {
                "url": pr.html_url,
                "title": f"GitHub PR #{pr.number}: {pr.title}",
                "status": {"resolved": pr.merged},
            },
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code in (200, 201):
                logger.info("linked PR to %s", key)
                return True
            logger.warning("link %s failed: %s %s", key, resp.status_code, resp.text)
        except Exception as exc:
            logger.error("link %s failed: %s", key, exc)
        return False

    def _comment_body(self, text: str) -> dict:
        if self.api_version == "2":
            return {"body": text}
        return {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": text}]}
                ],
            }
        }

    def comment(self, key: str, text: str) -> bool:
        url = self._api(f"issue/{key}/comment")
        try:
            resp = self.session.post(
                url, json=self._comment_body(text), timeout=self.timeout
            )
            if resp.status_code in (200, 201):
                return True
            logger.warning("comment %s failed: %s", key, resp.status_code)
        except Exception as exc:
            logger.error("comment %s failed: %s", key, exc)
        return False

    def transition(self, key: str, target: str) -> bool:
        wanted = self.state_for(target)
        if not wanted:
            return True
        url = self._api(f"issue/{key}/transitions")
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning("transitions for %s unavailable", key)
                return False
            for trans in resp.json().get("transitions", []):
                if str(trans["id"]) == str(wanted) or (
                    trans["name"].lower() == str(wanted).lower()
                ):
                    post = self.session.post(
                        url,
                        json={"transition": {"id": trans["id"]}},
                        timeout=self.timeout,
                    )
                    if post.status_code in (200, 204):
                        logger.info("transitioned %s to '%s'", key, trans["name"])
                        return True
                    logger.warning("transition %s failed: %s", key, post.status_code)
                    return False
            logger.info("transition '%s' not available for %s", wanted, key)
            return True
        except Exception as exc:
            logger.error("transition %s failed: %s", key, exc)
            return False
