"""Trello (REST): card short-link keys; attach PR, comment, move to a list.

Keys: a trello.com/c/<id> URL, or a card-<id> / trello-<id> token in the branch.
"""

from __future__ import annotations

import logging
import os
import re

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")

API = "https://api.trello.com/1"


class TrelloTracker(Tracker):
    name = "trello"
    default_key_pattern = r"(?:trello\.com/c/|card[-_/]|trello[-_/])([A-Za-z0-9]{8,})"
    target_envs = {
        "in_review": ("TRELLO_LIST_IN_REVIEW", "TRACKER_STATE_IN_REVIEW"),
        "done": ("TRELLO_LIST_DONE", "TRACKER_STATE_DONE"),
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.key = os.environ.get("TRELLO_KEY")
        self.token = os.environ.get("TRELLO_TOKEN")
        if not self.key or not self.token:
            raise RuntimeError("TRELLO_KEY and TRELLO_TOKEN are required")
        self.session = make_session(headers={"Accept": "application/json"})
        self._card_rx = re.compile(self.key_pattern)

    def extract_keys(self, *texts):
        keys = []
        for text in texts:
            for match in self._card_rx.finditer(text or ""):
                keys.append(match.group(1))
        return self._ordered_unique(keys)

    def _params(self, **extra) -> dict:
        params = {"key": self.key, "token": self.token}
        params.update(extra)
        return params

    def issue_exists(self, key: str) -> bool:
        try:
            resp = self.session.get(
                f"{API}/cards/{key}",
                params=self._params(fields="id"),
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("verify card %s failed: %s", key, exc)
            return False

    def link_pr(self, key: str, pr: PRContext) -> bool:
        try:
            resp = self.session.post(
                f"{API}/cards/{key}/attachments",
                params=self._params(url=pr.html_url, name=f"GitHub PR #{pr.number}"),
                timeout=self.timeout,
            )
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("link card %s failed: %s", key, exc)
            return False

    def comment(self, key: str, text: str) -> bool:
        try:
            resp = self.session.post(
                f"{API}/cards/{key}/actions/comments",
                params=self._params(text=text),
                timeout=self.timeout,
            )
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("comment card %s failed: %s", key, exc)
            return False

    def transition(self, key: str, target: str) -> bool:
        list_id = self.state_for(target)
        if not list_id:
            return True
        try:
            resp = self.session.put(
                f"{API}/cards/{key}",
                params=self._params(idList=list_id),
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("transition card %s failed: %s", key, exc)
            return False
