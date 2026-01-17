# Database Skills

## Database Design Principles

### Normalization
- **1NF**: Eliminate duplicate columns, create separate tables
- **2NF**: Remove partial dependencies (all non-key attributes depend on full primary key)
- **3NF**: Remove transitive dependencies (non-key attributes depend only on primary key)
- **Denormalization**: Acceptable for performance when needed (document rationale)

### Naming Conventions
- Tables: plural, snake_case (`users`, `order_items`)
- Columns: snake_case (`user_id`, `created_at`)
- Indexes: descriptive (`idx_users_email`, `idx_orders_user_id`)
- Foreign keys: `{referenced_table}_id` (e.g., `user_id`)

## Schema Design

### Primary Keys
- Use auto-incrementing integers or UUIDs
- Never use business data as primary key
- Composite keys only when necessary

### Foreign Keys
- Always define foreign key constraints
- Use `ON DELETE CASCADE` or `ON DELETE SET NULL` appropriately
- Index foreign key columns

### Indexes
- Index columns used in WHERE, JOIN, ORDER BY clauses
- Don't over-index (slows writes)
- Use composite indexes for multi-column queries
- Monitor index usage and remove unused indexes

### Data Types
- Use appropriate types (INT vs BIGINT, VARCHAR vs TEXT)
- Use constraints (NOT NULL, CHECK, UNIQUE)
- Use ENUMs sparingly (prefer lookup tables for flexibility)

## Query Optimization

### SELECT Best Practices
- Select only needed columns (avoid `SELECT *`)
- Use LIMIT for large result sets
- Use appropriate JOIN types (INNER, LEFT, RIGHT)
- Avoid N+1 queries (use JOINs or batch loading)

### Index Usage
```sql
-- Good: Uses index on email
SELECT * FROM users WHERE email = 'user@example.com';

-- Bad: Can't use index (function on column)
SELECT * FROM users WHERE UPPER(email) = 'USER@EXAMPLE.COM';

-- Better: Index on computed column or query rewrite
SELECT * FROM users WHERE email = LOWER('USER@EXAMPLE.COM');
```

### Query Analysis
- Use `EXPLAIN` or `EXPLAIN ANALYZE` to understand query plans
- Look for full table scans (add indexes)
- Monitor slow query logs
- Use query profiling tools

## Migrations

### Migration Best Practices
- **Always use migrations** (never manual schema changes)
- **One logical change per migration**
- **Test migrations up and down**
- **Never edit existing migrations** (create new ones)
- **Backward compatible** when possible

### Migration Patterns

#### Adding Columns
```python
# Django example
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
```

#### Renaming Columns
```python
# Two-step: add new, migrate data, remove old
operations = [
    migrations.AddField(
        model_name='user',
        name='email_address',
        field=models.EmailField(max_length=255),
    ),
    migrations.RunPython(migrate_email_data),
    migrations.RemoveField(model_name='user', name='email'),
    migrations.RenameField(
        model_name='user',
        old_name='email_address',
        new_name='email',
    ),
]
```

### Data Migrations
- Separate schema migrations from data migrations
- Make data migrations idempotent
- Test with production-like data volumes
- Have rollback plan

## Transactions

### ACID Properties
- **Atomicity**: All or nothing
- **Consistency**: Valid state transitions
- **Isolation**: Concurrent transactions don't interfere
- **Durability**: Committed changes persist

### Transaction Best Practices
- Keep transactions short
- Avoid long-running transactions
- Use appropriate isolation levels
- Handle deadlocks gracefully

### Common Patterns
```python
# Django
with transaction.atomic():
    user = User.objects.create(...)
    Profile.objects.create(user=user, ...)

# SQLAlchemy
with session.begin():
    user = User(...)
    session.add(user)
    session.commit()
```

## Database Security

### SQL Injection Prevention
- **Always use parameterized queries**
- Never concatenate user input into SQL
- Use ORM query builders when possible
- Validate and sanitize inputs

### Access Control
- Use least privilege principle
- Separate read/write users
- Use connection pooling
- Encrypt sensitive data at rest

### Backup and Recovery
- Regular automated backups
- Test restore procedures
- Point-in-time recovery capability
- Backup verification

## Performance Tuning

### Connection Pooling
- Configure appropriate pool size
- Monitor connection usage
- Use read replicas for read-heavy workloads

### Caching
- Cache frequently accessed data
- Invalidate cache on updates
- Use Redis/Memcached for distributed caching
- Cache query results when appropriate

### Partitioning
- Partition large tables by date or range
- Improves query performance on large datasets
- Simplifies data archival

## Monitoring

### Key Metrics
- Query execution time
- Connection pool usage
- Lock contention
- Disk I/O
- Replication lag (if applicable)

### Tools
- Database-specific monitoring (pg_stat, MySQL performance schema)
- Application performance monitoring (APM)
- Query analyzers
- Slow query logs

## Common Anti-Patterns

1. **SELECT N+1**: Fetching related data in loops
2. **Missing indexes**: Queries scanning full tables
3. **Over-normalization**: Too many joins for simple queries
4. **Under-normalization**: Data duplication and inconsistency
5. **Ignoring migrations**: Manual schema changes
6. **No connection pooling**: Creating new connections per request
7. **Storing files in DB**: Use object storage instead
8. **No backup strategy**: Relying on single point of failure
