# Database Skills

## Database Best Practices

### Migrations
- Always use migrations for schema changes
- Make migrations backward compatible when possible
- Test migrations on staging first

### Queries
- Use parameterized queries (never string concatenation)
- Index frequently queried columns
- Avoid N+1 query problems

### Safety
- Never run destructive operations without backup
- Use transactions for multi-step operations
- Validate data before insertion
