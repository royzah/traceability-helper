#!/usr/bin/env python3
"""Link a pull/merge request to its tracker and sync issue state.

Backend via TRACKER_PROVIDER, host auto-detected. Keys come from the branch,
title, and body. Run in CI on a request event.
"""

from __future__ import annotations

import logging
import os
import sys

from hosts import detect_host, load_pr_context
from trackers import available, get_tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("traceability")


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")


def main() -> int:
    provider = os.environ.get("TRACKER_PROVIDER", "jira")
    config = {
        "project_keys": os.environ.get("PROJECT_KEYS", ""),
        "key_pattern": os.environ.get("KEY_PATTERN", ""),
        "timeout": os.environ.get("TRACKER_TIMEOUT", "15"),
    }

    try:
        tracker = get_tracker(provider, config)
    except ValueError as exc:
        logger.error("%s (available: %s)", exc, ", ".join(available()))
        return 1
    except RuntimeError as exc:
        logger.error("provider '%s' misconfigured: %s", provider, exc)
        return 1

    logger.info("host=%s provider=%s", detect_host(), provider)
    pr = load_pr_context()
    if not pr:
        logger.info("no pull/merge request in context; nothing to do")
        return 0

    keys = tracker.extract_keys(pr.head_ref, pr.title, pr.body)
    if not keys:
        print(f"::notice::no {tracker.name} issue key in branch, title, or body")
        return 0

    skip_draft = env_bool("SKIP_DRAFT_PRS", False)
    rc = 0
    for key in keys:
        if not tracker.issue_exists(key):
            print(f"::error::{tracker.name} issue {key} not found or inaccessible")
            rc = 1
            continue

        tracker.link_pr(key, pr)
        logger.info("processing %s for PR #%s (%s)", key, pr.number, pr.action)

        if pr.draft and skip_draft:
            logger.info("draft PR; skipping comment and transition for %s", key)
            continue

        if pr.action in ("opened", "reopened", "ready_for_review"):
            verb = "ready for review" if pr.action == "ready_for_review" else "opened"
            tracker.comment(key, f"Pull request {verb} by {pr.author}: {pr.html_url}")
            tracker.transition(key, "in_review")
        elif pr.action == "closed":
            if pr.merged:
                sha = pr.merge_commit_sha[:12]
                tracker.comment(key, f"Pull request merged ({sha}): {pr.html_url}")
                tracker.transition(key, "done")
            else:
                tracker.comment(key, f"Pull request closed unmerged: {pr.html_url}")

    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - top-level guard for CI
        logger.error("unexpected error: %s", exc)
        sys.exit(1)
