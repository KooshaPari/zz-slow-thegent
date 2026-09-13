<DONE>
# Friction Detection Automation - Complete Solution

> **Date**: 2026-02-18
> **Status**: ✅ Implemented and Active
> **Purpose**: Ensure automatic detection and resolution of UX/DX/AX friction

---

## Problem Statement

Agents were not automatically detecting and fixing CLI/UX friction patterns (like `cd &&`, `2>&1`, `head`) even though `CLAUDE.md` explicitly mandates this behavior.

## Solution: Multi-Layer Automation

### Layer 1: Automated Hook Detection ✅

**Implementation**:

- `scripts/friction_detector.py` - Detects friction patterns in code/commands
- `hooks/friction-detector.sh` - Runs automatically on every Write/Edit/Execute
- Integrated into `hooks/posttool-dispatcher.sh` hook array

**How It Works**:

1. Hook runs automatically after every tool operation
2. Scans content for friction patterns
3. Outputs advisory warnings with priority, category, and solution
4. Agent sees warnings and must act on them

**Patterns Detected**:

- ✅ `cd &&` → CLI should work from any directory
- ✅ `2>&1` → CLI should handle stderr automatically
- ✅ `head -n` → CLI should have `--limit` option
- ✅ `grep -v` → CLI should filter noise automatically
- ✅ Bash loops wrapping commands → CLI should have native loop support
- ✅ Multiple sequential `read_file()` calls → Use `batch_read_files()`
- ✅ Manual path resolution → Use `normalize_path()` helper

### Layer 2: Updated Instructions ✅

**CLAUDE.md Updates**:

- Added explicit reminder: "Hook detected friction? → Fix immediately or delegate"
- Updated friction detection checklist with hook integration
- Emphasized "don't wait for user to ask" behavior

### Layer 3: Behavioral Reminders ✅

**Workflow Integration**:

- Hook output is visible to agent
- Agent must act on P1 friction immediately
- Agent can delegate P2 friction to `thegent free --bg`
- Friction logged to `FRICTION_LOG.md` for tracking

## Testing

```bash
# Test friction detection
python3 scripts/friction_detector.py --command "cd /path && thegent ps --format json 2>&1 | head -100"

# Output:
# Found 3 friction pattern(s):
#   [P1] UX: verbosity - cd && pattern
#   [P1] UX: error_handling - 2>&1 pattern
#   [P1] UX: pagination - head pattern
```

## How Agents Will Behave Going Forward

1. **Hook runs automatically** → Detects friction patterns
2. **Agent sees warnings** → Must act on them
3. **Agent fixes friction** → Immediately or delegates
4. **Friction logged** → For tracking and improvement

## Success Metrics

- [x] Hook detects friction automatically
- [x] Hook outputs actionable warnings
- [x] Instructions updated with reminders
- [ ] Agents fix friction automatically (behavioral - to be measured)
- [ ] Friction patterns decrease over time

## Files Created/Modified

1. ✅ `scripts/friction_detector.py` - Pattern detection engine
2. ✅ `hooks/friction-detector.sh` - Hook integration
3. ✅ `hooks/posttool-dispatcher.sh` - Added friction-detector to hook array
4. ✅ `CLAUDE.md` - Updated with hook-aware friction detection
5. ✅ `docs/research/FRICTION_DETECTION_AUTOMATION.md` - Documentation

## Next Steps

1. Monitor hook output for friction detection
2. Measure agent response to friction warnings
3. Track friction pattern reduction over time
4. Add more friction patterns as needed
