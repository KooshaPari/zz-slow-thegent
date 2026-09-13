# Migration Overview & Strategy Guide

**Last Updated:** February 20, 2026  
**Status:** Consolidated from 45+ migration files across the project

## Table of Contents

1. [Migration Categories](#migration-categories)
2. [Quick Start by Type](#quick-start-by-type)
3. [Migration Safety Principles](#migration-safety-principles)
4. [Validation Procedures](#validation-procedures)
5. [Troubleshooting](#troubleshooting)
6. [Related Guides](#related-guides)

---

## Migration Categories

This project has migration needs across three main categories. Choose the guide relevant to your task:

### 1. **Legacy System Migrations**

Moving from legacy architectures, patterns, or codebases to modern implementations.

**Scope:**

- System architecture replacements (legacy convergence)
- Framework upgrades (Rust, Go, Python versions)
- Dependency replacements (see legacy-migration.md)
- CLI framework transitions (e.g., Click → Typer)

**Characteristics:**

- May affect multiple files across the codebase
- Requires comprehensive testing
- May need backward compatibility period
- Risk: Medium to High

**Examples:**

- Replacing `gorilla/mux` with `chi` router
- Migrating from `psycopg2` to `psycopg3` or `asyncpg`
- Updating `gorm` to `sqlc` or `sqlx`
- CLI library migrations (Typer vs Click)

**See Also:** `legacy-migration.md` for complete dependency migration guide

---

### 2. **Data Migrations**

Transforming data structures, storage formats, or database schemas.

**Scope:**

- Storage format changes (JSONL → SQLite, JSON → MessagePack)
- Database schema version upgrades
- Data transformation and validation
- Backup and rollback procedures

**Characteristics:**

- Non-destructive (original data preserved)
- Incremental (can run in phases)
- Requires validation at each step
- Risk: Low to Medium (with proper backups)

**Examples:**

- JSONL memory files → SQLite database migration
- JSON configuration → YAML transformation
- Version 1.0 → 2.0 schema migrations
- Cache format transitions

**See Also:** `data-migration.md` for complete data migration procedures

---

### 3. **Code Pattern Migrations**

Updating code patterns, import structures, or language-specific idioms.

**Scope:**

- Import path changes
- Module reorganization
- Deprecated API removal
- Refactoring for modernization

**Characteristics:**

- Usually localized to specific files
- Low risk if tests pass
- Can be automated with scripts
- Risk: Low

**Examples:**

- Updating legacy imports
- Removing deprecated API calls
- Moving from `sha2` to `blake3` hashing
- Encoding library updates (`hex` → `base16ct`)

**See Also:** `legacy-migration.md` for code pattern examples

---

## Quick Start by Type

### For Dependency Replacements

1. **Identify the scope:**

   ```bash
   # Find usage across codebase
   grep -r "old_library" . --include="*.rs" --include="*.go" --include="*.py"
   ```

2. **Check priority level:**
   - HIGH: Security issues (MD5), unmaintained libraries
   - MEDIUM: Performance improvements, modern alternatives
   - LOW: Optional improvements

3. **Follow the migration guide:**
   - See `legacy-migration.md` for specific patterns
   - Each replacement includes before/after code
   - Validation checklist provided

### For Data Migrations

1. **Create backup first:**

   ```bash
   cp -r source destination.backup.$(date +%Y%m%d)
   ```

2. **Run dry-run:**

   ```bash
   python3 scripts/migrate.py --dry-run
   ```

3. **Validate results:**
   - Check record counts
   - Spot-check data integrity
   - Verify all mappings

4. **Follow the guide:**
   - See `data-migration.md` for step-by-step procedures
   - Safety checks and validation procedures included

### For Legacy Systems

1. **Understand current state:**
   - Document current architecture
   - Identify affected components
   - Create communication plan

2. **Phase the migration:**
   - Phase 1: Identify scope
   - Phase 2: Create adapter/compatibility layer
   - Phase 3: Migrate gradually
   - Phase 4: Remove legacy code

3. **Test thoroughly:**
   - Unit tests for each component
   - Integration tests for workflows
   - Backward compatibility tests

---

## Migration Safety Principles

### 1. **Non-Destructive Changes**

- **Always backup first:** Original data/code preserved
- **Use dry-runs:** Test without committing changes
- **Version control:** Commit before and after states
- **Rollback plan:** Know how to revert

### 2. **Incremental Approach**

- **Small steps:** One logical change per commit
- **Test after each step:** Catch issues early
- **Document progress:** Keep migration log
- **Phase over time:** Don't do everything at once

### 3. **Validation**

- **Automated checks:** Unit tests, integration tests
- **Manual review:** Spot-check key areas
- **Data verification:** Count records, validate samples
- **Performance checks:** Ensure no regressions

### 4. **Communication**

- **Notify stakeholders:** Inform teams of impacts
- **Document changes:** Why, what, when
- **Provide migration guide:** Help others adapt
- **Timeline clarity:** Deprecation period before removal

---

## Validation Procedures

### For Dependency Migrations

**After updating dependencies:**

```bash
# Rust
cargo check --workspace      # Check compilation
cargo test --workspace       # Run all tests
cargo build --release        # Build optimized binary

# Go
go mod tidy                  # Tidy dependencies
go build ./...               # Build packages
go test ./...                # Run tests

# Python
python -m pytest             # Run test suite
mypy .                       # Type checking
black . --check              # Code formatting
```

### For Data Migrations

**After running migration:**

```bash
# Count records
SELECT COUNT(*) FROM old_table;
SELECT COUNT(*) FROM new_table;

# Spot-check samples
SELECT * FROM new_table LIMIT 10;

# Verify data integrity
-- Check for NULL values where not expected
-- Validate data types
-- Verify referential integrity

# Performance check
-- Compare query times
-- Check index usage
-- Monitor disk space
```

### For Legacy System Migrations

**After migration complete:**

1. **Functional tests:** Verify all features work
2. **Integration tests:** Verify systems communicate
3. **Performance tests:** Ensure no regressions
4. **Backward compatibility:** Old API still works (if applicable)
5. **Documentation:** Updated and accurate

---

## Troubleshooting

### Common Migration Issues

#### "Migration rollback needed"

1. Determine what went wrong
2. Stop the migration process
3. Restore from backup
4. Investigate root cause
5. Plan mitigation strategy
6. Retry with fixes

#### "Incomplete migration state"

**Scenario:** Migration partially completed but failed

1. **Check state:**

   ```bash
   # For data migrations
   SELECT COUNT(*) FROM migrated_data;
   SELECT COUNT(*) FROM original_data;
   ```

2. **Options:**
   - Complete the migration (if safe)
   - Rollback to backup
   - Fix and resume

#### "Performance degradation after migration"

1. Check indexes are created
2. Verify data distribution
3. Run query plan analysis
4. Compare old vs new performance
5. Optimize if needed

#### "Test failures after migration"

1. Identify which tests fail
2. Check for hardcoded assumptions
3. Update tests if expected behavior changed
4. Verify actual functionality works

---

## Related Guides

- **[Legacy Migration Guide](./legacy-migration.md)** - Dependency and code pattern migrations
- **[Data Migration Guide](./data-migration.md)** - Data format and storage migrations
- **[Phase 6 Memory Migration](./PHASE_6_MEMORY_MIGRATION_GUIDE.md)** - JSONL to SQLite migration
- **[Legacy Alternatives](./legacy-alternatives.md)** - Complete dependency audit

---

## Components with Active Migrations

The following components have documented migration paths:

- **crun** - Migration framework, version upgrades
- **trace** - Frontend migrations (TanStack Start), backend upgrades
- **thegent** - Architecture refactoring, hook system upgrades
- **pheno-sdk** - CLI framework migrations, context folding
- **zen-mcp-server** - MCP protocol migrations, tool migrations
- **atoms-mcp-prod** - Tool integration migrations
- **4sgm** - LangFuse integration migrations

---

## Migration Checklist

Before starting any migration:

- [ ] Understand scope and dependencies
- [ ] Create backup/branch
- [ ] Review existing guides
- [ ] Identify test coverage gaps
- [ ] Plan rollback strategy
- [ ] Communicate with team
- [ ] Start with dry-run or staging
- [ ] Validate at each step
- [ ] Test thoroughly
- [ ] Update documentation
- [ ] Deploy to production
- [ ] Monitor for issues

---

**Generated:** 2026-02-20  
**Consolidated from:** 45+ migration files across crun, trace, thegent, pheno-sdk, zen-mcp-server, and related components
