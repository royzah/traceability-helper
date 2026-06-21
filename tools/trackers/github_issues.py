"""GitHub Issues: "#123" or a leading branch number. Native cross-ref;
merge closes the issue, open can apply a label.
"""

from __future__ import annotations

import logging
import os
import re

from .base import BRANCH_NUMBER_RE, PRContext, Tracker, make_session

logger = logging.getLogger("traceability")

# GitHub's auto-close keywords; only these (or the branch issue) may close.
CLOSING_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*:?\s*#(\d+)", re.IGNORECASE
)
HASH_RE = re.compile(r"#(\d+)")


class GitHubIssuesTracker(Tracker):
    name = "github"
    default_key_pattern = r"\d+"

    def __init__(self, config: dict):
        super().__init__(config)
        self.api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is required for the github provider")
        self.session = make_session(
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        # Set by extract_keys; gate which issues a merge may close.
        self._closing: set = set()
        self._branch: set = set()

    def extract_keys(self, *texts):
        self._closing = set()
        self._branch = set()
        keys = []
        for index, text in enumerate(texts):
            if not text:
                continue
            self._closing.update(CLOSING_RE.findall(text))
            found = HASH_RE.findall(text)
            if not found and index == 0:
                # One issue per branch: only the leading number.
                found = BRANCH_NUMBER_RE.findall(text)[:1]
                self._branch.update(found)
            keys.extend(found)
        return self._ordered_unique(keys)

    def _should_close(self, key: str) -> bool:
        # Closing keyword wins; else the branch issue. Never a bare mention.
        if key in self._closing:
            return True
        return not self._closing and key in self._branch

    def _repo(self) -> str:
        return self.repo or os.environ.get("GITHUB_REPOSITORY", "")

    def issue_exists(self, key: str) -> bool:
        repo = self._repo()
        try:
            resp = self.session.get(
                f"{self.api}/repos/{repo}/issues/{key}", timeout=self.timeout
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("verify #%s failed: %s", key, exc)
            return False

    def link_pr(self, key: str, pr: PRContext) -> bool:
        # GitHub cross-references the PR natively once it mentions the issue.
        return True

    def comment(self, key: str, text: str) -> bool:
        repo = self._repo()
        try:
            resp = self.session.post(
                f"{self.api}/repos/{repo}/issues/{key}/comments",
                json={"body": text},
                timeout=self.timeout,
            )
            return resp.status_code in (200, 201)
        except Exception as exc:
            logger.error("comment #%s failed: %s", key, exc)
            return False

    def transition(self, key: str, target: str) -> bool:
        repo = self._repo()
        try:
            if target == "done":
                if not self._should_close(key):
                    logger.info("#%s only mentioned; leaving it open", key)
                    return True
                resp = self.session.patch(
                    f"{self.api}/repos/{repo}/issues/{key}",
                    json={"state": "closed"},
                    timeout=self.timeout,
                )
                return resp.status_code == 200
            label = os.environ.get("GITHUB_LABEL_IN_REVIEW")
            if target == "in_review" and label:
                resp = self.session.post(
                    f"{self.api}/repos/{repo}/issues/{key}/labels",
                    json={"labels": [label]},
                    timeout=self.timeout,
                )
                return resp.status_code in (200, 201)
            return True
        except Exception as exc:
            logger.error("transition #%s failed: %s", key, exc)
            return False
