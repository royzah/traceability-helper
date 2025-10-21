# Jira-GitHub Traceability Framework

Automated bidirectional traceability between GitHub and Jira with zero developer overhead.

## Overview

This framework enforces that every commit and pull request is linked to a Jira issue through automation, providing complete traceability without impacting developer workflow. The system automatically:

- Injects Jira issue keys into commit messages
- Validates branch names and commits via CI
- Creates bidirectional links between PRs and Jira issues
- Transitions issues through workflow states
- Provides audit trails and compliance reporting

## Key Features

### Developer Experience

- **Zero Manual Effort**: Jira IDs automatically injected from branch names
- **No Forms or Tickets**: Traceability data extracted from existing Git workflow
- **Smart Validation**: CI checks prevent missing references before merge
- **Multi-Project Support**: Works across all Jira projects in your organization

### Compliance & Governance

- **100% Coverage**: Every commit traced to a business requirement
- **Audit Ready**: Complete linkage for compliance reviews
- **Automated Transitions**: Issues move through workflow without manual updates
- **Real-time Sync**: Jira reflects PR status immediately

### Technical Architecture

- **GitHub Actions Based**: No external dependencies or services
- **API-First Integration**: Direct Jira REST API integration
- **Configurable Workflows**: Adapt to your specific Jira workflow
- **Enterprise Ready**: Supports Jira Cloud and Data Center

## Quick Start

### Prerequisites

- GitHub repository with Actions enabled
- Jira instance (Cloud or Data Center)
- Admin access to configure repository secrets

### Installation

1. **Copy Framework Files**

   ```bash
   git clone https://github.com/royzah/traceability-helper
   cp -r traceability-helper/.githooks your-repo/
   cp -r traceability-helper/.github your-repo/
   cp -r traceability-helper/tools your-repo/
   cp -r traceability-helper/scripts your-repo/
   ```

2. **Configure Project Keys**
   Edit `.github/workflows/jira-traceability.yml`:

   ```yaml
   env:
     JIRA_PROJECT_KEYS: "YOUR_KEYS_HERE" # e.g., "SECO,DEVOPS,ACCREQ"
   ```

3. **Set Repository Secrets**
   Go to Settings → Secrets and variables → Actions:

   - `JIRA_BASE_URL`
   - `JIRA_USER_EMAIL`
   - `JIRA_API_TOKEN`
   - `JIRA_TRANSITION_IN_REVIEW` (optional)
   - `JIRA_TRANSITION_DONE` (optional)

4. **Enable for Developers**

   ```bash
   ./scripts/install-hooks.sh
   ```

## Usage

### Branch Naming

Include the Jira issue key anywhere in the branch name:

- `feature/SECO-1234-add-authentication`
- `DEVOPS-89-fix-pipeline`
- `hotfix/urgent-ACCREQ-456`

### Commit Messages

The hook automatically adds `[PROJECT-ID]` to commits:

```bash
# You write:
git commit -m "Add user authentication"

# Git commits:
[SECO-1234] Add user authentication
```

### Pull Request Flow

1. Create PR from branch with Jira key
2. CI validates branch and all commits
3. Jira issue automatically linked
4. Status transitions on PR events:
   - Open/Ready → "In Review"
   - Merged → "Done"

## Configuration

### Workflow Transitions

Find your Jira transition IDs:

```bash
curl -u email:token \
  https://your-jira.atlassian.net/rest/api/3/issue/SECO-1234/transitions
```

Set in GitHub Secrets:

- `JIRA_TRANSITION_IN_REVIEW`: Name or ID
- `JIRA_TRANSITION_DONE`: Name or ID

### Multiple Projects

Support multiple Jira projects by updating the workflow:

```yaml
JIRA_PROJECT_KEYS: "SECO,DEVOPS,ACCREQ,FMO,KMS"
```

### Branch Protection

Enforce via Settings → Branches:

- Require status checks: `validate-branch-name`, `validate-commits`
- Include administrators (recommended)

## Architecture

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Developer │────▶│  Git Hooks   │────▶│   GitHub    │
│   Commits   │     │  Auto-inject │     │     Repo    │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    Jira     │◀────│GitHub Actions│◀────│  Pull       │
│    Issue    │     │  Validation  │     │  Request    │
└─────────────┘     │  & Sync      │     └─────────────┘
                    └──────────────┘
```

## Validation Rules

### Branch Names

- Must contain: `[A-Z]{2,10}-[0-9]+`
- Valid: `feature/SECO-123`, `DEVOPS-45-fix`
- Invalid: `feature/new-login`, `main`

### Commit Message Format

- Must start with: `[PROJECT-ID]`
- Valid: `[SECO-123] Add feature`
- Invalid: `Add feature`

### CI Checks

- **Branch validation**: On push and PR
- **Commit validation**: On PR only
- **Jira sync**: On PR events

## Troubleshooting

### Common Issues

#### Hooks not working

```bash
git config core.hooksPath  # Should output: .githooks
./scripts/install-hooks.sh  # Reinstall
```

#### Jira sync failures

- Check Actions logs for specific errors
- Verify API token permissions
- Ensure issue exists and is accessible

#### Transition not available

- Issue may be in wrong status
- Check workflow configuration in Jira
- Use numeric IDs instead of names

### Debug Commands

Test Jira connectivity:

```bash
curl -u email:token \
  https://our-jira.atlassian.net/rest/api/3/myself
```

Verify issue access:

```bash
curl -u email:token \
  https://our-jira.atlassian.net/rest/api/3/issue/SECO-1234
```

## Security Considerations

- API tokens stored in GitHub Secrets (encrypted)
- Minimal Jira permissions required (read/write issues)
- No sensitive data in repository
- Actions run in isolated environments

## Support Matrix

| Component        | Version |
| ---------------- | ------- |
| Git              | 2.30+   |
| GitHub Actions   | Latest  |
| Python           | 3.10+   |
| Jira Cloud       | Latest  |
| Jira Data Center | 8.0+    |

## Contributing

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed setup instructions.
