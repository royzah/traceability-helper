#!/usr/bin/env bash
# Install Git hooks for automatic issue-key injection.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Installing traceability hooks..."

git config core.hooksPath .githooks
chmod +x "${REPO_ROOT}/.githooks/prepare-commit-msg" "${REPO_ROOT}/.githooks/commit-msg" 2>/dev/null || true

if [[ "$(git config core.hooksPath)" != ".githooks" ]]; then
	echo "ERROR: failed to set core.hooksPath" >&2
	exit 1
fi

echo "Done. Hooks active via core.hooksPath=.githooks"
echo
echo "Optional per-repo config:"
echo "  git config traceability.keyPlacement suffix|prefix|footer   # default suffix"
echo "  git config traceability.keyPattern '<regex>'                # default PROJ-123"
echo
echo "Usage:"
echo "  1. Branch with the issue key:  git switch -c feat/SECO-1234-thing"
echo "  2. Commit normally; the key is appended:  feat: thing (SECO-1234)"
echo "  3. Push and open a PR; CI links it to the tracker."
