#!/usr/bin/env bash
# Install Git hooks for automatic Jira ID injection

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Installing Jira traceability hooks..."

# Check Git version
GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="2.30"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$GIT_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "WARNING: Git version ${GIT_VERSION} detected. Version ${REQUIRED_VERSION}+ recommended for hooks."
fi

# Set hooks path
git config core.hooksPath .githooks
echo "✓ Configured Git to use .githooks directory"

# Make hooks executable
chmod +x "${REPO_ROOT}/.githooks/prepare-commit-msg" 2>/dev/null || true
chmod +x "${REPO_ROOT}/.githooks/commit-msg" 2>/dev/null || true
echo "✓ Made hook scripts executable"

# Verify configuration
HOOKS_PATH=$(git config core.hooksPath)
if [[ "${HOOKS_PATH}" == ".githooks" ]]; then
    echo "✓ Hooks installation successful"
else
    echo "ERROR: Failed to set hooks path"
    exit 1
fi

echo ""
echo "Jira traceability hooks installed successfully!"
echo ""
echo "Usage:"
echo "  1. Create a branch with a Jira issue key: git checkout -b feature/SECO-1234-description"
echo "  2. Make commits as usual - the Jira ID will be auto-added"
echo "  3. Push and create a PR - it will be linked to Jira automatically"
echo ""
echo "Valid project keys for this repository:"
echo "  Check .github/workflows/jira-traceability.yml for the JIRA_PROJECT_KEYS list"