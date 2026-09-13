<DONE>
# Friction Detection Automation

> **Status**: ✅ Implemented
> **Date**: 2026-02-18
> **Purpose**: Ensure automatic detection and resolution of UX/DX/AX friction

---

## Overview

Friction detection is now **fully automated** via hooks. The system automatically detects common friction patterns and alerts agents to fix them immediately.

## Implementation

### 1. Friction Detector Script

**Location**: `scripts/friction_detector.py`

Detects friction patterns in:

- Code files (Write/Edit operations)
- Command strings (Execute operations)
- Documentation

**Patterns Detected**:

- `cd &&` → CLI should work from any directory
- `2>&1` → CLI should handle stderr automatically
- `head -n` → CLI should have `--limit` option
- `grep -v` → CLI should filter noise automatically
- Bash loops wrapping commands → CLI should have native loop support
- Multiple sequential `read_file()` calls → Use `batch_read_files()`
- Manual path resolution → Use `normalize_path()` helper

### 2. Friction Detector Hook

**Location**: `hooks/friction-detector.sh`

**Event**: `PostToolUse` (Write|Edit|Execute)

**Behavior**:

- Runs automatically after every Write/Edit/Execute operation
- Scans content for friction patterns
- Outputs advisory warnings (non-blocking)
- Shows priority (P1/P2), category (UX/DX/AX), and solution

**Integration**: Added to `posttool-dispatcher.sh` hook array

### 3. Workflow Integration

**Agent Behavior**:

1. Hook runs automatically and detects friction
2. Agent sees friction warnings in hook output
3. Agent fixes friction immediately or delegates to `thegent free --bg`
4. Agent logs friction using `log_friction()` if needed

**CLAUDE.md Updates**:

- Added explicit reminder to act on hook-detected friction
- Updated friction detection checklist
- Emphasized "don't wait for user to ask"

## Usage

### Manual Detection

```bash
# Scan a file
python3 scripts/friction_detector.py --file path/to/file.py

# Scan a command
python3 scripts/friction_detector.py --command "cd /path && cmd 2>&1 | head -100"

# JSON output
python3 scripts/friction_detector.py --file file.py --format json
```

### Automatic Detection

The hook runs automatically. To test:

```bash
# Edit a file with friction patterns
echo 'cd /path && cmd 2>&1 | head -100' > test.sh

# Hook will detect and warn
```

## Example Output

```
FRICTION DETECTED in command:
  [P1] UX: verbosity - Commands requiring 'cd &&' instead of working from any directory
  [P1] UX: error_handling - Commands requiring '2>&1' for error handling
  [P1] UX: pagination - Commands requiring 'head' for output limiting
```

## Next Steps

1. ✅ Friction detector script created
2. ✅ Hook integration complete
3. ✅ CLAUDE.md updated with reminders
4. ⏳ Monitor hook output for friction patterns
5. ⏳ Fix friction automatically when detected
6. ⏳ Log friction points for tracking

## Success Criteria

- [x] Hook detects friction patterns automatically
- [x] Hook outputs actionable warnings
- [x] Agents are reminded to act on friction
- [ ] Agents fix friction automatically (behavioral change)
- [ ] Friction points logged for tracking
- [ ] CLI UX improvements reduce friction patterns over time
