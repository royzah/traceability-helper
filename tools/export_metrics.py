#!/usr/bin/env python3
"""
Export Jira-GitHub integration metrics for reporting and analysis
"""

import csv
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MetricsExporter:
    """Export metrics for Jira-GitHub integration"""

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.jira_base_url = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
        self.jira_user = os.environ.get("JIRA_USER_EMAIL")
        self.jira_token = os.environ.get("JIRA_API_TOKEN")
        self.days_back = int(os.environ.get("DAYS_BACK", "30"))

        # Get repository from environment
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")

        self.output_dir = Path("metrics")
        self.output_dir.mkdir(exist_ok=True)

        # Setup sessions
        self.github_session = requests.Session()
        self.github_session.headers.update(
            {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )

        self.jira_session = requests.Session()
        self.jira_session.auth = (self.jira_user, self.jira_token)

    def get_recent_prs(self) -> List[Dict[str, Any]]:
        """Fetch recent PRs from GitHub"""
        since = (datetime.now() - timedelta(days=self.days_back)).isoformat()

        prs = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/repos/{self.repo}/pulls"
            params = {
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }

            response = self.github_session.get(url, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch PRs: {response.status_code}")
                break

            batch = response.json()
            if not batch:
                break

            for pr in batch:
                if pr["updated_at"] < since:
                    return prs
                prs.append(pr)

            page += 1

        return prs

    def extract_jira_key(self, pr: Dict[str, Any]) -> str:
        """Extract Jira key from PR"""
        import re

        pattern = r"\b([A-Z][A-Z0-9]{1,9}-[0-9]+)\b"

        # Check branch, title, body
        for field in ["head", "title", "body"]:
            if field == "head":
                text = pr.get("head", {}).get("ref", "")
            else:
                text = pr.get(field, "")

            match = re.search(pattern, text or "")
            if match:
                return match.group(1)

        return ""

    def calculate_metrics(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key metrics from PRs"""
        metrics = {
            "total_prs": len(prs),
            "merged_prs": 0,
            "open_prs": 0,
            "closed_without_merge": 0,
            "with_jira_key": 0,
            "without_jira_key": 0,
            "avg_time_to_merge_hours": 0,
            "avg_review_time_hours": 0,
            "prs_by_project": {},
            "monthly_trend": {},
        }

        merge_times = []

        for pr in prs:
            # Jira key tracking
            jira_key = self.extract_jira_key(pr)
            if jira_key:
                metrics["with_jira_key"] += 1
                project = jira_key.split("-")[0]
                metrics["prs_by_project"][project] = (
                    metrics["prs_by_project"].get(project, 0) + 1
                )
            else:
                metrics["without_jira_key"] += 1

            # State tracking
            if pr["state"] == "open":
                metrics["open_prs"] += 1
            elif pr.get("merged_at"):
                metrics["merged_prs"] += 1

                # Calculate time to merge
                created = datetime.fromisoformat(
                    pr["created_at"].replace("Z", "+00:00")
                )
                merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                merge_time = (merged - created).total_seconds() / 3600
                merge_times.append(merge_time)

            else:
                metrics["closed_without_merge"] += 1

            # Monthly trend
            created_date = pr["created_at"][:7]  # YYYY-MM
            metrics["monthly_trend"][created_date] = (
                metrics["monthly_trend"].get(created_date, 0) + 1
            )

        # Calculate averages
        if merge_times:
            metrics["avg_time_to_merge_hours"] = round(
                sum(merge_times) / len(merge_times), 2
            )

        # Compliance rate
        if metrics["total_prs"] > 0:
            metrics["jira_compliance_rate"] = round(
                metrics["with_jira_key"] / metrics["total_prs"] * 100, 2
            )
        else:
            metrics["jira_compliance_rate"] = 0

        return metrics

    def export_to_json(self, metrics: Dict[str, Any], prs: List[Dict[str, Any]]):
        """Export metrics to JSON files"""
        # Summary metrics
        with open(self.output_dir / "summary.json", "w") as f:
            json.dump(metrics, f, indent=2)

        # Detailed PR data
        pr_data = []
        for pr in prs:
            pr_data.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "jira_key": self.extract_jira_key(pr),
                    "created_at": pr["created_at"],
                    "merged_at": pr.get("merged_at"),
                    "user": pr["user"]["login"],
                    "url": pr["html_url"],
                }
            )

        with open(self.output_dir / "pull_requests.json", "w") as f:
            json.dump(pr_data, f, indent=2)

    def export_to_csv(self, metrics: Dict[str, Any], prs: List[Dict[str, Any]]):
        """Export metrics to CSV files"""
        # PR details CSV
        csv_path = self.output_dir / "pull_requests.csv"
        with open(csv_path, "w", newline="") as f:
            fieldnames = [
                "number",
                "jira_key",
                "title",
                "state",
                "created_at",
                "merged_at",
                "user",
                "url",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for pr in prs:
                writer.writerow(
                    {
                        "number": pr["number"],
                        "jira_key": self.extract_jira_key(pr),
                        "title": pr["title"],
                        "state": pr["state"],
                        "created_at": pr["created_at"],
                        "merged_at": pr.get("merged_at", ""),
                        "user": pr["user"]["login"],
                        "url": pr["html_url"],
                    }
                )

        # Project summary CSV
        csv_path = self.output_dir / "project_summary.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Project", "PR Count"])
            for project, count in metrics["prs_by_project"].items():
                writer.writerow([project, count])

    def run(self):
        """Execute metrics export"""
        logger.info(f"Exporting metrics for {self.repo} (last {self.days_back} days)")

        # Fetch PRs
        prs = self.get_recent_prs()
        logger.info(f"Found {len(prs)} PRs")

        # Calculate metrics
        metrics = self.calculate_metrics(prs)

        # Add metadata
        metrics["repository"] = self.repo
        metrics["export_date"] = datetime.now().isoformat()
        metrics["period_days"] = self.days_back

        # Export
        self.export_to_json(metrics, prs)
        self.export_to_csv(metrics, prs)

        # Log summary
        logger.info(f"Metrics exported to {self.output_dir}")
        logger.info(f"Jira compliance rate: {metrics['jira_compliance_rate']}%")
        logger.info(
            f"Average time to merge: {metrics['avg_time_to_merge_hours']} hours"
        )

        return metrics


def main():
    """Main entry point"""
    try:
        exporter = MetricsExporter()
        exporter.run()
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise


if __name__ == "__main__":
    main()
