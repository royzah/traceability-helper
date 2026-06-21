# Implementation guide

Steps to adopt the enforcement-only traceability gate in a repository.

## Prerequisites

- A GitHub or GitLab repository with CI enabled.
- A Jira instance (Cloud or Data Center) with the native integration installed
  (Jira DC DVCS connector for GitHub, or GitLab's Jira integration for GitLab).
- Git 2.30+ for the hook.

## Step 1: Add the gate

GitHub: copy `enforcement-only/github/traceability.yml` to
`.github/workflows/traceability.yml`. GitLab: copy
`enforcement-only/gitlab/.gitlab-ci.yml` and `include:` it. Set `KEY_PATTERN` or
a `PROJECT_KEYS` allowlist in the file if needed.

## Step 2: Add the PR or MR template

Copy the matching template from `enforcement-only/templates/` into the repo.

## Step 3: Enable the hook

Document this one-time command (CONTRIBUTING or onboarding); Git does not
auto-run hooks from a clone:

```sh
./scripts/install-hooks.sh
```

Placement and pattern are configurable:

```sh
git config traceability.keyPlacement suffix   # or prefix, footer
git config traceability.keyPattern '[A-Z][A-Z0-9]{1,9}-[0-9]+'
```

## Step 4: Protect the default branch and set the merge strategy

Branch protection is the enforcement boundary; the hook only saves manual typing.

Merge strategy: allow squash merging only; set the squash commit message to the
PR or MR title (it carries the key); enable automatic deletion of head branches.

Branch protection rule on the default branch:

- Require a PR or MR before merging, with at least one approval.
- Dismiss stale approvals when new commits are pushed.
- Require status checks to pass and branches to be up to date:
  - `Lint`
  - `Test`
  - `Require issue key`
- Require linear history (pairs with squash) and conversation resolution.
- Block force pushes and deletions, and apply the rules to administrators.

## Step 5: Connect the native integration

GitHub + Jira DC: enable the DVCS connector and Smart Commits, or an Automation
for Jira rule that transitions on merge. GitLab: enable the Jira integration.
Details: [enforcement-only/README.md](enforcement-only/README.md).

## Step 6: Verify

1. Branch `feat/PROJ-1234-thing`, commit, confirm the key is appended.
2. Open a PR or MR with the key in the title, confirm the gate passes.
3. Confirm the tracker issue shows the linked change (native integration).
4. Squash merge, confirm the issue transitions (native integration).

## Optional: coverage metrics

Copy `examples/metrics.yml` to schedule a report of the share of merged PRs that
reference a key. Output is uploaded as an artifact and written to the run
summary.
