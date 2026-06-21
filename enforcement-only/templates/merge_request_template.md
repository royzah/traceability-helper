<!-- markdownlint-disable-file MD041 -->
<!--
Title is the squash commit: <type>: <summary> (KEY), e.g. feat: add login (PROJ-1234).
The key must be in the title. Copy to .gitlab/merge_request_templates/Default.md.
-->

## What

<!-- One or two lines: what this change does. -->

## Why

<!-- The problem or value. Reference the issue, e.g. Closes PROJ-1234. -->

Closes <KEY>

## How tested

<!-- Tests added or run, manual steps, screenshots. -->

## Risk and rollout

<!-- Blast radius, migrations, feature flags, how to revert. "Low" is fine. -->

---

- [ ] Title is `<type>: <summary> (KEY)` and follows Conventional Commits
- [ ] Scope is one ticket, MR is small and focused
- [ ] Pipeline green (lint, tests, traceability check)
- [ ] Acceptance criteria met (QA verifies)
