"""GitLab CI host: reads CI_MERGE_REQUEST_* and the merge-commit title."""

from __future__ import annotations

import os

from trackers.base import PRContext

from .base import resolve_event


def load() -> PRContext | None:
    iid = os.environ.get("CI_MERGE_REQUEST_IID", "")
    head = os.environ.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME") or os.environ.get(
        "CI_COMMIT_BRANCH", ""
    )
    title = os.environ.get("CI_MERGE_REQUEST_TITLE") or os.environ.get(
        "CI_COMMIT_TITLE", ""
    )
    body = os.environ.get("CI_MERGE_REQUEST_DESCRIPTION") or os.environ.get(
        "CI_COMMIT_DESCRIPTION", ""
    )
    project_url = os.environ.get("CI_MERGE_REQUEST_PROJECT_URL") or os.environ.get(
        "CI_PROJECT_URL", ""
    )
    html_url = (
        f"{project_url}/-/merge_requests/{iid}" if iid and project_url else project_url
    )

    action, merged = resolve_event("opened", False)

    return PRContext(
        number=int(iid) if iid.isdigit() else 0,
        title=title,
        body=body,
        html_url=html_url,
        state="open",
        merged=merged,
        draft=os.environ.get("CI_MERGE_REQUEST_DRAFT", "") == "true",
        head_ref=head,
        base_ref=os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", ""),
        repo=os.environ.get("CI_PROJECT_PATH", ""),
        author=os.environ.get("GITLAB_USER_LOGIN", "unknown"),
        merge_commit_sha=os.environ.get("CI_COMMIT_SHA", ""),
        action=action,
    )
