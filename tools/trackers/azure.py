"""Azure Boards (REST): AB#123 keys; hyperlink, comment, System.State (PAT)."""

from __future__ import annotations

import logging
import os
import re

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")

API = "api-version=7.0"


class AzureBoardsTracker(Tracker):
    name = "azure"
    default_key_pattern = r"AB#(\d+)"
    target_envs = {
        "in_review": ("AZURE_STATE_IN_REVIEW", "TRACKER_STATE_IN_REVIEW"),
        "done": ("AZURE_STATE_DONE", "TRACKER_STATE_DONE"),
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.org = (os.environ.get("AZURE_ORG_URL") or "").rstrip("/")
        self.project = os.environ.get("AZURE_PROJECT", "")
        pat = os.environ.get("AZURE_PAT")
        if not self.org or not self.project or not pat:
            raise RuntimeError("AZURE_ORG_URL, AZURE_PROJECT, AZURE_PAT are required")
        self.session = make_session(
            headers={"Accept": "application/json"}, auth=("", pat)
        )

    def extract_keys(self, *texts):
        seen, out = set(), []
        rx = re.compile(r"AB#(\d+)")
        branch_rx = re.compile(r"(?:^|[/_-])(\d+)")
        for index, text in enumerate(texts):
            if not text:
                continue
            found = rx.findall(text)
            if not found and index == 0:
                found = branch_rx.findall(text)
            for num in found:
                if num not in seen:
                    seen.add(num)
                    out.append(num)
        return out

    def _wit(self, key: str) -> str:
        return f"{self.org}/{self.project}/_apis/wit/workitems/{key}?{API}"

    def issue_exists(self, key: str) -> bool:
        try:
            resp = self.session.get(self._wit(key), timeout=self.timeout)
            return resp.status_code == 200
        except Exception as exc:
            logger.error("verify AB#%s failed: %s", key, exc)
            return False

    def link_pr(self, key: str, pr: PRContext) -> bool:
        patch = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "Hyperlink",
                    "url": pr.html_url,
                    "attributes": {"comment": f"GitHub PR #{pr.number}"},
                },
            }
        ]
        try:
            resp = self.session.patch(
                self._wit(key),
                json=patch,
                headers={"Content-Type": "application/json-patch+json"},
                timeout=self.timeout,
            )
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("link AB#%s failed: %s", key, exc)
            return False

    def comment(self, key: str, text: str) -> bool:
        url = (
            f"{self.org}/{self.project}/_apis/wit/workItems/{key}/comments"
            "?api-version=7.0-preview.3"
        )
        try:
            resp = self.session.post(url, json={"text": text}, timeout=self.timeout)
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("comment AB#%s failed: %s", key, exc)
            return False

    def transition(self, key: str, target: str) -> bool:
        wanted = self.state_for(target)
        if not wanted:
            return True
        patch = [{"op": "add", "path": "/fields/System.State", "value": wanted}]
        try:
            resp = self.session.patch(
                self._wit(key),
                json=patch,
                headers={"Content-Type": "application/json-patch+json"},
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("transition AB#%s failed: %s", key, exc)
            return False
