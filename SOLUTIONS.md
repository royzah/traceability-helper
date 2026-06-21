# Two solutions

Two ways to guarantee every change traces to an issue. Both share the Git
hooks, the branch and PR conventions, and squash-and-merge (see
[WORKFLOW.md](WORKFLOW.md)). They differ in who links and transitions.

| aspect              | A: full tool                                                     | B: enforcement-only                 |
| ------------------- | ---------------------------------------------------------------- | ----------------------------------- |
| enforce key present | branch, commit, PR/MR title                                      | branch, PR/MR title                 |
| link and comment    | this tool, from CI                                               | native integration                  |
| transition state    | this tool, from CI                                               | native integration or smart commits |
| coverage metric     | yes (`tools/metrics.py`)                                         | optional (reuse it)                 |
| credentials in CI   | tracker API token                                                | none                                |
| consuming-repo code | caller workflow + hook                                           | one CI job + hook                   |
| trackers and hosts  | Jira, Linear, YouTrack, Azure, Trello; GitHub, GitLab, Bitbucket | whatever the integration covers     |

A is the repo root; B is [enforcement-only/](enforcement-only).

## Which to choose

- B: a native integration already links and transitions (GitHub or GitLab with
  Jira); the gap is the gate plus a coverage number. Smallest footprint.
- A: no native integration to lean on, several trackers or hosts on one process,
  or central control rolled out by tag.

## On-prem

Both support Jira Data Center and both hosts.

- Jira DC: REST v2 and a PAT. Solution A: set `JIRA_API_VERSION=2`,
  `JIRA_AUTH=bearer`.
- GitHub + Jira DC: native linking via Jira DC's DVCS connector.
- GitLab + Jira DC: native linking via GitLab's Jira integration (targets Server
  and Data Center).

A ships a GitLab host adapter and B ships a GitLab gate, so an on-prem GitLab
move is covered either way. Details:
[enforcement-only/README.md](enforcement-only/README.md).

## Before pruning Solution A

Delete the full tool only after a pilot on one real repo confirms the native
integration covers what A does. Check all of:

- [ ] Native integration installed and authorized (Jira DC DVCS connector for
      GitHub, or GitLab's Jira integration for GitLab).
- [ ] A merged PR/MR auto-links to the issue (the development panel shows it).
- [ ] A merged PR/MR moves the issue to Done automatically, verified on a real
      ticket (automation rule, or keyword on GitLab).
- [ ] An opened PR/MR moves the issue to In Review, if that step is wanted.
- [ ] Only one tracker is in use (no Linear, YouTrack, Azure, or Trello need).
- [ ] Coverage still comes from `tools/metrics.py`, which the prune keeps.
- [ ] Branch protection requires the gate check on the default branch.

When every box is ticked, merge the prune branch. Until then, keeping A costs
almost nothing and stays recoverable.
