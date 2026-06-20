"""Offline tracker tests: the HTTP session is mocked, no network."""

from unittest.mock import MagicMock

from conftest import Resp
from trackers.base import PRContext


def pr(number=5):
    return PRContext(
        number=number,
        title="add auth (SECO-1)",
        body="body",
        html_url="https://gh/pr/5",
        state="open",
        merged=False,
        draft=False,
        head_ref="feat/SECO-1-x",
        base_ref="main",
        repo="o/r",
        author="dev",
        merge_commit_sha="abc123def456",
        action="opened",
    )


# -- Jira --------------------------------------------------------------------


def jira(monkeypatch, version="3"):
    monkeypatch.setenv("JIRA_BASE_URL", "https://x.atlassian.net")
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    monkeypatch.setenv("JIRA_USER_EMAIL", "e")
    monkeypatch.setenv("JIRA_API_VERSION", version)
    from trackers.jira import JiraTracker

    tracker = JiraTracker({"project_keys": "SECO", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_jira_extract_filters_unknown_project(monkeypatch):
    t = jira(monkeypatch)
    assert t.extract_keys("feat/SECO-1-x", "also SECO-9 and IGNORE-2", "") == [
        "SECO-1",
        "SECO-9",
    ]


def test_jira_issue_exists(monkeypatch):
    t = jira(monkeypatch)
    t.session.get.return_value = Resp(200)
    assert t.issue_exists("SECO-1") is True
    assert t.session.get.call_args[0][0].endswith("/rest/api/3/issue/SECO-1")


def test_jira_link(monkeypatch):
    t = jira(monkeypatch)
    t.session.post.return_value = Resp(201)
    assert t.link_pr("SECO-1", pr()) is True
    call = t.session.post.call_args
    assert call[0][0].endswith("/issue/SECO-1/remotelink")
    assert call[1]["json"]["globalId"] == "github-pr-o/r-5"


def test_jira_comment_adf_v3_plain_v2(monkeypatch):
    t3 = jira(monkeypatch, "3")
    t3.session.post.return_value = Resp(201)
    t3.comment("SECO-1", "hi")
    assert isinstance(t3.session.post.call_args[1]["json"]["body"], dict)

    t2 = jira(monkeypatch, "2")
    t2.session.post.return_value = Resp(201)
    t2.comment("SECO-1", "hi")
    assert t2.session.post.call_args[1]["json"]["body"] == "hi"


def test_jira_transition_done(monkeypatch):
    monkeypatch.setenv("JIRA_TRANSITION_DONE", "Done")
    t = jira(monkeypatch)
    t.session.get.return_value = Resp(
        200, {"transitions": [{"id": "31", "name": "Done"}]}
    )
    t.session.post.return_value = Resp(204)
    assert t.transition("SECO-1", "done") is True
    assert t.session.post.call_args[1]["json"] == {"transition": {"id": "31"}}


def test_jira_transition_noop_when_unset(monkeypatch):
    t = jira(monkeypatch)
    assert t.transition("SECO-1", "done") is True
    t.session.get.assert_not_called()


# -- GitHub Issues -----------------------------------------------------------


def github(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    from trackers.github_issues import GitHubIssuesTracker

    tracker = GitHubIssuesTracker({"project_keys": "", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_github_extract_branch_and_hash(monkeypatch):
    t = github(monkeypatch)
    assert t.extract_keys("123-fix", "see #45", "") == ["123", "45"]


def test_github_transition_done_closes(monkeypatch):
    t = github(monkeypatch)
    t.session.patch.return_value = Resp(200)
    assert t.transition("45", "done") is True
    assert t.session.patch.call_args[1]["json"] == {"state": "closed"}


def test_github_link_is_noop(monkeypatch):
    t = github(monkeypatch)
    assert t.link_pr("45", pr()) is True
    t.session.post.assert_not_called()


# -- Linear ------------------------------------------------------------------


def linear(monkeypatch):
    monkeypatch.setenv("LINEAR_API_KEY", "k")
    from trackers.linear import LinearTracker

    tracker = LinearTracker({"project_keys": "", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_linear_issue_exists(monkeypatch):
    t = linear(monkeypatch)
    t.session.post.return_value = Resp(
        200,
        {"data": {"issueSearch": {"nodes": [{"id": "uuid", "identifier": "ENG-1"}]}}},
    )
    assert t.issue_exists("ENG-1") is True


def test_linear_comment(monkeypatch):
    t = linear(monkeypatch)
    t._cache["ENG-1"] = {"id": "uuid"}
    t.session.post.return_value = Resp(
        200, {"data": {"commentCreate": {"success": True}}}
    )
    assert t.comment("ENG-1", "hi") is True


# -- YouTrack ----------------------------------------------------------------


def youtrack(monkeypatch):
    monkeypatch.setenv("YOUTRACK_BASE_URL", "https://yt")
    monkeypatch.setenv("YOUTRACK_TOKEN", "t")
    from trackers.youtrack import YouTrackTracker

    tracker = YouTrackTracker({"project_keys": "", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_youtrack_comment_and_transition(monkeypatch):
    monkeypatch.setenv("YOUTRACK_STATE_DONE", "Fixed")
    t = youtrack(monkeypatch)
    t.session.post.return_value = Resp(200)
    assert t.comment("PROJ-1", "hi") is True
    assert t.transition("PROJ-1", "done") is True
    assert t.session.post.call_args[1]["json"]["query"] == "State Fixed"


# -- Azure Boards ------------------------------------------------------------


def azure(monkeypatch):
    monkeypatch.setenv("AZURE_ORG_URL", "https://dev.azure.com/o")
    monkeypatch.setenv("AZURE_PROJECT", "p")
    monkeypatch.setenv("AZURE_PAT", "x")
    from trackers.azure import AzureBoardsTracker

    tracker = AzureBoardsTracker({"project_keys": "", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_azure_extract(monkeypatch):
    t = azure(monkeypatch)
    assert t.extract_keys("feature/AB#77-x", "refs AB#88", "") == ["77", "88"]


def test_azure_transition_sets_state(monkeypatch):
    monkeypatch.setenv("AZURE_STATE_DONE", "Closed")
    t = azure(monkeypatch)
    t.session.patch.return_value = Resp(200)
    assert t.transition("77", "done") is True
    patch = t.session.patch.call_args[1]["json"]
    assert patch[0]["path"] == "/fields/System.State"
    assert patch[0]["value"] == "Closed"


# -- Trello ------------------------------------------------------------------


def trello(monkeypatch):
    monkeypatch.setenv("TRELLO_KEY", "k")
    monkeypatch.setenv("TRELLO_TOKEN", "t")
    from trackers.trello import TrelloTracker

    tracker = TrelloTracker({"project_keys": "", "key_pattern": ""})
    tracker.session = MagicMock()
    return tracker


def test_trello_extract(monkeypatch):
    t = trello(monkeypatch)
    assert t.extract_keys(
        "feat/trello-aBcD1234-x", "https://trello.com/c/Zz99Yy00/5", ""
    ) == ["aBcD1234", "Zz99Yy00"]


def test_trello_transition_moves_list(monkeypatch):
    monkeypatch.setenv("TRELLO_LIST_DONE", "list99")
    t = trello(monkeypatch)
    t.session.put.return_value = Resp(200)
    assert t.transition("aBcD1234", "done") is True
    assert t.session.put.call_args[1]["params"]["idList"] == "list99"


# -- Registry ----------------------------------------------------------------


def test_unknown_provider_raises():
    from trackers import get_tracker

    try:
        get_tracker("nope", {})
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "unknown provider" in str(exc)
