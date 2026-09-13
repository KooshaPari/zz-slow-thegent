<DONE>
# Plan Incorporate Research & Enhancement Plan

**Date**: 2026-02-18
**Goal**: Enhance `plan incorporate` command with task validation

---

## Current State

### Command Location

- **CLI Command**: `thegent plan incorporate` (`src/thegent/cli.py:4775`)
- **MCP Tool**: `thegent_plan_incorporate` (`src/thegent/mcp_server.py:2745`)
- **Implementation**: `incorporate_impl()` - **NOT YET IMPLEMENTED** (TODO in mcp_server.py:74)

### Expected Behavior

From documentation (`CLAUDE.md:600`):

- Scans `docs/plans/`, `docs/research/`, `docs/docset/` for fragments
- Extracts work items from fragments
- Merges into `WORK_STREAM.md`
- Preserves CLAIMED and COMPLETED sections

### Current Implementation Status

**Status**: `incorporate_impl()` function **does not exist yet**

**Evidence**:

- `mcp_server.py:74` has comment: `# incorporate_impl,  # TODO: Not implemented`
- Function is imported but not defined in `cli_impl.py`
- Command exists but implementation is missing

---

## Enhancement Requirements

### Phase 4: Plan Incorporate Enhancement

**Goal**: Add task validation during `plan incorporate` command

**Tasks**:

1. **Implement `incorporate_impl()` function**
   - [ ] Create function in `src/thegent/cli_impl.py`
   - [ ] Scan fragments from sources (`02-UNIFIED-WBS.md`, `docs/plans/`, etc.)
   - [ ] Extract work items
   - [ ] Merge into WORK_STREAM.md BACKLOG section
   - [ ] Preserve CLAIMED and COMPLETED sections

2. **Add Task Validation**
   - [ ] Validate task files in `tasks/` directory before merging
   - [ ] Use `TaskValidator` to check schema compliance
   - [ ] Collect validation errors
   - [ ] Report errors clearly
   - [ ] Block incorporation if validation fails

3. **Add Auto-Sync**
   - [ ] After successful incorporation, sync tasks to WORK_STREAM.md
   - [ ] Use `WorkStreamSync.update_work_stream_from_tasks()`
   - [ ] Provide summary of synced tasks

---

## Implementation Plan

### Step 1: Create `incorporate_impl()` Function

**File**: `src/thegent/cli_impl.py` (new function)

**Function Signature**:

```python
def incorporate_impl(cd: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md.

    Scans sources:
    - docs/plans/02-UNIFIED-WBS.md
    - docs/plans/*.md
    - docs/research/*.md
    - docs/docset/*.md

    Extracts work items and merges into WORK_STREAM.md BACKLOG.
    Preserves CLAIMED and COMPLETED sections.

    Args:
        cd: Working directory (default: current directory)
        dry_run: If True, show what would be merged without writing

    Returns:
        dict with keys: merged (int), sources (list), error (str, optional)
    """
```

**Implementation Steps**:

1. **Resolve working directory**:

```python
cwd = _resolve_cwd(cd)
if cwd is None:
    cwd = Path.cwd()
```

2. **Validate task files** (NEW):

```python
tasks_dir = cwd / "tasks"
validation_errors = []

if tasks_dir.exists() and tasks_dir.is_dir():
    from thegent.task import validate_task_file

    task_files = list(tasks_dir.glob("*.md"))
    for task_file in task_files:
        try:
            result = validate_task_file(task_file)
            if not result.valid:
                validation_errors.append(
                    {
                        "file": str(task_file),
                        "errors": result.errors,
                    }
                )
        except Exception as e:
            validation_errors.append(
                {
                    "file": str(task_file),
                    "errors": [f"Validation failed: {e}"],
                }
            )

if validation_errors:
    return {
        "error": "Task validation failed",
        "validation_errors": validation_errors,
        "merged": 0,
    }
```

3. **Scan sources**:

```python
sources = []
items_to_merge = []

# Scan 02-UNIFIED-WBS.md
wbs_path = cwd / "docs" / "plans" / "02-UNIFIED-WBS.md"
if wbs_path.exists():
    items = _extract_items_from_wbs(wbs_path)
    items_to_merge.extend(items)
    sources.append("02-UNIFIED-WBS.md")

# Scan docs/plans/*.md
plans_dir = cwd / "docs" / "plans"
if plans_dir.exists():
    for plan_file in plans_dir.glob("*.md"):
        if plan_file.name != "02-UNIFIED-WBS.md":
            items = _extract_items_from_plan(plan_file)
            items_to_merge.extend(items)
            sources.append(plan_file.name)

# Scan docs/research/*.md
research_dir = cwd / "docs" / "research"
if research_dir.exists():
    for research_file in research_dir.glob("*.md"):
        items = _extract_items_from_research(research_file)
        items_to_merge.extend(items)
        sources.append(f"research/{research_file.name}")
```

4. **Merge into WORK_STREAM.md**:

```python
work_stream_path = cwd / "docs" / "reference" / "WORK_STREAM.md"

if not dry_run:
    _merge_items_to_work_stream(work_stream_path, items_to_merge)
else:
    # Dry run: just return what would be merged
    pass

return {
    "merged": len(items_to_merge),
    "sources": sources,
    "dry_run": dry_run,
}
```

5. **Auto-sync tasks** (NEW):

```python
if not dry_run and len(items_to_merge) > 0:
    try:
        from thegent.task import WorkStreamSync

        if work_stream_path.exists() and tasks_dir.exists():
            sync = WorkStreamSync(work_stream_path, tasks_dir)
            sync_result = sync.update_work_stream_from_tasks()
            return {
                **result,
                "synced_tasks": sync_result.get("tasks_synced", 0),
            }
    except Exception as e:
        _log.warning("Failed to sync tasks to WORK_STREAM.md: %s", e)
        return {
            **result,
            "sync_warning": str(e),
        }
```

### Step 2: Helper Functions

**Extract items from WBS**:

```python
def _extract_items_from_wbs(wbs_path: Path) -> list[dict[str, Any]]:
    """Extract work items from 02-UNIFIED-WBS.md."""
    items = []
    text = wbs_path.read_text(encoding="utf-8")

    # Parse markdown table
    # Format: | WP-XXXX | Title | Status | Priority | Depends |
    # Extract rows where Status != DONE
    for line in text.splitlines():
        if "|" in line and "WP-" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                item_id = parts[1]
                title = parts[2]
                status = parts[3]
                priority = parts[4] if len(parts) > 4 else "P2"
                depends = parts[5].split(",") if len(parts) > 5 and parts[5] else []

                if status.upper() != "DONE":
                    items.append(
                        {
                            "id": item_id,
                            "title": title,
                            "status": status,
                            "priority": priority,
                            "depends": [d.strip() for d in depends if d.strip()],
                            "source": "02-UNIFIED-WBS.md",
                        }
                    )

    return items
```

**Extract items from plan files**:

```python
def _extract_items_from_plan(plan_path: Path) -> list[dict[str, Any]]:
    """Extract work items from plan markdown files."""
    items = []
    # Similar parsing logic
    return items
```

**Extract items from research files**:

```python
def _extract_items_from_research(research_path: Path) -> list[dict[str, Any]]:
    """Extract work items from research markdown files."""
    items = []
    text = research_path.read_text(encoding="utf-8")

    # Look for TODO, WP-, FR- references
    # Create research-{slug} IDs
    # Similar parsing logic
    return items
```

**Merge items to WORK_STREAM.md**:

```python
def _merge_items_to_work_stream(work_stream_path: Path, items: list[dict[str, Any]]) -> None:
    """Merge items into WORK_STREAM.md BACKLOG section."""
    if not work_stream_path.exists():
        # Create WORK_STREAM.md if it doesn't exist
        _create_work_stream(work_stream_path)

    text = work_stream_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_lines = []
    in_backlog = False
    backlog_start_idx = None

    # Find BACKLOG section
    for i, line in enumerate(lines):
        if line.strip().startswith("## BACKLOG") or line.strip().startswith("## PENDING"):
            in_backlog = True
            backlog_start_idx = i
            new_lines.append(line)
            # Add header if not present
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith("| ID"):
                new_lines.append("| ID | Title | Source | Priority | Depends |")
                new_lines.append("|----|-------|--------|----------|---------|")
            continue

        if in_backlog and line.strip().startswith("##"):
            # End of BACKLOG section, insert items
            for item in items:
                depends_str = ", ".join(item.get("depends", [])) or "-"
                new_lines.append(
                    f"| {item['id']} | {item['title']} | {item.get('source', '')} | "
                    f"{item.get('priority', 'P2')} | {depends_str} |"
                )
            in_backlog = False
            new_lines.append(line)
            continue

        new_lines.append(line)

    # If BACKLOG section not found, add it at the end
    if in_backlog:
        for item in items:
            depends_str = ", ".join(item.get("depends", [])) or "-"
            new_lines.append(
                f"| {item['id']} | {item['title']} | {item.get('source', '')} | "
                f"{item.get('priority', 'P2')} | {depends_str} |"
            )
    elif backlog_start_idx is None:
        # No BACKLOG section, create it
        new_lines.append("")
        new_lines.append("## BACKLOG")
        new_lines.append("| ID | Title | Source | Priority | Depends |")
        new_lines.append("|----|-------|--------|----------|---------|")
        for item in items:
            depends_str = ", ".join(item.get("depends", [])) or "-"
            new_lines.append(
                f"| {item['id']} | {item['title']} | {item.get('source', '')} | "
                f"{item.get('priority', 'P2')} | {depends_str} |"
            )

    work_stream_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
```

---

## Integration with Task System

### Validation Integration

**Before merging**, validate all task files:

- Use `TaskValidator.validate_task_file()`
- Collect all errors
- Block incorporation if any errors found
- Report errors clearly

### Auto-Sync Integration

**After successful merging**, sync tasks to WORK_STREAM.md:

- Use `WorkStreamSync.update_work_stream_from_tasks()`
- Update BACKLOG section with task files
- Provide summary of synced tasks

---

## Testing Plan

### Unit Tests

1. **Test `incorporate_impl()`**:
   - [ ] Test with valid fragments
   - [ ] Test with invalid task files (should fail)
   - [ ] Test dry run mode
   - [ ] Test with existing WORK_STREAM.md
   - [ ] Test with new WORK_STREAM.md

2. **Test helper functions**:
   - [ ] Test `_extract_items_from_wbs()`
   - [ ] Test `_extract_items_from_plan()`
   - [ ] Test `_extract_items_from_research()`
   - [ ] Test `_merge_items_to_work_stream()`

### Integration Tests

1. **Test full flow**:
   ```bash
   # Create test fragments
   # Create test task files (some invalid)
   # Run incorporate
   # Verify validation blocks invalid tasks
   # Verify valid tasks merged
   # Verify auto-sync works
   ```

---

## Files to Create/Modify

### New Files

- None (all in existing files)

### Modified Files

- `src/thegent/cli_impl.py` - Add `incorporate_impl()` function and helpers

---

## Success Criteria

- ✅ `incorporate_impl()` function implemented
- ✅ Task validation works correctly
- ✅ Auto-sync to WORK_STREAM.md works
- ✅ Error reporting is clear
- ✅ All tests pass

---

**Status**: Ready for Implementation
**Priority**: Medium (part of Phase 4)
