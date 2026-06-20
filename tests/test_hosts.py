"""Offline host-adapter tests: CI env is faked, no network."""

import json


def clear_ci(monkeypatch):
    for var in (
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "BITBUCKET_PIPELINE_UUID",
        "BITBUCKET_BUILD_NUMBER",
        "TRACKER_EVENT",
        "CI_HOST",
    ):
        monkeypatch.delenv(var, raising=False)


def test_github_load_and_override(monkeypatch, tmp_path):
    clear_ci(monkeypatch)
    event = {
        "action": "opened",
        "pull_request": {
            "number": 7,
            "title": "t SECO-1",
            "body": "b",
            "html_url": "u",
            "state": "open",
            "merged": False,
            "draft": False,
            "head": {"ref": "feat/SECO-1-x"},
            "base": {"ref": "main", "repo": {"full_name": "o/r"}},
            "user": {"login": "dev"},
        },
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))

    from hosts import github

    ctx = github.load()
    assert ctx.number == 7
    assert ctx.head_ref == "feat/SECO-1-x"
    assert ctx.action == "opened" and ctx.merged is False

    monkeypatch.setenv("TRACKER_EVENT", "merged")
    ctx = github.load()
    assert ctx.action == "closed" and ctx.merged is True


def test_gitlab_load(monkeypatch):
    clear_ci(monkeypatch)
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "12")
    monkeypatch.setenv("CI_MERGE_REQUEST_TITLE", "feat SECO-1")
    monkeypatch.setenv("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME", "feat/SECO-1-x")
    monkeypatch.setenv("CI_PROJECT_URL", "https://gl/o/r")

    from hosts import gitlab

    ctx = gitlab.load()
    assert ctx.number == 12
    assert ctx.head_ref == "feat/SECO-1-x"

    monkeypatch.setenv("TRACKER_EVENT", "merged")
    ctx = gitlab.load()
    assert ctx.action == "closed" and ctx.merged is True


def test_bitbucket_load(monkeypatch):
    clear_ci(monkeypatch)
    monkeypatch.setenv("BITBUCKET_PR_ID", "9")
    monkeypatch.setenv("BITBUCKET_REPO_FULL_NAME", "o/r")
    monkeypatch.setenv("BITBUCKET_BRANCH", "feat/SECO-1-x")

    from hosts import bitbucket

    ctx = bitbucket.load()
    assert ctx.number == 9
    assert ctx.head_ref == "feat/SECO-1-x"
    assert ctx.repo == "o/r"


def test_detect_host(monkeypatch):
    import hosts

    clear_ci(monkeypatch)
    monkeypatch.setenv("GITLAB_CI", "true")
    assert hosts.detect_host() == "gitlab"
    monkeypatch.delenv("GITLAB_CI")
    monkeypatch.setenv("BITBUCKET_BUILD_NUMBER", "1")
    assert hosts.detect_host() == "bitbucket"
    monkeypatch.delenv("BITBUCKET_BUILD_NUMBER")
    monkeypatch.setenv("CI_HOST", "github")
    assert hosts.detect_host() == "github"
