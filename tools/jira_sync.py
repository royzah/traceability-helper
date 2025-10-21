
import os, re, json, requests, yaml

def load_event():
    p = os.environ.get("GITHUB_EVENT_PATH")
    if p and os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}

def jira_auth():
    user = os.environ["JIRA_USER_EMAIL"]
    token = os.environ["JIRA_API_TOKEN"]
    return (user, token)

def jira_base():
    return os.environ["JIRA_BASE_URL"].rstrip("/")

def project_regex():
    return re.compile(os.environ.get("JIRA_PROJECT_KEY", r"(SECO)-\d+"))

def first_key_from_text(*texts):
    pat = re.compile(r"[A-Z]+-\d+")
    for t in texts:
        m = pat.search(t or "")
        if m:
            return m.group(0).upper()
    return None

def parse_pr_info(evt):
    pr = evt.get("pull_request") or {}
    title = pr.get("title", "")
    body = pr.get("body", "")
    head_ref = pr.get("head", {}).get("ref", "")
    merged = pr.get("merged", False)
    html_url = pr.get("html_url", "")
    state = pr.get("state", "")
    action = evt.get("action", "")

    key = first_key_from_text(head_ref, title, body)
    return {
        "key": key,
        "title": title,
        "body": body,
        "head_ref": head_ref,
        "merged": merged,
        "html_url": html_url,
        "state": state,
        "action": action,
        "number": pr.get("number"),
        "base_ref": pr.get("base", {}).get("ref", ""),
    }

def ensure_remote_link(issue_key, url, title):
    # Create or update a remote link from Jira issue to PR
    api = f"{jira_base()}/rest/api/3/issue/{issue_key}/remotelink"
    payload = {
        "object": {
            "url": url,
            "title": title,
            "icon": {"url16x16": "https://github.githubassets.com/favicons/favicon.png"},
        }
    }
    r = requests.post(api, auth=jira_auth(), json=payload, timeout=20)
    if r.status_code not in (200, 201):
        print(f"::warning::Failed to create remote link: {r.status_code} {r.text}")

def add_comment(issue_key, text):
    api = f"{jira_base()}/rest/api/3/issue/{issue_key}/comment"
    r = requests.post(api, auth=jira_auth(), json={"body": text}, timeout=20)
    if r.status_code not in (200, 201):
        print(f"::warning::Failed to add comment: {r.status_code} {r.text}")

def transition_issue(issue_key, transition_name_or_id):
    if not transition_name_or_id:
        return
    # Get available transitions
    api = f"{jira_base()}/rest/api/3/issue/{issue_key}/transitions"
    r = requests.get(api, auth=jira_auth(), timeout=20)
    if r.status_code != 200:
        print(f"::warning::Failed to get transitions: {r.status_code} {r.text}")
        return
    tid = None
    for t in r.json().get("transitions", []):
        if t["id"] == str(transition_name_or_id) or t["name"].lower() == str(transition_name_or_id).lower():
            tid = t["id"]
            break
    if not tid:
        print("::notice::No matching transition found; skipping")
        return
    r2 = requests.post(api, auth=jira_auth(), json={"transition": {"id": tid}}, timeout=20)
    if r2.status_code not in (200, 204):
        print(f"::warning::Transition failed: {r2.status_code} {r2.text}")

def main():
    evt = load_event()
    pr = parse_pr_info(evt)
    if not pr["key"]:
        print("::notice::No Jira key found in PR; nothing to sync.")
        return

    issue_key = pr["key"]
    ensure_remote_link(issue_key, pr["html_url"], f"GitHub PR #{pr['number']} ({pr['head_ref']} → {pr['base_ref']})")

    action = pr["action"]
    if action in ("opened", "reopened", "ready_for_review", "synchronize"):
        add_comment(issue_key, f"Linked PR: {pr['html_url']}")
        transition_issue(issue_key, os.environ.get("JIRA_TRANSITION_IN_REVIEW", ""))
    elif action == "closed":
        if pr["merged"]:
            add_comment(issue_key, f"PR merged: {pr['html_url']}")
            transition_issue(issue_key, os.environ.get("JIRA_TRANSITION_DONE", ""))
        else:
            add_comment(issue_key, f"PR closed without merge: {pr['html_url']}")

if __name__ == "__main__":
    main()
