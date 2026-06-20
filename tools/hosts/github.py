"""GitHub Actions host adapter (reads the pull_request event payload)."""

from __future__ import annotations

import json
import logging
import os

from trackers.base import PRContext

from .base import event_override

logger = logging.getLogger("traceability")


def load() -> PRContext | None:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        logger.error("GITHUB_EVENT_PATH not set or missing")
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            event = json.load(handle)
    except Exception as exc:
        logger.error("failed to read event file: %s", exc)
        return None

    pr = event.get("pull_request")
    if not pr:
        return None

    base = pr.get("base", {}) or {}
    head = pr.get("head", {}) or {}
    action = event.get("action", "")
    merged = bool(pr.get("merged"))
    override = event_override(action, merged)
    if override:
        action, merged = override

    return PRContext(
        number=pr.get("number", 0),
        title=pr.get("title") or "",
        body=pr.get("body") or "",
        html_url=pr.get("html_url") or "",
        state=pr.get("state") or "open",
        merged=merged,
        draft=bool(pr.get("draft")),
        head_ref=head.get("ref", ""),
        base_ref=base.get("ref", ""),
        repo=(base.get("repo", {}) or {}).get("full_name", "")
        or os.environ.get("GITHUB_REPOSITORY", ""),
        author=(pr.get("user", {}) or {}).get("login", "unknown"),
        merge_commit_sha=pr.get("merge_commit_sha") or "",
        action=action,
    )
