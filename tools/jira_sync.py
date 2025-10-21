#!/usr/bin/env python3
"""
Jira-GitHub PR Synchronization Tool
Automatically links GitHub PRs to Jira issues and manages transitions
"""

import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class JiraGitHubSync:
    """Handles synchronization between GitHub PRs and Jira issues"""

    def __init__(self):
        self.jira_base_url = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
        self.jira_user = os.environ.get("JIRA_USER_EMAIL")
        self.jira_token = os.environ.get("JIRA_API_TOKEN")
        self.valid_projects = os.environ.get("JIRA_PROJECT_KEYS", "").split(",")

        if not all([self.jira_base_url, self.jira_user, self.jira_token]):
            logger.error("Missing required Jira configuration in environment variables")
            sys.exit(1)

        self.session = requests.Session()
        self.session.auth = (self.jira_user, self.jira_token)
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

    def extract_jira_keys(self, text: str) -> List[str]:
        """Extract all Jira issue keys from text"""
        pattern = r"\b([A-Z][A-Z0-9]{1,9}-[0-9]+)\b"
        keys = re.findall(pattern, text or "")

        # Filter by valid projects if configured
        if self.valid_projects:
            keys = [k for k in keys if k.split("-")[0] in self.valid_projects]

        return keys

    def get_first_jira_key(self, *texts: str) -> Optional[str]:
        """Get the first Jira key from multiple text sources"""
        for text in texts:
            keys = self.extract_jira_keys(text)
            if keys:
                return keys[0]
        return None

    def load_github_event(self) -> Dict[str, Any]:
        """Load GitHub event data from the event file"""
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path or not os.path.exists(event_path):
            logger.error("GitHub event file not found")
            return {}

        try:
            with open(event_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load GitHub event: {e}")
            return {}

    def verify_issue_exists(self, issue_key: str) -> bool:
        """Verify that the Jira issue exists and is accessible"""
        url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}"

        try:
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to verify issue {issue_key}: {e}")
            return False

    def create_or_update_remote_link(
        self, issue_key: str, pr_data: Dict[str, Any]
    ) -> bool:
        """Create or update a remote link from Jira issue to GitHub PR"""
        url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}/remotelink"

        # Check if link already exists
        try:
            existing_links = self.session.get(url, timeout=10).json()
            for link in existing_links:
                if link.get("object", {}).get("url") == pr_data["html_url"]:
                    logger.info(f"Remote link already exists for {issue_key}")
                    return True
        except Exception as e:  # nosec B110
            logger.debug(f"Failed to check existing links: {e}")

        # Create new link
        link_title = f"GitHub PR #{pr_data['number']} - {pr_data['title']}"
        payload = {
            "object": {
                "url": pr_data["html_url"],
                "title": link_title,
                "icon": {
                    "url16x16": "https://github.githubassets.com/favicons/favicon.png",
                    "title": "GitHub",
                },
                "status": {
                    "resolved": pr_data.get("merged", False),
                    "icon": {
                        "url16x16": self._get_status_icon(
                            pr_data["state"], pr_data.get("merged", False)
                        ),
                        "title": self._get_status_text(
                            pr_data["state"], pr_data.get("merged", False)
                        ),
                    },
                },
            },
            "globalId": f"github-pr-{pr_data['repo']}-{pr_data['number']}",
            "relationship": "Pull Request",
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Created remote link for {issue_key}")
                return True
            else:
                logger.warning(
                    f"Failed to create remote link: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to create remote link: {e}")
            return False

    def _get_status_icon(self, state: str, merged: bool) -> str:
        """Get appropriate status icon URL"""
        if merged:
            return "https://github.githubassets.com/images/icons/emoji/unicode/2705.png"  # Check mark
        elif state == "open":
            return "https://github.githubassets.com/images/icons/emoji/unicode/1f7e2.png"  # Green circle
        else:
            return "https://github.githubassets.com/images/icons/emoji/unicode/1f534.png"  # Red circle

    def _get_status_text(self, state: str, merged: bool) -> str:
        """Get status text for the PR"""
        if merged:
            return "Merged"
        elif state == "open":
            return "Open"
        else:
            return "Closed"

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to the Jira issue"""
        url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}/comment"

        # Format comment with metadata
        formatted_comment = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment, "marks": []}],
                    }
                ],
            }
        }

        try:
            response = self.session.post(url, json=formatted_comment, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Added comment to {issue_key}")
                return True
            else:
                logger.warning(f"Failed to add comment: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return False

    def transition_issue(self, issue_key: str, transition_name_or_id: str) -> bool:
        """Transition the Jira issue to a new status"""
        if not transition_name_or_id:
            return True

        # Get available transitions
        url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}/transitions"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to get transitions for {issue_key}")
                return False

            transitions = response.json().get("transitions", [])

            # Find matching transition
            transition_id = None
            for trans in transitions:
                if (
                    str(trans["id"]) == str(transition_name_or_id)
                    or trans["name"].lower() == str(transition_name_or_id).lower()
                ):
                    transition_id = trans["id"]
                    transition_name = trans["name"]
                    break

            if not transition_id:
                logger.info(
                    f"Transition '{transition_name_or_id}' not available for {issue_key}"
                )
                return True  # Not an error, just not applicable

            # Execute transition
            payload = {"transition": {"id": transition_id}}
            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code in [200, 204]:
                logger.info(f"Transitioned {issue_key} to '{transition_name}'")
                return True
            else:
                logger.warning(f"Failed to transition: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to transition issue: {e}")
            return False

    def process_pull_request(self):
        """Main method to process the GitHub PR event"""
        event = self.load_github_event()
        if not event:
            logger.error("No GitHub event data available")
            return

        pr = event.get("pull_request", {})
        if not pr:
            logger.info("Not a pull request event, skipping")
            return

        # Extract PR information
        pr_data = {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "html_url": pr.get("html_url", ""),
            "state": pr.get("state", "open"),
            "merged": pr.get("merged", False),
            "head_ref": pr.get("head", {}).get("ref", ""),
            "base_ref": pr.get("base", {}).get("ref", ""),
            "repo": pr.get("base", {}).get("repo", {}).get("full_name", ""),
            "user": pr.get("user", {}).get("login", "unknown"),
            "created_at": pr.get("created_at", ""),
            "updated_at": pr.get("updated_at", ""),
            "merged_at": pr.get("merged_at", ""),
            "merge_commit_sha": pr.get("merge_commit_sha", ""),
        }

        action = event.get("action", "")

        # Extract Jira key from PR
        jira_key = self.get_first_jira_key(
            pr_data["head_ref"], pr_data["title"], pr_data["body"]
        )

        if not jira_key:
            logger.warning("No Jira key found in PR, skipping sync")
            print(
                "::notice::No Jira key found in PR. Ensure branch name or PR title contains a valid Jira issue key."
            )
            return

        logger.info(f"Processing PR #{pr_data['number']} for Jira issue {jira_key}")

        # Verify issue exists
        if not self.verify_issue_exists(jira_key):
            logger.error(f"Jira issue {jira_key} not found or not accessible")
            print(
                f"::error::Jira issue {jira_key} not found. Please create the issue first."
            )
            sys.exit(1)

        # Create/update remote link
        self.create_or_update_remote_link(jira_key, pr_data)

        # Add appropriate comment based on action
        if action == "opened":
            comment = (
                f"🔗 Pull Request opened by {pr_data['user']}: {pr_data['html_url']}"
            )
            self.add_comment(jira_key, comment)

            # Transition to "In Review" if configured
            transition = os.environ.get("JIRA_TRANSITION_IN_REVIEW")
            if transition:
                self.transition_issue(jira_key, transition)

        elif action == "closed":
            if pr_data["merged"]:
                comment = f"✅ Pull Request merged: {pr_data['html_url']}\nMerge commit: {pr_data['merge_commit_sha']}"
                self.add_comment(jira_key, comment)

                # Transition to "Done" if configured
                transition = os.environ.get("JIRA_TRANSITION_DONE")
                if transition:
                    self.transition_issue(jira_key, transition)
            else:
                comment = f"❌ Pull Request closed without merge: {pr_data['html_url']}"
                self.add_comment(jira_key, comment)

        elif action == "ready_for_review":
            comment = f"👀 Pull Request ready for review: {pr_data['html_url']}"
            self.add_comment(jira_key, comment)

            # Transition to "In Review" if configured
            transition = os.environ.get("JIRA_TRANSITION_IN_REVIEW")
            if transition:
                self.transition_issue(jira_key, transition)

        logger.info("Jira sync completed successfully")


def main():
    """Main entry point"""
    try:
        sync = JiraGitHubSync()
        sync.process_pull_request()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
