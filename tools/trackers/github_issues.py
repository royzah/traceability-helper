"""GitHub Issues: "#123" or a leading branch number. Native cross-ref;
merge closes the issue, open can apply a label.
"""

from __future__ import annotations

import logging
import os
import re

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")


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

    def extract_keys(self, *texts):
        seen, out = set(), []
        hash_rx = re.compile(r"#(\d+)")
        branch_rx = re.compile(r"(?:^|[/_-])(\d+)")
        for index, text in enumerate(texts):
            if not text:
                continue
            found = hash_rx.findall(text)
            if not found and index == 0:
                found = branch_rx.findall(text)
            for num in found:
                if num not in seen:
                    seen.add(num)
                    out.append(num)
        return out

    def _repo_for(self, pr: PRContext) -> str:
        return pr.repo or self.repo

    def issue_exists(self, key: str) -> bool:
        repo = self.repo or os.environ.get("GITHUB_REPOSITORY", "")
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
        repo = self.repo or os.environ.get("GITHUB_REPOSITORY", "")
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
        repo = self.repo or os.environ.get("GITHUB_REPOSITORY", "")
        try:
            if target == "done":
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
