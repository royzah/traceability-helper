"""Shared host helpers. Each adapter reads its CI env into a PRContext."""

from __future__ import annotations

import logging
import os
import subprocess

logger = logging.getLogger("traceability")


def event_override(action: str, merged: bool) -> tuple[str, bool] | None:
    """Map TRACKER_EVENT (opened|ready|merged|closed) to (action, merged)."""
    event = (os.environ.get("TRACKER_EVENT") or "").strip().lower()
    if not event:
        return None
    if event in ("merged", "done"):
        return "closed", True
    if event in ("closed", "declined"):
        return "closed", False
    if event in ("ready", "ready_for_review"):
        return "ready_for_review", False
    if event in ("reopened",):
        return "reopened", False
    return "opened", False


def resolve_event(action: str, merged: bool) -> tuple[str, bool]:
    """The TRACKER_EVENT override if set, else the host-supplied defaults."""
    return event_override(action, merged) or (action, merged)


def commit_message(sha: str) -> str:
    """Full message of a commit, or "" — fallback key source for merges."""
    if not sha:
        return ""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B", sha],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as exc:
        logger.warning("could not read commit %s: %s", sha[:12], exc)
        return ""
