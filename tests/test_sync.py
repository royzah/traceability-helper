"""End-to-end sync flow with a stub tracker and host (no network)."""

from unittest.mock import MagicMock

import sync
from trackers.base import PRContext


def make_pr(action, merged=False, draft=False):
    return PRContext(
        number=5,
        title="t",
        body="b",
        html_url="u",
        state="open",
        merged=merged,
        draft=draft,
        head_ref="feat/SECO-1-x",
        base_ref="main",
        repo="o/r",
        author="dev",
        merge_commit_sha="abc123def456",
        action=action,
    )


def stub_tracker():
    t = MagicMock()
    t.name = "jira"
    t.extract_keys.return_value = ["SECO-1"]
    t.issue_exists.return_value = True
    return t


def wire(monkeypatch, tracker, pr):
    monkeypatch.setenv("TRACKER_PROVIDER", "jira")
    monkeypatch.setattr(sync, "get_tracker", lambda *a, **k: tracker)
    monkeypatch.setattr(sync, "load_pr_context", lambda: pr)
    monkeypatch.setattr(sync, "detect_host", lambda: "github")


def test_opened_links_and_reviews(monkeypatch):
    t = stub_tracker()
    wire(monkeypatch, t, make_pr("opened"))
    assert sync.main() == 0
    t.link_pr.assert_called_once()
    t.transition.assert_called_once_with("SECO-1", "in_review")


def test_merged_transitions_done(monkeypatch):
    t = stub_tracker()
    wire(monkeypatch, t, make_pr("closed", merged=True))
    assert sync.main() == 0
    t.transition.assert_called_once_with("SECO-1", "done")


def test_missing_issue_returns_error(monkeypatch):
    t = stub_tracker()
    t.issue_exists.return_value = False
    wire(monkeypatch, t, make_pr("opened"))
    assert sync.main() == 1
    t.transition.assert_not_called()


def test_no_key_is_noop(monkeypatch):
    t = stub_tracker()
    t.extract_keys.return_value = []
    wire(monkeypatch, t, make_pr("opened"))
    assert sync.main() == 0
    t.link_pr.assert_not_called()


def test_draft_skips_transition(monkeypatch):
    t = stub_tracker()
    monkeypatch.setenv("SKIP_DRAFT_PRS", "true")
    wire(monkeypatch, t, make_pr("opened", draft=True))
    assert sync.main() == 0
    t.link_pr.assert_called_once()
    t.transition.assert_not_called()
