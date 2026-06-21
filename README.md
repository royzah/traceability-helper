# Traceability Helper

Guarantee every change traces to an issue, with zero developer overhead. A Git
hook injects the issue key from the branch name, and CI fails any change whose
branch or PR/MR title lacks a key. Linking the change to the issue and moving
its state are handled by the native host-to-Jira integration. A scheduled job
reports coverage.

Works on GitHub and GitLab, with Jira (Cloud or Data Center). Process and roles:
[WORKFLOW.md](WORKFLOW.md). Setup: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md).

## What it does

- Injects the key into commits from the branch name (Conventional-Commits safe).
- Fails CI on a branch or PR/MR title that has no key.
- Defers linking, comments, and transitions to the native integration.
- Reports traceability coverage across merged changes.

## The gate

Pick the host and copy one file:

| host   | gate                                       | template                                               |
| ------ | ------------------------------------------ | ------------------------------------------------------ |
| GitHub | `enforcement-only/github/traceability.yml` | `enforcement-only/templates/pull_request_template.md`  |
| GitLab | `enforcement-only/gitlab/.gitlab-ci.yml`   | `enforcement-only/templates/merge_request_template.md` |

Full setup, branch protection, and the native integration:
[enforcement-only/README.md](enforcement-only/README.md).

## Native linking and transitions

- GitHub + Jira: the Cloud app, or the Data Center DVCS connector, links
  commits, branches, and PRs; transitions run via Smart Commits or Automation
  for Jira.
- GitLab + Jira (Server, Data Center, or Cloud): GitLab's Jira integration
  cross-links and transitions from keywords like `Closes PROJ-1234`.

## Coverage

Schedule [examples/metrics.yml](examples/metrics.yml) to report the share of
merged PRs that reference a key (GitHub). Output is uploaded as an artifact and
written to the run summary.

## Convention

- Branch: `<type>/<KEY>-<slug>`, e.g. `feat/PROJ-1234-add-auth`.
- Commit: the key is appended as a suffix, e.g. `feat: add auth (PROJ-1234)`.
- PR/MR: squash and merge, with the key in the title (it becomes the commit on
  the default branch).

## Hook

Enable once per clone:

```sh
./scripts/install-hooks.sh
```

## Layout

```text
.githooks/                 prepare-commit-msg, commit-msg
enforcement-only/          GitHub and GitLab gates, PR/MR templates, setup
.github/workflows/         metrics.yml (reusable), ci.yml
examples/metrics.yml       caller for the coverage report
scripts/install-hooks.sh   sets core.hooksPath
tools/metrics.py           coverage report
```

## License

MIT. See [LICENSE](LICENSE).
