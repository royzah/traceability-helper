"""Bitbucket Pipelines host: reads BITBUCKET_* (key comes from the branch)."""

from __future__ import annotations

import os

from trackers.base import PRContext

from .base import commit_message, resolve_event


def load() -> PRContext | None:
    pr_id = os.environ.get("BITBUCKET_PR_ID", "")
    repo = os.environ.get("BITBUCKET_REPO_FULL_NAME", "")
    branch = os.environ.get("BITBUCKET_BRANCH", "")
    sha = os.environ.get("BITBUCKET_COMMIT", "")
    html_url = (
        f"https://bitbucket.org/{repo}/pull-requests/{pr_id}"
        if repo and pr_id
        else f"https://bitbucket.org/{repo}"
    )

    action, merged = resolve_event("opened", False)

    return PRContext(
        number=int(pr_id) if pr_id.isdigit() else 0,
        title=os.environ.get("BITBUCKET_PR_TITLE", ""),
        # On merges the key lives in the merge-commit message, not the env.
        body=commit_message(sha),
        html_url=html_url,
        state="open",
        merged=merged,
        draft=False,
        head_ref=branch,
        base_ref=os.environ.get("BITBUCKET_PR_DESTINATION_BRANCH", ""),
        repo=repo,
        author=os.environ.get("BITBUCKET_STEP_TRIGGERER_UUID", "unknown"),
        merge_commit_sha=sha,
        action=action,
    )
