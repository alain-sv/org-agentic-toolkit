# Code Review Checklist

## Pre-Review Checklist

Before requesting review, ensure:
- [ ] All tests pass locally
- [ ] Code follows style guide (linting passes)
- [ ] No console.logs or debug code
- [ ] Documentation updated if needed
- [ ] No secrets or sensitive data committed
- [ ] Branch is up to date with target branch

## Code Quality

### Functionality
- [ ] Code solves the stated problem
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logic errors
- [ ] Performance considerations addressed

### Code Style
- [ ] Follows project style guide
- [ ] Consistent naming conventions
- [ ] Appropriate comments (not too many, not too few)
- [ ] No commented-out code
- [ ] No magic numbers (use named constants)

### Architecture
- [ ] Follows existing patterns
- [ ] Appropriate separation of concerns
- [ ] No unnecessary complexity
- [ ] Reusable where appropriate
- [ ] Dependencies are reasonable

## Testing

### Test Coverage
- [ ] New code has tests
- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases
- [ ] Integration tests for API changes
- [ ] E2E tests for user-facing changes

### Test Quality
- [ ] Tests are readable and maintainable
- [ ] Tests are independent (no shared state)
- [ ] Tests use appropriate fixtures/mocks
- [ ] Test names are descriptive

## Security

### Input Validation
- [ ] All user inputs are validated
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevention for user-generated content
- [ ] CSRF protection where needed

### Authentication & Authorization
- [ ] Proper authentication checks
- [ ] Authorization checks for protected resources
- [ ] No privilege escalation vulnerabilities
- [ ] Session management is secure

### Data Protection
- [ ] No secrets in code or config files
- [ ] Sensitive data is encrypted
- [ ] PII handling complies with regulations
- [ ] Logs don't contain sensitive information

## Performance

### Efficiency
- [ ] No obvious performance issues
- [ ] Database queries are optimized
- [ ] No N+1 query problems
- [ ] Appropriate use of caching
- [ ] Large datasets handled efficiently

### Resource Usage
- [ ] Memory usage is reasonable
- [ ] No memory leaks
- [ ] File handles are closed properly
- [ ] Network requests are batched when possible

## Documentation

### Code Documentation
- [ ] Complex logic has comments explaining why
- [ ] Public APIs are documented
- [ ] Function/method docstrings are clear
- [ ] README updated if needed

### Change Documentation
- [ ] PR description explains what and why
- [ ] Breaking changes are documented
- [ ] Migration guide if needed
- [ ] Changelog updated

## Dependencies

### Package Management
- [ ] New dependencies are necessary
- [ ] Dependencies are up to date
- [ ] Security vulnerabilities addressed
- [ ] License compatibility checked

## Git & Version Control

### Commit Quality
- [ ] Commit messages are clear
- [ ] Commits are logically grouped
- [ ] No merge commits in feature branch
- [ ] Branch is rebased on target

### File Management
- [ ] No unnecessary files committed
- [ ] .gitignore is up to date
- [ ] No large binary files
- [ ] Generated files excluded

## Review Feedback Guidelines

### For Reviewers
- Be constructive and respectful
- Explain the "why" behind suggestions
- Focus on code quality, not personal preferences
- Approve when standards are met
- Request changes when standards are not met
- Respond promptly to review requests

### For Authors
- Respond to all comments
- Ask questions if feedback is unclear
- Don't take feedback personally
- Thank reviewers for their time
- Learn from feedback to improve future code

## Approval Criteria

Code should be approved when:
- ✅ All checklist items are satisfied
- ✅ At least one approval from team member
- ✅ All CI checks pass
- ✅ No blocking issues remain
- ✅ Reviewer understands the changes

## Common Issues to Watch For

1. **Security vulnerabilities**: SQL injection, XSS, auth bypass
2. **Performance problems**: N+1 queries, missing indexes, inefficient algorithms
3. **Test gaps**: Missing edge cases, no error handling tests
4. **Code smells**: Duplication, long functions, high complexity
5. **Breaking changes**: Undocumented API changes, migration issues
6. **Dependency issues**: Outdated packages, security vulnerabilities
7. **Documentation gaps**: Missing docstrings, unclear PR descriptions
