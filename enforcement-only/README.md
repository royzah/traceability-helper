# Enforcement-only gate

A hard gate that every change carries an issue key. Linking, comments, and
transitions are delegated to the native host-to-Jira integration. No secrets.

## What it is

- The Git hooks (`../.githooks`, key injection) and one CI job that fails a PR
  or MR whose branch and title lack a key.
- Coverage stays available via `../tools/metrics.py`.

## Squash insight

With squash merging, only the PR or MR title reaches the default branch, so
enforcing the branch and title is enough; CI no longer fails on a messy
work-in-progress commit. The hook still injects keys for convenience.

## GitHub + Jira Data Center

1. Copy `github/traceability.yml` to `.github/workflows/traceability.yml`; set
   `PROJECT_KEYS` for an allowlist.
2. Copy `templates/pull_request_template.md` to `.github/pull_request_template.md`.
3. Install hooks once per clone: `../scripts/install-hooks.sh`.
4. Branch protection: squash-only, squash message set to the PR title, require
   the `Require issue key` check (see `../IMPLEMENTATION_GUIDE.md`).
5. Linking and transitions: enable Jira DC's built-in DVCS connector for the
   GitHub org; use Smart Commits or an Automation for Jira rule to transition.

## GitLab + Jira Data Center

1. Copy `gitlab/.gitlab-ci.yml` into the repo and `include:` it.
2. Copy `templates/merge_request_template.md` to
   `.gitlab/merge_request_templates/Default.md`.
3. Install hooks once per clone: `../scripts/install-hooks.sh`.
4. Protect the default branch: "Squash commits when merging", require approvals
   and a green pipeline, squash message set to the MR title.
5. Linking and transitions: enable GitLab's Jira integration (Settings,
   Integrations, Jira). It targets Server and Data Center, cross-links commits
   and MRs, comments, and transitions from keywords like `Closes PROJ-1234`.

## Why the backend differs

Jira DC's DVCS connector supports GitHub and Bitbucket, not GitLab; GitLab ships
its own Jira integration instead. The gate is identical across hosts; only the
native linking backend differs.
