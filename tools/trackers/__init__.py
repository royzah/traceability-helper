"""Tracker registry: get_tracker(name) returns a base.Tracker backend."""

from __future__ import annotations

from .azure import AzureBoardsTracker
from .base import PRContext, Tracker
from .github_issues import GitHubIssuesTracker
from .jira import JiraTracker
from .linear import LinearTracker
from .trello import TrelloTracker
from .youtrack import YouTrackTracker

_REGISTRY = {
    "jira": JiraTracker,
    "github": GitHubIssuesTracker,
    "github-issues": GitHubIssuesTracker,
    "linear": LinearTracker,
    "youtrack": YouTrackTracker,
    "azure": AzureBoardsTracker,
    "azure-devops": AzureBoardsTracker,
    "trello": TrelloTracker,
}


def get_tracker(name: str, config: dict) -> Tracker:
    key = (name or "jira").strip().lower()
    if key not in _REGISTRY:
        raise ValueError(f"unknown provider '{key}'; valid: {', '.join(available())}")
    return _REGISTRY[key](config)


def available() -> list:
    return sorted(set(_REGISTRY))


__all__ = ["Tracker", "PRContext", "get_tracker", "available"]
