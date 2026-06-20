# Implementation Guide

Steps to adopt the traceability helper in a repository. The framework runs as
reusable workflows, so consuming repos hold only a thin caller plus the local
hook.

## Prerequisites

- GitHub repository with Actions enabled.
- A tracker instance (Jira Cloud or Data Center, GitHub Issues, Linear,
  YouTrack, or Azure Boards) and an API credential with issue read/write.
- Git 2.30+ for hooks; Python 3.10+ on CI runners (provided by the workflow).

## Step 1: Set secrets

Add the selected provider's secrets at the org level (shared across repos) or
per repo, under Settings > Secrets and variables > Actions. The required set per
provider is listed in the README. Org-level secrets plus `secrets: inherit` in
the caller mean a new repo needs no credential setup.

## Step 2: Add the caller workflow

Copy `examples/traceability.yml` to `.github/workflows/traceability.yml` and set
the provider and project keys:

```yaml
jobs:
  traceability:
    uses: royzah/traceability-helper/.github/workflows/traceability.yml@v1
    with:
      provider: jira
      project_keys: "SECO,DEVOPS"
    secrets: inherit
```

Pin `@v1` to a released tag. Bump the tag across repos to roll out changes.

## Step 3: Enable the hook

Document this one-time command in the consuming repo (CONTRIBUTING or
onboarding); Git will not auto-run hooks from a clone:

```sh
./scripts/install-hooks.sh
```

The hook appends the key from the branch name to each commit subject. Placement
and pattern are configurable:

```sh
git config traceability.keyPlacement suffix   # or prefix, footer
git config traceability.keyPattern '[A-Z][A-Z0-9]{1,9}-[0-9]+'
```

## Step 4: Protect the branch

Under Settings > Branches, require these status checks on the default branch:

- `Validate branch name`
- `Validate commit messages`

CI is the enforcement boundary; the hook only saves manual typing.

## Step 5: Verify

1. Create a branch named with a key, e.g. `feat/SECO-1234-thing`.
2. Commit and confirm the key is appended: `feat: thing (SECO-1234)`.
3. Open a PR and confirm the validation checks pass.
4. Confirm the tracker issue shows the PR link and a comment.
5. Merge and confirm the issue transitions to done.

## Optional: coverage metrics

Copy `examples/metrics.yml` to schedule a weekly report of the share of merged
PRs that reference a key. Output is uploaded as an artifact and written to the
run summary.

## Troubleshooting

- Hook inactive: confirm `git config core.hooksPath` returns `.githooks`.
- Sync failures: check the Actions log; verify the credential has issue edit
  permission and the issue key exists.
- Transition skipped: the transition name or id must match the tracker
  workflow; numeric ids are more reliable for Jira.
- Wrong key shape: set `key_pattern` in the caller (GitHub uses `#123`, Azure
  uses `AB#123`).
