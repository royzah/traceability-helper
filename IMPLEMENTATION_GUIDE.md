# Jira-GitHub Traceability Implementation Guide

## Executive Summary

This guide provides step-by-step instructions for implementing automated Jira-GitHub traceability in your repository. The system enforces that every commit and PR is linked to a Jira issue with zero manual effort from developers.

## Prerequisites

- GitHub repository with Actions enabled
- Jira Cloud or Data Center instance
- Jira API credentials with issue edit permissions
- Git 2.30+ (for hooks support)
- Python 3.10+ on CI runners

## Implementation Steps

### Step 1: Copy Required Files

Clone the traceability-helper template and copy these files to your repository:

```text
.githooks/
├── prepare-commit-msg
└── commit-msg

.github/
└── workflows/
    ├── jira-traceability.yml
    └── metrics-export.yml (optional)

tools/
├── jira_sync.py
├── requirements.txt
└── config.yaml

scripts/
└── install-hooks.sh
```

### Step 2: Configure Jira Project Keys

Edit `.github/workflows/jira-traceability.yml` to specify which Jira project keys are valid for your repository:

```yaml
env:
  JIRA_PROJECT_KEYS: "SECO,DEVOPS,ACCREQ" # Add project keys here
```

### Step 3: Set Repository Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

| Secret Name                 | Description                     | Example                    |
| --------------------------- | ------------------------------- | -------------------------- |
| `JIRA_BASE_URL`             | Your Jira instance URL          | `https://jira.company.com` |
| `JIRA_USER_EMAIL`           | Email for API authentication    | `bot@company.com`          |
| `JIRA_API_TOKEN`            | API token (Cloud) or PAT (DC)   | `ATATT3xFfG...`            |
| `JIRA_TRANSITION_IN_REVIEW` | Transition name/ID for PR open  | `In Review` or `21`        |
| `JIRA_TRANSITION_DONE`      | Transition name/ID for PR merge | `Done` or `31`             |

### Step 4: Enable Branch Protection

Go to **Settings → Branches** and add a branch protection rule for `main`:

- **Required status checks**: Enable `validate-branch-name` and `validate-commits`
- **Require branches to be up to date**: Recommended
- **Include administrators**: Recommended for consistency

### Step 5: Install Hooks for Developers

Add this to your repository README:

```markdown
## Setup for Developers

Run once after cloning:
./scripts/install-hooks.sh

This enables automatic Jira ID injection in commits based on your branch name.
```

## Workflow Rules

### Branch Naming Convention

Branches must include a valid Jira key:

- ✓ `feature/SECO-1234-add-auth`
- ✓ `hotfix/DEVOPS-89-fix-pipeline`
- ✓ `ACCREQ-456-refactor`
- ✗ `feature/new-login` (missing Jira key)

### Commit Messages

Commits must start with `[PROJECT-ID]`:

- ✓ `[SECO-1234] Add authentication module`
- ✓ `[DEVOPS-89] Fix: pipeline timeout issue`
- ✗ `Add new feature` (missing Jira reference)

The git hook automatically adds this prefix from your branch name.

## Verification Checklist

After implementation, verify:

1. Create a branch with pattern `PROJECT-####-description`
2. Make a commit (verify `[PROJECT-####]` is auto-added)
3. Open a PR (verify CI checks pass)
4. Check Jira issue has PR link added
5. Merge PR and verify Jira transitions to Done

## Troubleshooting

### Issue: Hooks not working

- Ensure `scripts/install-hooks.sh` was executed
- Verify with: `git config core.hooksPath` (should show `.githooks`)

### Issue: Jira sync failing

- Check Actions logs for specific errors
- Verify API token has correct permissions
- Ensure Jira project key exists and is accessible

### Issue: Transition not working

- Run `GET /rest/api/3/issue/{issueKey}/transitions` to find valid transition IDs
- Use numeric IDs instead of names for reliability
