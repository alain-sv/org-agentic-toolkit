# Git Skills

## Branch Management

### Creating Branches
- Always create feature branches from `develop` or `main`
- Use descriptive branch names: `feature/user-authentication`, `fix/login-bug`, `hotfix/security-patch`
- Never commit directly to `main` or `develop`

### Branch Cleanup
- Delete merged branches after merge
- Keep feature branches up to date with base branch
- Use `git rebase` to keep history clean (avoid merge commits in feature branches)

## Commit Best Practices

### Commit Messages
- Use conventional commits format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`
- Scope is optional but recommended (e.g., `feat(auth): add OAuth2 support`)
- Description should be imperative mood, lowercase, no period
- Body (optional) explains what and why, separated by blank line

### Commit Examples
```
feat(auth): add JWT token refresh

Implement automatic token refresh before expiration.
Uses refresh token stored in httpOnly cookie.

fix(api): handle null response in user endpoint

test(utils): add tests for date formatting

chore(deps): update axios to 1.6.0
```

### Commit Frequency
- Commit early and often (small, logical units)
- Each commit should be a complete, working change
- Use `git add -p` to stage specific changes
- Squash commits before merging if needed

## Pull Request Workflow

### Before Creating PR
1. Ensure all tests pass locally
2. Rebase on target branch: `git rebase origin/develop`
3. Resolve any conflicts
4. Run linters and formatters
5. Update documentation if needed

### PR Best Practices
- Keep PRs focused and small (easier to review)
- Include clear description of changes
- Reference related issues/tickets
- Add screenshots for UI changes
- Request specific reviewers
- Respond to review feedback promptly

## Advanced Git Operations

### Interactive Rebase
```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# Reorder, squash, or edit commits
# Use: pick, reword, edit, squash, fixup, drop
```

### Stashing
```bash
# Save current changes
git stash save "descriptive message"

# List stashes
git stash list

# Apply and keep stash
git stash apply

# Apply and remove stash
git stash pop

# Drop specific stash
git stash drop stash@{0}
```

### Finding Issues
```bash
# Find when bug was introduced
git bisect start
git bisect bad
git bisect good <commit>
# Test and mark good/bad until found

# Search commit messages
git log --grep="keyword"

# Search code history
git log -S "function_name" --source --all
```

## Common Mistakes to Avoid

1. **Force pushing to shared branches**: Never `git push --force` to `main` or `develop`
2. **Committing secrets**: Always check `.gitignore` and use secret management
3. **Large binary files**: Use Git LFS or external storage
4. **Mixing concerns**: One commit = one logical change
5. **Ignoring merge conflicts**: Always resolve conflicts properly, don't just accept one side
