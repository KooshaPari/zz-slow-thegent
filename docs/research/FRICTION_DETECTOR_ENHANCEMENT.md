<DONE>
# Friction Detector Enhancement - Comprehensive Pattern Detection

> **Date**: 2026-02-18
> **Status**: ✅ Enhanced
> **Purpose**: Robust detection of friction, optimizations, and process inefficiencies

---

## Enhancement Summary

Expanded friction detector from **7 patterns** to **40+ patterns** covering:

### Categories

1. **CLI/UX Verbosity** (6 patterns)
   - `cd &&`, `2>&1`, `head`, `tail`, `grep -v`, `sed/awk`

2. **Process/Agent Workflow** (7 patterns)
   - Bash loops, polling, sequential calls, manual coordination
   - Busy loops, work claiming, session management

3. **File Operations** (5 patterns)
   - Multiple reads, full reads, repeated reads
   - Manual path resolution, `ls -l` in root

4. **Code Quality** (5 patterns)
   - Custom retry/cache/file-watching instead of libraries
   - Manual HTTP, print debugging

5. **Agent Process Optimization** (6 patterns)
   - Sequential exploration, reading many files
   - Manual context management, not delegating
   - Finishing when work ongoing, manual coordination

6. **Performance** (5 patterns)
   - Subprocess overhead, multiple calls
   - Synchronous HTTP, inefficient string ops
   - Regex in loops

7. **Error Handling** (3 patterns)
   - Bare except, silent failures, missing context

8. **Type Safety** (2 patterns)
   - Missing type hints, Any usage

9. **Documentation** (2 patterns)
   - Missing docstrings, TODO in code

## New Features

### Multi-Line Pattern Detection

- Detects patterns spanning multiple lines
- Handles sequential operations across lines

### Category Grouping

- Output grouped by category (UX, DX, AX)
- Sorted by priority (P1 first)

### Filtering Options

- `--category ux|dx|ax|all` - Filter by category
- `--priority P1|P2|all` - Filter by priority

### Deduplication

- Removes duplicate findings at same location
- Prevents false positives

## Pattern Examples

### Process/Agent Workflow Patterns

**Sequential Agent Calls**:

```python
thegent free "Task 1"
thegent free "Task 2"
thegent free "Task 3"
```

→ **Detected**: Should use `thegent bg` for parallel execution

**While Loop Polling**:

```bash
while true; do
  sleep 5
  thegent ps
done
```

→ **Detected**: Should use `thegent plan wait-next`

**Reading Many Files**:

```python
read_file("file1.py")
read_file("file2.py")
read_file("file3.py")
read_file("file4.py")
```

→ **Detected**: Should delegate or use `batch_read_files()`

### Performance Patterns

**Subprocess Overhead**:

```python
subprocess.run("cmd", shell=True)
```

→ **Detected**: Use `shell=False` or FastSubprocess helper

**Regex in Loop**:

```python
for line in lines:
    re.search(pattern, line)
```

→ **Detected**: Compile regex once before loop

## Usage

```bash
# Scan file
python3 scripts/friction_detector.py --file path/to/file.py

# Scan command
python3 scripts/friction_detector.py --command "cd /path && cmd 2>&1 | head -100"

# Filter by category
python3 scripts/friction_detector.py --file file.py --category dx

# Filter by priority
python3 scripts/friction_detector.py --file file.py --priority P1

# JSON output
python3 scripts/friction_detector.py --file file.py --format json
```

## Integration

- ✅ Hook integration: `hooks/friction-detector.sh`
- ✅ Runs automatically on Write/Edit/Execute
- ✅ Outputs advisory warnings
- ✅ Agents must act on P1 friction immediately

## Impact

**Before**: 7 patterns detected
**After**: 40+ patterns detected

**Coverage**:

- CLI/UX friction ✅
- Process inefficiencies ✅
- Agent workflow optimizations ✅
- Performance bottlenecks ✅
- Code quality anti-patterns ✅
- Error handling issues ✅
- Type safety gaps ✅

## Next Steps

1. Monitor hook output for new patterns
2. Add more patterns as needed
3. Track friction reduction over time
4. Measure agent response to warnings
