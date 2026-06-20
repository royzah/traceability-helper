"""Shared host helpers. Each adapter reads its CI env into a PRContext."""

from __future__ import annotations

import os


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
