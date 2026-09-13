# Phase 6: JSONL to SQLite Memory Migration Guide

**Applies to:** Civilization Framework deployments using Phase 5B JSONL memory storage
**Target:** Phase 6 SQLite memory backend
**Last updated:** 2026-02-19

---

## 1. Overview

Phase 6 introduces a SQLite-backed memory storage backend that replaces the original JSONL file-based storage from Phase 5B. The migration tool converts existing JSONL memory files into a single indexed SQLite database, providing:

- **2.4x faster queries** through indexed lookups instead of full file scans
- **Full-text keyword search** across memory content
- **Typed memory relationships** (causal, similarity, contradiction edges)
- **SQL-native aggregation** for analytics and dashboard integration
- **Reduced disk I/O** from single-file database vs per-agent JSONL files

The migration is non-destructive. Original JSONL files are never modified or deleted by the migration tool.

---

## 2. Prerequisites

- Python 3.9 or later (for `pathlib`, `dataclasses`, and `sqlite3` stdlib modules)
- Existing JSONL memory files in the agent data directory
- Write access to the target SQLite database path
- Sufficient disk space (~1.2x the total JSONL file size, to hold both formats during transition)

---

## 3. Before You Start

### Back Up Your Data

The migration tool does not modify JSONL files, but creating an explicit backup is still recommended:

```bash
# Back up the entire agent data directory
cp -r ~/.claude/civilization/agents ~/.claude/civilization/agents.backup.$(date +%Y%m%d)
```

### Check Existing Data

Verify that JSONL memory files exist and contain valid data:

```bash
# List all agent memory files
find ~/.claude/civilization/agents -name "memory.jsonl" -type f

# Check a sample file for valid JSONL
head -3 ~/.claude/civilization/agents/<agent-id>/memory.jsonl
```

Each line in a valid JSONL file should be a complete JSON object containing at minimum `memory_id` (or `id`), `agent_id`, `memory_type`, `timestamp`, and `content`.

### Check Disk Space

```bash
# Total size of JSONL files
du -sh ~/.claude/civilization/agents/*/memory.jsonl 2>/dev/null | tail -1

# Available disk space
df -h ~/.claude/civilization/
```

The SQLite database will be approximately the same size as the combined JSONL files, plus index overhead (~20%).

---

## 4. Migration Steps

### Step A: Dry Run (Preview)

Run the migration tool in dry-run mode to preview what will be migrated without writing anything:

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py --dry-run
```

Expected output:

```
Source: /Users/<you>/.claude/civilization/agents
Target: /Users/<you>/.claude/civilization/memories.db
Dry run: True

Found 3 JSONL file(s) to migrate:

  Migrating: /Users/<you>/.claude/civilization/agents/agent-alpha/memory.jsonl
    Records: 42 total, 42 migrated, 0 skipped, 0 errors

  Migrating: /Users/<you>/.claude/civilization/agents/agent-beta/memory.jsonl
    Records: 18 total, 18 migrated, 0 skipped, 0 errors

  Migrating: /Users/<you>/.claude/civilization/agents/agent-gamma/memory.jsonl
    Records: 7 total, 7 migrated, 0 skipped, 0 errors

DRY RUN Migration complete:
  Total migrated: 67
  Total skipped:  0
  Total errors:   0
```

**Review the output.** If any records are skipped (missing `memory_id`/`id` field) or errors occur (malformed data), investigate those JSONL files before proceeding.

### Step B: Run Actual Migration

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py
```

The tool will:
1. Scan `~/.claude/civilization/agents/*/memory.jsonl` for JSONL files
2. Create the SQLite database at `~/.claude/civilization/memories.db`
3. Initialize the schema (memories table, indexes, relationships table)
4. Insert each memory record using `INSERT OR IGNORE` (duplicates are skipped safely)
5. Commit per file and report per-file statistics

### Step C: Verify Migration

After migration, verify data integrity:

```bash
# Check record count in SQLite
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.claude/civilization/memories.db')
count = conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]
print(f'Total memories in SQLite: {count}')
# Per-agent counts
for row in conn.execute('SELECT agent_id, COUNT(*) as cnt FROM memories GROUP BY agent_id'):
    print(f'  {row[0]}: {row[1]} memories')
conn.close()
"
```

Compare the SQLite count against the JSONL line counts:

```bash
# Count lines in all JSONL files (excluding blank lines)
find ~/.claude/civilization/agents -name "memory.jsonl" -exec grep -c '.' {} +
```

The counts should match (minus any records skipped due to missing IDs).

### Step D: Switch Backend

Once verification passes, update your application code to use the SQLite backend:

```python
from civilization_memory_storage import SQLiteMemoryStorage

# Default path: ~/.claude/civilization/memories.db
storage = SQLiteMemoryStorage()

# Or specify a custom path
storage = SQLiteMemoryStorage(db_path=Path("/path/to/memories.db"))
```

The `SQLiteMemoryStorage` class implements the same `MemoryStorage` interface as `JSONLMemoryStorage`, so all existing code that uses the abstraction layer works without changes.

---

## 5. Migration Commands Reference

### Default Paths

```bash
# Standard migration (default paths)
python3 scripts/migrate_memory_jsonl_to_sqlite.py
```

Source: `~/.claude/civilization/agents` (scans `*/memory.jsonl`)
Target: `~/.claude/civilization/memories.db`

### Custom Paths

```bash
# Custom source directory
python3 scripts/migrate_memory_jsonl_to_sqlite.py \
  --source-dir /path/to/agents

# Custom database path
python3 scripts/migrate_memory_jsonl_to_sqlite.py \
  --db-path /path/to/memories.db

# Both custom
python3 scripts/migrate_memory_jsonl_to_sqlite.py \
  --source-dir /path/to/agents \
  --db-path /path/to/memories.db
```

### Dry Run

```bash
# Preview only (no database created or modified)
python3 scripts/migrate_memory_jsonl_to_sqlite.py --dry-run
```

### Full Options

```
usage: migrate_memory_jsonl_to_sqlite.py [-h] [--dry-run] [--source-dir SOURCE_DIR] [--db-path DB_PATH]

Migrate JSONL memories to SQLite

options:
  -h, --help            show this help message and exit
  --dry-run             Preview without writing
  --source-dir SOURCE_DIR
                        Base directory containing agent subdirs
                        (default: ~/.claude/civilization/agents)
  --db-path DB_PATH     Target SQLite database path
                        (default: ~/.claude/civilization/memories.db)
```

---

## 6. Verification Steps

After migration, run these checks to confirm data integrity:

### A. Record Count Parity

```bash
# JSONL total
JSONL_COUNT=$(find ~/.claude/civilization/agents -name "memory.jsonl" -exec grep -c '.' {} + | awk -F: '{s+=$NF} END{print s}')
echo "JSONL records: $JSONL_COUNT"

# SQLite total
SQLITE_COUNT=$(python3 -c "
import sqlite3; conn = sqlite3.connect('$HOME/.claude/civilization/memories.db')
print(conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0]); conn.close()
")
echo "SQLite records: $SQLITE_COUNT"
```

### B. Per-Agent Verification

```python
import sqlite3
import json
from pathlib import Path

db = sqlite3.connect(Path.home() / ".claude/civilization/memories.db")
agents_dir = Path.home() / ".claude/civilization/agents"

for agent_dir in sorted(agents_dir.iterdir()):
    jsonl_file = agent_dir / "memory.jsonl"
    if not jsonl_file.exists():
        continue

    # Count JSONL records (non-blank lines)
    jsonl_count = sum(1 for line in open(jsonl_file) if line.strip())

    # Count SQLite records
    sqlite_count = db.execute("SELECT COUNT(*) FROM memories WHERE agent_id = ?", (agent_dir.name,)).fetchone()[0]

    status = "OK" if jsonl_count == sqlite_count else "MISMATCH"
    print(f"{agent_dir.name}: JSONL={jsonl_count} SQLite={sqlite_count} [{status}]")

db.close()
```

### C. Spot-Check Content

```python
import sqlite3, json
from pathlib import Path

db = sqlite3.connect(Path.home() / ".claude/civilization/memories.db")
row = db.execute("SELECT id, agent_id, content FROM memories LIMIT 1").fetchone()
print(f"ID: {row[0]}")
print(f"Agent: {row[1]}")
print(f"Content: {json.loads(row[2])}")
db.close()
```

### D. Run Test Suite

```bash
cd scripts
python3 -m pytest test_civilization_memory_storage.py test_memory_migration.py -v
```

All 28 tests (16 storage + 12 migration) should pass.

---

## 7. Rollback Procedure

If issues are discovered after migration:

### A. Keep JSONL Files

The migration tool never modifies or deletes JSONL files. They remain in place at `~/.claude/civilization/agents/<agent-id>/memory.jsonl`.

### B. Switch Back to JSONL Backend

```python
from civilization_memory_storage import JSONLMemoryStorage

# Use the original JSONL backend
storage = JSONLMemoryStorage()

# Or with a custom path
storage = JSONLMemoryStorage(base_path=Path("/path/to/agents"))
```

### C. Remove SQLite Database (Optional)

If you want to fully revert:

```bash
rm ~/.claude/civilization/memories.db
```

### D. Restore from Backup (If Needed)

If JSONL files were inadvertently modified:

```bash
rm -rf ~/.claude/civilization/agents
cp -r ~/.claude/civilization/agents.backup.<date> ~/.claude/civilization/agents
```

---

## 8. Troubleshooting

### Permission Errors

```
ERROR: [Errno 13] Permission denied: '/path/to/memories.db'
```

**Fix:** Ensure write permissions to the target database directory:

```bash
chmod 755 ~/.claude/civilization/
# Or specify a writable path
python3 scripts/migrate_memory_jsonl_to_sqlite.py --db-path /tmp/memories.db
```

### Malformed JSONL Lines

```
WARNING: Skipping malformed line 47 in .../memory.jsonl: Expecting property name: line 1 column 2
```

**Cause:** Corrupted or truncated JSON line in the JSONL file.

**Fix:** The migration tool automatically skips malformed lines and reports them. Review the source file manually:

```bash
# Show the problematic line
sed -n '47p' ~/.claude/civilization/agents/<agent-id>/memory.jsonl
```

If the data is recoverable, fix the JSON manually. If not, the record is safely skipped.

### Missing Memory IDs

```
Records: 50 total, 48 migrated, 2 skipped, 0 errors
```

**Cause:** Some memory records lack a `memory_id` or `id` field.

**Fix:** Skipped records cannot be uniquely identified for insertion. Review the JSONL file to determine if IDs can be added. Records without IDs are safely skipped.

### Disk Space Errors

```
ERROR: disk I/O error
```

**Fix:** Free disk space or specify a database path on a volume with sufficient space:

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py --db-path /volume/with/space/memories.db
```

### Duplicate Records

The migration uses `INSERT OR IGNORE`, so running the migration multiple times is safe. Duplicate `memory_id` values are silently skipped without error.

### Source Directory Not Found

```
Source directory does not exist: /path/to/agents
Nothing to migrate.
```

**Fix:** Verify the source directory path. The default is `~/.claude/civilization/agents`. If agents are stored elsewhere, use `--source-dir`:

```bash
python3 scripts/migrate_memory_jsonl_to_sqlite.py --source-dir /actual/path/to/agents
```

---

## 9. Performance After Migration

Expected improvements after migrating to SQLite:

| Operation | Before (JSONL) | After (SQLite) | Notes |
|-----------|----------------|----------------|-------|
| Query agent memories | File scan O(n) | Index lookup O(log n) | 2.4x faster |
| Filter by type + time | Full scan + filter | Compound index | ~3x faster |
| Full-text search | Substring scan | Keyword index | ~5x faster |
| Aggregate statistics | Load all + compute | SQL COUNT/AVG/GROUP BY | ~2x faster |
| Dashboard rendering | Multiple file reads | Single SQL query | Reduced I/O |
| Memory purge | Rewrite entire file | DELETE by index | ~2x faster |
| Single store | File append | INSERT + index | ~0.8x (slightly slower) |

The single-store overhead is minimal (~20% slower per write) and is offset by the read-heavy nature of memory workloads. Dashboards, analytics, search, and query operations all benefit significantly from indexed storage.

### Database Size

The SQLite database is typically comparable in size to the combined JSONL files, plus approximately 20% overhead for indexes. For a deployment with 10,000 memories across 20 agents, expect:

- JSONL total: ~5 MB (across 20 files)
- SQLite database: ~6 MB (single file, with indexes)
