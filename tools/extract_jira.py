
import os, re, json, sys

PROJECT_REGEX = re.compile(os.environ.get("JIRA_PROJECT_REGEX", r"(SECO)-\d+"), re.IGNORECASE)
KEY_REGEX = re.compile(r"[A-Z]+-\d+")

def extract_keys(text: str):
    return KEY_REGEX.findall(text or "")

def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    data = {}
    if event_path and os.path.exists(event_path):
        with open(event_path) as f:
            data = json.load(f)

    candidates = []

    # From branch
    ref_name = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or ""
    candidates += extract_keys(ref_name)

    # From PR title/body
    pr = data.get("pull_request") or {}
    candidates += extract_keys(pr.get("title", ""))
    candidates += extract_keys(pr.get("body", ""))

    # From commits (optional: Actions fetch-depth 0 recommended)
    # You can pass commit subjects via stdin or files if needed.

    # De-duplicate, preserve order
    seen = set()
    keys = []
    for k in candidates:
        if k.upper() not in seen:
            seen.add(k.upper())
            keys.append(k.upper())

    # Filter by project regex if present
    keys = [k for k in keys if PROJECT_REGEX.match(k)]

    out = {"jira_keys": keys, "ref_name": ref_name}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
