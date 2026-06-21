#!/usr/bin/env python3
"""Traceability coverage: share of merged PRs that reference an issue key.

Writes metrics/summary.json and metrics/prs.csv. Needs GITHUB_TOKEN and
GITHUB_REPOSITORY; KEY_PATTERN and DAYS_BACK optional.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("traceability")

DEFAULT_KEY_PATTERN = r"[A-Z][A-Z0-9]{1,9}-[0-9]+|AB#\d+|#\d+"


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    days_back = int(os.environ.get("DAYS_BACK", "30"))
    pattern = re.compile(os.environ.get("KEY_PATTERN") or DEFAULT_KEY_PATTERN)
    if not token or not repo:
        logger.error("GITHUB_TOKEN and GITHUB_REPOSITORY are required")
        return 1

    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    rows, page = [], 1
    while True:
        resp = session.get(
            f"{api}/repos/{repo}/pulls",
            params={
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        stop = False
        for pr in batch:
            updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            if updated < cutoff:
                stop = True
                break
            merged_at = pr.get("merged_at")
            if not merged_at:
                continue
            # Count by merge date, not by recent activity.
            merged = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            if merged < cutoff:
                continue
            text = " ".join(
                [
                    pr.get("head", {}).get("ref", ""),
                    pr.get("title", ""),
                    pr.get("body") or "",
                ]
            )
            match = pattern.search(text)
            rows.append(
                {
                    "number": pr["number"],
                    "merged_at": pr["merged_at"],
                    "key": match.group(0) if match else "",
                    "traced": bool(match),
                    "url": pr["html_url"],
                }
            )
        if stop or len(batch) < 100:
            break
        page += 1

    total = len(rows)
    traced = sum(1 for r in rows if r["traced"])
    # No merged PRs: report null, not a misleading 100%.
    coverage = round(100 * traced / total, 1) if total else None
    summary = {
        "repo": repo,
        "days_back": days_back,
        "merged_prs": total,
        "traced_prs": traced,
        "coverage_pct": coverage,
    }

    out = Path("metrics")
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (out / "prs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["number", "merged_at", "key", "traced", "url"]
        )
        writer.writeheader()
        writer.writerows(rows)

    if total:
        logger.info("coverage: %s%% (%s/%s)", coverage, traced, total)
    else:
        logger.info("no merged PRs in the last %s days", days_back)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
