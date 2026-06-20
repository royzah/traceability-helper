"""Host registry: detect the CI host and return a PRContext (override: CI_HOST)."""

from __future__ import annotations

import os

from trackers.base import PRContext

from . import bitbucket, github, gitlab

_LOADERS = {
    "github": github.load,
    "gitlab": gitlab.load,
    "bitbucket": bitbucket.load,
}


def detect_host() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return "github"
    if os.environ.get("GITLAB_CI"):
        return "gitlab"
    if os.environ.get("BITBUCKET_PIPELINE_UUID") or os.environ.get(
        "BITBUCKET_BUILD_NUMBER"
    ):
        return "bitbucket"
    return (os.environ.get("CI_HOST") or "github").strip().lower()


def load_pr_context() -> PRContext | None:
    loader = _LOADERS.get(detect_host())
    return loader() if loader else None


def available_hosts() -> list:
    return sorted(_LOADERS)


__all__ = ["detect_host", "load_pr_context", "available_hosts"]
