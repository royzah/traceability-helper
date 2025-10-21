
# SECO Traceability Helper (Jira ↔ GitHub)

**Developer‑centric traceability**: zero manual toil, full audit.  
This repo provides hooks, CI checks, and a sync action so that **every commit/PR** is automatically linked to a Jira issue (project key: `SECO`), with clean reporting.

> Guiding principle: *Blend automation + lightweight governance* — keep traceability and visibility without breaking flow.

## What you get
- **Hooks**: auto‑inject `[SECO-XXXX]` from branch name into commit messages.
- **Branch/Commit CI checks**: enforce `SECO-\d+` in branch names and commits.
- **Jira Sync GitHub Action**: on PR open/sync/merge, link PR and transition the issue.
- **Metrics exporter**: emit JSON/CSV for cycle time and review latency to feed dashboards.

---

## Quick Start

### 0) Prereqs
- Git 2.30+
- Python 3.10+ on CI (Actions runner) and locally (optional)
- A Jira Cloud (or DC) project with key **`SECO`**
- A Jira API token (Cloud) or PAT (DC) with permission to edit issues

### 1) Configure repo secrets (GitHub → Settings → Secrets and variables → Actions)
- `JIRA_BASE_URL` — e.g. `https://yourcompany.atlassian.net`
- `JIRA_USER_EMAIL` — your Jira user email for the API token
- `JIRA_API_TOKEN` — API token (Cloud) or PAT (DC)
- `JIRA_PROJECT_KEY` — set to `SECO`
- (Optional) `JIRA_TRANSITION_IN_REVIEW`, `JIRA_TRANSITION_DONE` — transition IDs or names

### 2) Install Git hooks (for all devs)
```bash
# one-time per clone
scripts/install-hooks.sh
```
This sets `core.hooksPath=.githooks` and installs **prepare-commit-msg** so commit subjects get `[SECO-1234]` injected from the current branch name (e.g. `feature/SECO-1234-improve-nats`).

### 3) Use the branch naming convention
- Branch must contain the Jira key: `SECO-1234`
  - Examples: `feature/SECO-1234-telemetry`, `hotfix/SECO-9-null-deref`

> CI will block PRs if the branch name or commits don’t include a Jira key.

### 4) Open a PR
- The workflow **links PR → Jira issue**, adds remote links and (optionally) transitions the issue (e.g. “In Review”, “Done”).

---

## How it works

### Hooks
- `.githooks/prepare-commit-msg` finds `SECO-\d+` in the **branch name** and prefixes commit subjects with `[SECO-XXXX]`.
- The hook is idempotent and won’t duplicate the tag if present already.

### CI Checks
- **Branch name** validator (push/PR): must include `SECO-\d+`.
- **Commit messages** validator (PR): every commit subject must start with `[SECO-XXXX]`.

### Jira Sync
- On PR events we parse the Jira key from the branch/PR title/commits.
- We create/update a *remote link* on the Jira issue to the PR; optionally transition state.
- We add PR metadata as a comment (commit count, reviewers, merge SHA).

### Metrics
- `dashboard/export_metrics.py` pulls PR data and writes **JSON/CSV** for lead time, review latency, and merged-throughput.
- Feed this to Grafana/Metabase or a simple Confluence chart.

---

## Local config (optional)
Copy `tools/config.example.yaml` to `tools/config.yaml` for local scripts.

---

## FAQ

**Q: What if a dev starts coding before creating a Jira ticket?**  
A: It’s fine — once a branch gets named `SECO-XXXX`, everything links automatically. If the branch was created before the ticket existed, just rename the branch (Git supports this) and amend the last commit for consistency.

**Q: Can we support multiple projects?**  
A: Yes. Set `JIRA_PROJECT_KEY` to a regex like `(SECO|OPS)` and update CI env vars.

**Q: What about squashed merges?**  
A: The PR sync uses the branch and PR title; the Jira link still works regardless of squash vs merge commits.

**Q: Self-hosted Jira Data Center?**  
A: Works the same; use PAT and REST endpoints accordingly.

---

## License
MIT
