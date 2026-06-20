"""YouTrack (REST): PROJ-123 keys; comment and "State <name>" command."""

from __future__ import annotations

import logging
import os

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")


class YouTrackTracker(Tracker):
    name = "youtrack"
    target_envs = {
        "in_review": ("YOUTRACK_STATE_IN_REVIEW", "TRACKER_STATE_IN_REVIEW"),
        "done": ("YOUTRACK_STATE_DONE", "TRACKER_STATE_DONE"),
    }

    def __init__(self, config: dict):
        super().__init__(config)
        base = (os.environ.get("YOUTRACK_BASE_URL") or "").rstrip("/")
        token = os.environ.get("YOUTRACK_TOKEN")
        if not base or not token:
            raise RuntimeError("YOUTRACK_BASE_URL and YOUTRACK_TOKEN are required")
        self.api = f"{base}/api"
        self.session = make_session(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def issue_exists(self, key: str) -> bool:
        try:
            resp = self.session.get(
                f"{self.api}/issues/{key}",
                params={"fields": "idReadable"},
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("verify %s failed: %s", key, exc)
            return False

    def link_pr(self, key: str, pr: PRContext) -> bool:
        return True

    def comment(self, key: str, text: str) -> bool:
        try:
            resp = self.session.post(
                f"{self.api}/issues/{key}/comments",
                json={"text": text},
                timeout=self.timeout,
            )
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("comment %s failed: %s", key, exc)
            return False

    def transition(self, key: str, target: str) -> bool:
        wanted = self.state_for(target)
        if not wanted:
            return True
        try:
            resp = self.session.post(
                f"{self.api}/commands",
                json={"query": f"State {wanted}", "issues": [{"idReadable": key}]},
                timeout=self.timeout,
            )
            return resp.status_code in (200, 204)
        except Exception as exc:
            logger.error("transition %s failed: %s", key, exc)
            return False
