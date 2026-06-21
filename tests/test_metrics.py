"""Offline metrics test: the HTTP session is mocked, no network."""

import json
from datetime import datetime, timedelta, timezone

import metrics
from conftest import Resp


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeSession:
    def __init__(self, pages):
        self._pages = pages
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        page = (params or {}).get("page", 1)
        data = self._pages[page - 1] if page - 1 < len(self._pages) else []
        return Resp(200, data)


def run(monkeypatch, tmp_path, pages):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setattr(metrics.requests, "Session", lambda: FakeSession(pages))
    monkeypatch.chdir(tmp_path)
    assert metrics.main() == 0
    return json.loads((tmp_path / "metrics" / "summary.json").read_text())


def test_counts_merged_in_window_only(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc)
    recent, old = now - timedelta(days=1), now - timedelta(days=400)
    page = [
        # merged in window, traced
        {
            "number": 1,
            "updated_at": iso(recent),
            "merged_at": iso(recent),
            "title": "feat: x (PROJ-1)",
            "html_url": "u1",
            "head": {"ref": "feat/PROJ-1-x"},
            "body": "",
        },
        # merged in window, untraced
        {
            "number": 2,
            "updated_at": iso(recent),
            "merged_at": iso(recent),
            "title": "no key",
            "html_url": "u2",
            "head": {"ref": "x"},
            "body": "",
        },
        # merged before the window but updated recently: must be excluded
        {
            "number": 3,
            "updated_at": iso(recent),
            "merged_at": iso(old),
            "title": "feat: old (PROJ-9)",
            "html_url": "u3",
            "head": {"ref": "y"},
            "body": "",
        },
        # closed unmerged: must be excluded
        {
            "number": 4,
            "updated_at": iso(recent),
            "merged_at": None,
            "title": "wip",
            "html_url": "u4",
            "head": {"ref": "z"},
            "body": "",
        },
    ]
    summary = run(monkeypatch, tmp_path, [page])
    assert summary["merged_prs"] == 2
    assert summary["traced_prs"] == 1
    assert summary["coverage_pct"] == 50.0


def test_no_merged_prs_reports_null_coverage(monkeypatch, tmp_path):
    summary = run(monkeypatch, tmp_path, [[]])
    assert summary["merged_prs"] == 0
    assert summary["coverage_pct"] is None
