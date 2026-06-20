"""Tracker abstraction: existence check, link, comment, transition.

Each provider implements these four calls against its own API.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover - urllib3 ships with requests
    Retry = None

logger = logging.getLogger("traceability")

# Jira, Linear, and YouTrack all use the PROJ-123 shape. GitHub and Azure
# providers override this with their own native reference format.
DEFAULT_KEY_PATTERN = r"[A-Z][A-Z0-9]{1,9}-[0-9]+"


@dataclass
class PRContext:
    """The slice of a GitHub pull_request event the trackers need."""

    number: int
    title: str
    body: str
    html_url: str
    state: str
    merged: bool
    draft: bool
    head_ref: str
    base_ref: str
    repo: str
    author: str
    merge_commit_sha: str
    action: str


def make_session(headers=None, auth=None, retries: int = 3, backoff: float = 1.0):
    """A requests session with retry/backoff on transient HTTP failures."""
    session = requests.Session()
    if auth:
        session.auth = auth
    if headers:
        session.headers.update(headers)
    if Retry is not None:
        retry = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    return session


def first_env(*names: str) -> str | None:
    """First non-empty environment variable from the given names."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


class Tracker:
    """Base class. Subclasses implement the four operations natively."""

    name = "base"
    default_key_pattern = DEFAULT_KEY_PATTERN
    # Logical targets the core asks for; providers map them to real states.
    target_envs = {
        "in_review": ("TRACKER_STATE_IN_REVIEW",),
        "done": ("TRACKER_STATE_DONE",),
    }

    def __init__(self, config: dict):
        self.config = config or {}
        self.project_keys = [
            k.strip()
            for k in (self.config.get("project_keys") or "").split(",")
            if k.strip()
        ]
        self.key_pattern = self.config.get("key_pattern") or self.default_key_pattern
        self.timeout = int(self.config.get("timeout") or 15)

    # -- key extraction (default: PROJ-123, project-filtered) --------------

    def extract_keys(self, *texts: str) -> list[str]:
        rx = re.compile("(" + self.key_pattern + ")")
        seen, out = set(), []
        for text in texts:
            for match in rx.finditer(text or ""):
                key = match.group(1)
                if (
                    self.project_keys
                    and "-" in key
                    and key.split("-")[0] not in self.project_keys
                ):
                    continue
                if key not in seen:
                    seen.add(key)
                    out.append(key)
        return out

    def state_for(self, target: str) -> str | None:
        return first_env(*self.target_envs.get(target, ()))

    # -- operations (override these) --------------------------------------

    def issue_exists(self, key: str) -> bool:
        return True

    def link_pr(self, key: str, pr: PRContext) -> bool:
        return True

    def comment(self, key: str, text: str) -> bool:
        return True

    def transition(self, key: str, target: str) -> bool:
        return True
