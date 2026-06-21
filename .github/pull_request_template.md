<!-- markdownlint-disable-file MD041 -->
<!--
Title becomes the squash commit: <type>: <summary> (KEY)
e.g.  feat: add OIDC login (PROJ-1234)
The issue key MUST be in the title. On squash merge the title is the
commit on the default branch, and that is what traceability reads.
-->

## What

<!-- One or two lines: what this change does. -->

## Why

<!-- The problem or value. Link the issue below. -->

Closes <KEY>

## How tested

<!-- Tests added or run, manual steps, screenshots. -->

## Risk and rollout

<!-- Blast radius, migrations, feature flags, how to revert. "Low" is fine. -->

---

- [ ] Title is `<type>: <summary> (KEY)` and follows Conventional Commits
- [ ] Scope is one ticket, PR is small and focused
- [ ] CI green (lint, tests, traceability checks)
- [ ] Acceptance criteria met (QA verifies)
