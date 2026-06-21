"""Linear (GraphQL): ENG-123 keys; attachment link, comment, state by name."""

from __future__ import annotations

import logging
import os

from .base import PRContext, Tracker, make_session

logger = logging.getLogger("traceability")

ENDPOINT = "https://api.linear.app/graphql"


class LinearTracker(Tracker):
    name = "linear"
    target_envs = {
        "in_review": ("LINEAR_STATE_IN_REVIEW", "TRACKER_STATE_IN_REVIEW"),
        "done": ("LINEAR_STATE_DONE", "TRACKER_STATE_DONE"),
    }

    def __init__(self, config: dict):
        super().__init__(config)
        token = os.environ.get("LINEAR_API_KEY")
        if not token:
            raise RuntimeError("LINEAR_API_KEY is required for the linear provider")
        self.session = make_session(
            headers={"Authorization": token, "Content-Type": "application/json"}
        )
        self._cache: dict = {}

    def _query(self, query: str, variables: dict) -> dict:
        try:
            resp = self.session.post(
                ENDPOINT,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
            )
            data = resp.json()
        except Exception as exc:
            # Non-JSON/5xx: degrade rather than crash the whole run.
            logger.error("linear request failed: %s", exc)
            return {}
        if data.get("errors"):
            logger.warning("linear error: %s", data["errors"])
        return data.get("data", {}) or {}

    def _resolve(self, key: str) -> dict:
        if key in self._cache:
            return self._cache[key]
        query = (
            "query($q:String!){issueSearch(query:$q){nodes"
            "{id identifier url team{id}}}}"
        )
        nodes = self._query(query, {"q": key}).get("issueSearch", {}).get("nodes", [])
        node = next((n for n in nodes if n.get("identifier") == key), None) or {}
        self._cache[key] = node
        return node

    def issue_exists(self, key: str) -> bool:
        return bool(self._resolve(key).get("id"))

    def link_pr(self, key: str, pr: PRContext) -> bool:
        node = self._resolve(key)
        if not node.get("id"):
            return False
        mutation = (
            "mutation($id:String!,$url:String!,$title:String!)"
            "{attachmentLinkURL(issueId:$id,url:$url,title:$title){success}}"
        )
        data = self._query(
            mutation,
            {"id": node["id"], "url": pr.html_url, "title": f"GitHub PR #{pr.number}"},
        )
        return bool(data.get("attachmentLinkURL", {}).get("success"))

    def comment(self, key: str, text: str) -> bool:
        node = self._resolve(key)
        if not node.get("id"):
            return False
        mutation = (
            "mutation($id:String!,$body:String!)"
            "{commentCreate(input:{issueId:$id,body:$body}){success}}"
        )
        data = self._query(mutation, {"id": node["id"], "body": text})
        return bool(data.get("commentCreate", {}).get("success"))

    def transition(self, key: str, target: str) -> bool:
        wanted = self.state_for(target)
        if not wanted:
            return True
        node = self._resolve(key)
        if not node.get("id"):
            return False
        states = (
            self._query(
                "query($id:String!){issue(id:$id){team{states{nodes{id name}}}}}",
                {"id": node["id"]},
            )
            .get("issue", {})
            .get("team", {})
            .get("states", {})
            .get("nodes", [])
        )
        state = next(
            (s for s in states if s["name"].lower() == str(wanted).lower()), None
        )
        if not state:
            logger.info("linear state '%s' not found for %s", wanted, key)
            return True
        data = self._query(
            "mutation($id:String!,$state:String!)"
            "{issueUpdate(id:$id,input:{stateId:$state}){success}}",
            {"id": node["id"], "state": state["id"]},
        )
        return bool(data.get("issueUpdate", {}).get("success"))
