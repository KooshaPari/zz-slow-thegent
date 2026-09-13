# Data Migration Guide

**Last Updated:** February 20, 2026  
**Status:** Comprehensive guide for all data format and storage migrations

## Table of Contents

1. [Overview](#overview)
2. [Common Data Migration Types](#common-data-migration-types)
3. [Migration Procedures](#migration-procedures)
4. [Safety Practices](#safety-practices)
5. [Validation & Testing](#validation--testing)
6. [Troubleshooting](#troubleshooting)
7. [Specific Examples](#specific-examples)

---

## Overview

Data migrations transform how information is stored or structured without losing content. Key characteristics:

- **Non-destructive:** Original data always preserved
- **Incremental:** Can migrate in batches or phases
- **Reversible:** Rollback procedures documented
- **Validatable:** Data integrity checked at each step

### Common Scenarios

- File format changes (JSONL → SQLite, JSON → YAML)
- Database schema upgrades (v1.0 → v2.0)
- Storage backend transitions (files → database)
- Encoding changes (UTF-8 validation, compression)
- Data transformation (field additions, restructuring)

---

## Common Data Migration Types

### 1. Memory Storage Format Migrations

**From:** JSONL files per agent  
**To:** Unified SQLite database with indexes

**Benefits:**

- 2.4x faster queries through indexing
- Full-text search capability
- Reduced disk I/O
- Better data relationships

**Example:** JSONL to SQLite memory migration (Phase 6)

### 2. Configuration Format Migrations

**From:** JSON configuration files  
**To:** YAML with validation

**Benefits:**

- More human-readable
- Comments supported
- Smaller file size
- Better for version control

### 3. Database Schema Migrations

**From:** Legacy database schema  
**To:** Modern schema with relationships

**Benefits:**

- Enforced data integrity
- Better query performance
- Improved data relationships
- Normalized structure

**Characteristics:**

- May require versioning
- Backward compatibility periods
- Migration scripts for each version

### 4. Cache Format Changes

**From:** JSON/pickle cache  
**To:** MessagePack/custom format

**Benefits:**

- Faster serialization
- Smaller memory footprint
- Better for large datasets
- Faster I/O operations

---

## Migration Procedures

### Phase 1: Preparation

#### Step 1.1: Assess Current State

```bash
# Check data size and distribution
du -sh /path/to/data
find /path/to/data -type f | wc -l

# For databases
SELECT COUNT(*) FROM target_table;
SELECT SUM(octet_length(column)) FROM target_table;
```

#### Step 1.2: Create Backup

```bash
# File-based backup
cp -r /source/data /source/data.backup.$(date +%Y%m%d)

# Database backup
pg_dump dbname > dbname.backup.sql
sqlite3 source.db ".backup backup.db"
```

#### Step 1.3: Plan Validation

Document what success looks like:

- Record count should match
- Specific field values to spot-check
- Performance metrics to verify
- Data integrity constraints

### Phase 2: Dry-Run

#### Step 2.1: Preview Migration

```bash
# File migrations
python3 scripts/migrate.py --dry-run

# Database migrations
BEGIN TRANSACTION;
-- Run migration script
ROLLBACK;  -- Don't commit changes
```

#### Step 2.2: Analyze Results

- Review log output
- Check error count
- Verify record transformations
- Confirm no data loss

#### Step 2.3: Make Adjustments

If dry-run reveals issues:

- Fix transformation logic
- Adjust mapping rules
- Update field handling
- Re-run dry-run

### Phase 3: Execute Migration

#### Step 3.1: Run Migration

```bash
# File-based migration
python3 scripts/migrate.py

# Database migration
psql -d dbname -f migration.sql
```

#### Step 3.2: Monitor Progress

```bash
# For long-running migrations
tail -f migration.log | grep -E "ERROR|WARNING|Complete"

# Check database size growth
watch 'du -sh /path/to/db'
```

### Phase 4: Verification

#### Step 4.1: Count Verification

```bash
# Original data count
SOURCE_COUNT=$(find /source -name "*.jsonl" -exec wc -l {} + | tail -1 | awk '{print $1}')

# Migrated data count
MIGRATED_COUNT=$(sqlite3 /target/db.db "SELECT COUNT(*) FROM table;")

if [ $SOURCE_COUNT -eq $MIGRATED_COUNT ]; then
  echo "✓ Count matches"
else
  echo "✗ Count mismatch: $SOURCE_COUNT vs $MIGRATED_COUNT"
fi
```

#### Step 4.2: Spot-Check Data

```python
# Load sample records from both sources
import sqlite3
import json
from pathlib import Path

# Check specific records
conn = sqlite3.connect("target.db")
cursor = conn.cursor()

# Sample verification
cursor.execute("SELECT * FROM table LIMIT 10")
for row in cursor.fetchall():
    # Verify fields exist and have expected types
    assert row["id"] is not None
    assert isinstance(row["timestamp"], (int, float))
    assert row["content"] is not None
```

#### Step 4.3: Run Test Suite

```bash
python3 -m pytest tests/ -v --tb=short
```

### Phase 5: Switch Backend

#### Step 5.1: Update Configuration

```python
# Update application to use new storage
from data_storage import SQLiteStorage

storage = SQLiteStorage(db_path="/path/to/db.db")
```

#### Step 5.2: Monitor in Production

- Watch error logs
- Monitor query performance
- Check disk I/O usage
- Verify data access patterns

#### Step 5.3: Cleanup (After Verification)

```bash
# Optional: Remove old storage (keep backup for 30 days)
rm /source/data  # Only after confirmed stable
```

---

## Safety Practices

### 1. Always Backup First

```bash
# Before ANY migration
cp -r original original.backup
```

### 2. Use Dry-Run Mode

```bash
# Preview changes
migrate.py --dry-run

# Or use transactions for rollback
BEGIN TRANSACTION;
-- migration here
ROLLBACK;  -- test without committing
```

### 3. Incremental Migration

```bash
# Migrate in batches if possible
migrate.py --batch-size 1000 --start-id 0 --end-id 1000
migrate.py --batch-size 1000 --start-id 1001 --end-id 2000
```

### 4. Validate After Each Step

```bash
# Quick validation
SELECT COUNT(*) FROM source;
SELECT COUNT(*) FROM target;

# Detailed verification
SELECT id FROM source EXCEPT SELECT id FROM target;
```

### 5. Document Everything

```bash
# Keep migration log
migration.py > migration-$(date +%Y%m%d-%H%M%S).log

# Record what changed
echo "Migration: JSONL→SQLite on $(date)" >> MIGRATION_LOG.txt
echo "Source count: $(count-source)" >> MIGRATION_LOG.txt
echo "Target count: $(count-target)" >> MIGRATION_LOG.txt
```

---

## Validation & Testing

### Data Integrity Checks

```sql
-- Check for missing values
SELECT COUNT(*) as missing_ids FROM target WHERE id IS NULL;
SELECT COUNT(*) as missing_timestamps FROM target WHERE timestamp IS NULL;

-- Check for unexpected NULLs
SELECT COUNT(*) as unexpected_nulls FROM target WHERE required_field IS NULL;

-- Verify data type distribution
SELECT typeof(column), COUNT(*) FROM target GROUP BY typeof(column);

-- Check for duplicate IDs
SELECT id, COUNT(*) as count FROM target GROUP BY id HAVING COUNT(*) > 1;
```

### Performance Validation

```bash
# Compare query performance
time SELECT COUNT(*) FROM old_table WHERE id = 12345;
time SELECT COUNT(*) FROM new_table WHERE id = 12345;

# Check index effectiveness
EXPLAIN QUERY PLAN SELECT * FROM new_table WHERE id = 12345;

# Monitor disk usage
du -sh /path/to/old /path/to/new
```

### Integration Testing

```bash
# Test with actual application code
python3 -m pytest tests/integration/ -v

# Load test migration
pytest tests/ -k "migration" -v

# Backward compatibility test
pytest tests/ -k "backward_compat" -v
```

---

## Troubleshooting

### Data Loss Detection

**Symptom:** Migrated record count < Source record count

**Diagnosis:**

```sql
-- Find missing records
SELECT id FROM source
WHERE id NOT IN (SELECT id FROM target);

-- Check for filtering issues
SELECT COUNT(*) FROM source WHERE condition = 'expected';
SELECT COUNT(*) FROM target WHERE condition = 'expected';
```

**Solution:**

1. Investigate missing records
2. Fix transformation logic
3. Restore from backup
4. Re-run migration

### Corruption Detection

**Symptom:** Data looks wrong after migration

**Diagnosis:**

```python
# Compare samples
source_record = source.get("record_id")
target_record = target.get("record_id")

if source_record != target_record:
    print(f"Mismatch: {source_record} vs {target_record}")
    # Review transformation logic
```

**Solution:**

1. Check transformation functions
2. Validate data types
3. Restore from backup if needed

### Performance Issues

**Symptom:** Queries slower after migration

**Diagnosis:**

```sql
-- Check indexes
SELECT * FROM sqlite_master WHERE type='index';

-- Analyze table statistics
ANALYZE;

-- Check query plans
EXPLAIN QUERY PLAN SELECT * FROM table WHERE id = 123;
```

**Solution:**

1. Create missing indexes
2. Rebuild statistics
3. Optimize schema design
4. Consider data partitioning

---

## Specific Examples

### Example 1: JSONL to SQLite (Memory Storage)

**Scenario:** Migrating agent memory from JSONL files to SQLite

**Step 1: Backup**

```bash
cp -r ~/.claude/civilization/agents ~/.claude/civilization/agents.backup.$(date +%Y%m%d)
```

**Step 2: Dry-run**

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py --dry-run
```

**Step 3: Execute**

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py
```

**Step 4: Verify**

```bash
# Count verification
JSONL_COUNT=$(find ~/.claude/civilization/agents -name "memory.jsonl" -exec wc -l {} + | tail -1 | awk '{print $1}')
SQLITE_COUNT=$(sqlite3 ~/.claude/civilization/memories.db "SELECT COUNT(*) FROM memories;")
echo "JSONL: $JSONL_COUNT, SQLite: $SQLITE_COUNT"

# Per-agent check
python3 scripts/verify_migration.py
```

**Step 5: Switch**

```python
# Update application config
from data_storage import SQLiteMemoryStorage

storage = SQLiteMemoryStorage()
```

### Example 2: Database Schema Upgrade

**Scenario:** Upgrading from schema v1.0 to v2.0

**Step 1: Create new schema**

```sql
BEGIN TRANSACTION;

-- Create new tables with v2.0 structure
CREATE TABLE users_v2 (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_email CHECK (email LIKE '%@%.%')
);

-- Migrate data
INSERT INTO users_v2 (id, username, email, created_at)
SELECT id, username, email, created_at FROM users;

-- Verify count
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM users_v2;

-- Rollback if counts don't match
ROLLBACK;
```

**Step 2: Switch tables**

```sql
BEGIN TRANSACTION;

ALTER TABLE users RENAME TO users_v1;
ALTER TABLE users_v2 RENAME TO users;

-- Test application
-- If tests pass, commit:
COMMIT;

-- Otherwise rollback:
-- ROLLBACK;
```

**Step 3: Cleanup** (after verification)

```sql
DROP TABLE users_v1;
```

---

## Migration Checklist

- [ ] Create backup of original data
- [ ] Review migration script/plan
- [ ] Run dry-run and verify output
- [ ] Document migration procedure
- [ ] Execute migration
- [ ] Verify record counts match
- [ ] Spot-check sample data
- [ ] Run test suite
- [ ] Monitor in staging environment
- [ ] Update application configuration
- [ ] Deploy to production
- [ ] Monitor for issues
- [ ] Keep backup for 30+ days
- [ ] Document completion

---

## Related Resources

- **[Migration Overview](./migration-overview.md)** - General migration strategies
- **[Legacy Migration Guide](./legacy-migration.md)** - Dependency and code migrations
- **[Phase 6 Memory Migration](./PHASE_6_MEMORY_MIGRATION_GUIDE.md)** - Detailed JSONL→SQLite example

---

**Generated:** 2026-02-20  
**Consolidated from:** Data migration procedures across crun, trace, thegent, pheno-sdk, zen-mcp-server, and memory storage systems
