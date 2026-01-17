# Organization Constitution

<!-- version: 1.0.0 -->

## Purpose

This constitution defines the immutable rules that govern all agents working within this organization. These rules cannot be overridden by project-specific or personal configurations.

## Tech Stack Standards

### Primary Languages
- Python 3.11+
- JavaScript/TypeScript (ES2020+)
- Go 1.21+

### Framework Preferences
- **Backend**: Django, FastAPI, Gin
- **Frontend**: React, Angular
- **Testing**: pytest, Jest, Go testing

## Code Standards

### General Principles
1. All code must be tested (minimum 80% coverage)
2. All code must pass linting (black, eslint, gofmt)
3. All code must be reviewed by at least one tech-lead
4. No secrets in code (use environment variables or secret management)
5. All APIs must be versioned
6. All database changes must use migrations

### Security Requirements
- Never commit secrets or API keys
- Use parameterized queries (never string concatenation for SQL)
- Validate all user inputs
- Use HTTPS for all external communications
- Follow OWASP Top 10 guidelines

### Documentation Requirements
- All public APIs must have documentation
- All complex logic must have inline comments
- README.md must be kept up to date
- Architecture decisions must be documented in ADRs

## Git Workflow

### Branching Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- Feature branches: `feature/description`
- Hotfix branches: `hotfix/description`

### Commit Messages
- Use conventional commits format
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore

### Pull Requests
- Must have at least one approval
- Must pass all CI checks
- Must be rebased on target branch
- Must have descriptive title and body

## Deployment

### Environments
- **Development**: Auto-deploy on merge to develop
- **Staging**: Manual approval required
- **Production**: Requires tech-lead approval and change ticket

### Rollback Policy
- All deployments must support instant rollback
- Database migrations must be backward compatible
- Feature flags required for major changes

## Exceptions

Any exceptions to these rules must:
1. Be explicitly documented in project.md
2. Include rationale and ticket reference
3. Be approved by tech-lead
