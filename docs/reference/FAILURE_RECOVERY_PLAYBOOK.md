# Failure Recovery Playbook

**Status:** Active | **Last Updated:** 2026-02-18 | **Scope:** Multi-agent coordination failures

---

## Overview

This playbook defines recovery procedures for common failure scenarios in multi-level coordination. Each scenario includes detection, root cause analysis, and step-by-step recovery with fallback options.

### Quick Symptom Matcher

| Symptom                                           | Root Cause                       | Playbook Section |
| ------------------------------------------------- | -------------------------------- | ---------------- |
| Task claimed but no progress for 10+ min          | Agent crash/hang                 | FRP-1            |
| Two agents claim same task                        | Race condition in WORK_STREAM.md | FRP-2            |
| Task A depends on B, B depends on A               | Circular dependency              | FRP-3            |
| Multiple agents editing same file, merge conflict | Concurrent file edits            | FRP-4            |
| Task marked complete, but downstream finds bug    | Incomplete testing/QA            | FRP-5            |
| Task estimate 5m, now 45+ min running             | SLO breach / scope creep         | FRP-6            |
| CLAIMED and PENDING both show same task           | Git conflict in WORK_STREAM.md   | FRP-7            |
| Blocker waiting 30+ min, upstream task stuck      | Dependency SLO breach            | FRP-8            |
| Agent reports file already exists / can't create  | Permission or file locking issue | FRP-9            |
| All agents idle, no work items available          | Work stream depletion            | FRP-10           |

---

## FRP-1: Agent Crash/Timeout During Execution

**Symptom:** Task in CLAIMED section, agent not responding, no status update for 10+ minutes.

**Detection:**

```bash
# Check for stale sessions (no update in 10 min)
thegent ps | grep -v updated
# or check WORK_STREAM.md for old timestamps
grep "IN_PROGRESS" docs/reference/WORK_STREAM.md | awk -F'|' '{print $3}' | while read ts; do
  age=$(($(date +%s) - $(date -d "$ts" +%s)))
  if [ $age -gt 600 ]; then echo "STALE: $ts ($age seconds)"; fi
done
```

### Recovery Steps

**Option A: Graceful Recovery (Preferred)**

1. **Attempt Soft Shutdown** (30-second timeout)

   ```bash
   thegent wait {session_id} --timeout 30
   ```

   - If agent responds, it can finish or gracefully abort
   - Check logs to understand what happened:
     ```bash
     tail -100 .process-compose/logs/{session_id}.log
     ```

2. **If Agent Responds:** Let it finish or ask to abort

   ```bash
   # Send message to agent (if TeamCreate used)
   SendMessage type=message recipient="{agent-name}" \
     content="Task running long. Finish if close, else abort and we'll restart."
   ```

3. **Move Task Back to PENDING**
   - Remove from CLAIMED section in WORK_STREAM.md
   - Mark original row as PENDING (revert from CLAIMED)
   - Add note: "Released due to timeout, can be reclaimed"

4. **Commit & Push**
   ```bash
   git add docs/reference/WORK_STREAM.md docs/reference/AGENTS_ACTIVE.md
   git commit -m "Release TGNT-P6.1 due to timeout (stale for 15 min)"
   git push origin main
   ```

**Option B: Force Terminate (If Soft Timeout Fails)**

1. **Force Kill Session** (immediate, no cleanup)

   ```bash
   thegent kill {session_id} --force
   ```

2. **Check for Partial Files**

   ```bash
   # Look for incomplete edits (e.g., .swp, .tmp files)
   git status | grep -E "\.swp|\.tmp|\.bak"
   # If found, clean up:
   rm -f {incomplete-files}
   ```

3. **Abort Any Pending Git Operations**

   ```bash
   # Check for dangling lock files
   ls -la .git/ | grep lock
   # If found, remove (only if process is truly dead)
   rm -f .git/index.lock
   ```

4. **Move Task Back to PENDING** (same as Option A, step 3)

5. **Update AGENTS_ACTIVE.md**

   ```markdown
   | agent-id | ... | ERROR | TGNT-P6.1 | -- | 2026-02-18T14:30:00Z | 2026-02-18T15:45:00Z | 75 min | Force killed after timeout |
   ```

6. **Post-Mortem Analysis**
   - Review task estimate vs. actual
   - Was task scope too large? (should be split)
   - Was task estimate too aggressive? (should be revised)
   - Add note to task for next attempt:
     ```markdown
     | TGNT-P6.1 | ... | ~8min | PENDING | Notes: Consider splitting or increasing estimate |
     ```

### Preventive Measures

1. **Shorter Estimates:** Tasks estimated > 20 min should be split into smaller tasks
2. **Health Checks:** Dashboard auto-alerts if task > 150% of estimate
3. **Heartbeat:** L2 teammates send status update every 5-10 min for long tasks
4. **SLO Timeout:** Automatic timeout at 2x estimate (with warning at 1.5x)

---

## FRP-2: Duplicate Task Claims (Race Condition)

**Symptom:** Two agents claim the same task (both update WORK_STREAM.md simultaneously).

**Detection:**

```bash
# Check for duplicate task in CLAIMED
grep "TGNT-P6.1" docs/reference/WORK_STREAM.md | wc -l
# If > 1, we have a duplicate

# Or check git log for conflicting commits
git log --oneline -20 docs/reference/WORK_STREAM.md
# Look for commits around same time updating same task
```

### Recovery Steps

**Step 1: Identify Conflicting Agents**

```bash
# Get both commits
git log --all --oneline -- docs/reference/WORK_STREAM.md | head -5
# Compare them
git show {commit1}:docs/reference/WORK_STREAM.md | grep TGNT-P6.1
git show {commit2}:docs/reference/WORK_STREAM.md | grep TGNT-P6.1
```

**Step 2: Determine Which Agent Actually Started Work**

- Check file timestamps for actual changes (use git diff)
- Check AGENTS_ACTIVE.md or session logs for actual start time
- Contact both agents: "Only one can work on this. Who started first?"

**Step 3: Assign Task to Winner, Release Loser**

**If Agent 1 wins:**

```bash
# In WORK_STREAM.md CLAIMED section, keep Agent 1 entry, remove Agent 2
# Commit with message:
git commit -m "Resolve race condition on TGNT-P6.1: Agent 1 wins (started first)"

# Notify Agent 2:
SendMessage type=message recipient="{agent-2}" \
  content="Race condition resolved. Task TGNT-P6.1 goes to agent-1. \
Next available: TGNT-P6.6 (ready now). Claim it?"
```

**Step 4: Lock WORK_STREAM.md During High Contention**

If race conditions are frequent:

```bash
# Add atomic locking mechanism (Git pre-commit hook)
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
if git diff --cached | grep -q "CLAIMED\|COMPLETED"; then
  # Check if WORK_STREAM.md was modified
  if git diff --cached --name-only | grep -q WORK_STREAM.md; then
    # Verify no duplicate claims
    if grep "^| TGNT" docs/reference/WORK_STREAM.md | cut -d'|' -f2 | sort | uniq -d | grep -q .; then
      echo "ERROR: Duplicate task ID in WORK_STREAM.md"
      exit 1
    fi
  fi
fi
EOF
chmod +x .git/hooks/pre-commit
```

**Step 5: Implement Mutex for CLAIMED Updates**

Use file locking to prevent concurrent updates:

```bash
# Wrap WORK_STREAM.md updates with flock
update_work_stream() {
  (
    flock -x 200 || exit 1
    # Edit WORK_STREAM.md here
    {command}
    git add docs/reference/WORK_STREAM.md
    git commit -m "..."
  ) 200>>/tmp/work_stream.lock
}
```

---

## FRP-3: Circular Dependencies

**Symptom:** Task A depends on B, task B depends on A. Both PENDING, nothing can start.

**Detection:**

```bash
# Build dependency graph
grep "Depends On" docs/reference/WORK_STREAM.md | while read -r line; do
  task=$(echo "$line" | cut -d'|' -f2)
  deps=$(echo "$line" | cut -d'|' -f4)
  echo "$task -> $deps"
done > /tmp/deps.txt

# Check for cycles (using DFS)
python3 << 'EOF'
import re
deps = {}
with open('/tmp/deps.txt') as f:
    for line in f:
        if '->' in line:
            task, dep = line.strip().split('->')
            deps[task.strip()] = [d.strip() for d in dep.split(',')]

def find_cycle(node, visited, rec_stack, parent):
    visited.add(node)
    rec_stack.add(node)
    if node in deps:
        for neighbor in deps[node]:
            if neighbor not in visited:
                path = find_cycle(neighbor, visited, rec_stack, node)
                if path:
                    return [node] + path
            elif neighbor in rec_stack:
                return [node, neighbor]
    rec_stack.remove(node)
    return None

for task in deps:
    path = find_cycle(task, set(), set(), None)
    if path:
        print(f"CYCLE DETECTED: {' -> '.join(path)}")
EOF
```

### Recovery Steps

**Step 1: Understand Dependency Reason**

```bash
# Read the task descriptions and Depends On column
grep -A1 "TGNT-P6.1\|TGNT-P6.2" docs/reference/WORK_STREAM.md

# Ask: Why does A depend on B? Why does B depend on A?
# Options:
#   - Misunderstood requirement (one dependency is wrong)
#   - Circular design (need redesign)
#   - Can be parallelized (remove dependency)
```

**Step 2: Break Cycle by Removing Weakest Link**

Identify which dependency is weakest:

```bash
# Ask questions:
# 1. Can task B be done without A's output? (if yes, remove A→B dependency)
# 2. Can task A be done without B's output? (if yes, remove B→A dependency)
# 3. Are A and B doing the same thing? (if yes, merge them)
```

**Example: A=Auth, B=API depends on Auth**

Original:

- TGNT-P1: Auth system (depends on: none)
- TGNT-P2: API endpoints (depends on: TGNT-P1)
- But TGNT-P1 also depends on TGNT-P2 (API middleware?)

Resolution: Split TGNT-P1 into two tasks:

- TGNT-P1a: Auth core (no deps) → can start now
- TGNT-P1b: Auth API integration (depends on TGNT-P2) → can start after P2

**Step 3: Update WORK_STREAM.md**

```markdown
| TGNT-P1a | Auth core | ... | -- | ~5min | PENDING |
| TGNT-P2 | API endpoints | ... | TGNT-P1a | ~10min | PENDING |
| TGNT-P1b | Auth API integration | ... | TGNT-P2 | ~5min | PENDING |
```

**Step 4: Reorder Tasks**

Now that cycle is broken, reorder to maximize parallelism:

```
TGNT-P1a (start now) → TGNT-P2 (start after P1a) + TGNT-P1b (wait for P2)
```

**Step 5: Commit & Escalate**

```bash
git commit -m "Break cycle: split TGNT-P1 into P1a (core) and P1b (integration)"

# Notify L1:
SendMessage type=message recipient="coordinator" \
  content="Circular dependency found: P1 <-> P2. \
Resolved by splitting P1 into P1a (core) and P1b (integration). \
Updated WORK_STREAM.md. Ready to proceed."
```

---

## FRP-4: File Conflict (Multiple Agents Editing Same File)

**Symptom:** Git merge conflict after agents edit same file.

**Detection:**

```bash
# Check git status
git status | grep "both modified"

# Or check for unmerged paths
git ls-files --unmerged
```

### Recovery Steps

**Step 1: Identify Conflicting Edits**

```bash
# Show conflict markers
git diff {filename} | head -50

# Or use mergetool
git mergetool {filename}
```

**Step 2: Resolve Manually or Auto-Merge**

**Option A: Manual Merge** (for logic conflicts)

```bash
# Edit file, remove conflict markers
nano {filename}
# Fix logic by taking both versions or choosing best

# Mark as resolved
git add {filename}
git commit -m "Resolve conflict: {filename} (took {agent-1} logic for {section})"
```

**Option B: Rebase & Replay**

If conflict is just ordering/format:

```bash
# Rebase agent B's changes on top of agent A's
git rebase -i {base-commit}

# This replays agent B's changes after agent A's
# May auto-resolve if changes don't overlap
```

**Step 3: Verify Merged File**

```bash
# Make sure merged file is valid
# For code: lint + tests
ruff check {filename}
pytest tests/test_{filename}.py

# For docs: check formatting
# For config: validate schema
```

**Step 4: Update Task Status**

- Agent A: Mark task COMPLETED (already done)
- Agent B: Restart task (was doing same work)
  ```markdown
  | TGNT-P6.2 | Agent B | 2026-02-18T14:30:00Z | 2026-02-18T15:00:00Z | CONFLICT_RESOLVED |
  | TGNT-P6.2 | Agent B | 2026-02-18T15:05:00Z | -- | IN_PROGRESS (restart) |
  ```

**Step 5: Prevent Future Conflicts**

Implement task scoping to prevent overlaps:

```markdown
# Best: Different agents, different files

Agent A: auth.py
Agent B: api.py

# OK: Same file, different functions

Agent A: auth.py (classes UserAuth, TokenAuth)
Agent B: auth.py (functions validate_token, refresh_token)

# BAD: Same function, both agents editing

Agent A & B: auth.py (function validate_token) ❌
```

---

## FRP-5: Regression After Completion

**Symptom:** Task marked COMPLETED, but downstream task finds bug or regression.

**Detection:**

```bash
# Downstream task reports error
# E.g., TGNT-P6.2 reports: "TGNT-P6.1 broke X"

# Verify by running tests
pytest tests/test_git_index.py -v

# Check git blame to find introducing commit
git blame {filename} | grep {broken_line}
```

### Recovery Steps

**Step 1: Confirm Bug**

```bash
# Run failing test
pytest tests/test_git_index.py::test_atomic_write -v

# Get stack trace
# Ask upstream agent to confirm: "Is this your bug?"
```

**Step 2: Reopen Task**

```markdown
# In WORK_STREAM.md, move from COMPLETED back to IN_PROGRESS:

| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | -- | IN_PROGRESS (reopened: regression in TGNT-P6.2) |
```

**Step 3: Root Cause Analysis**

Ask agent: "What went wrong?"

- Incomplete testing? (test didn't catch edge case)
- Partial implementation? (feature flag not complete)
- Assumption error? (didn't test on all platforms)

**Step 4: Fix and Re-Test**

Agent fixes the issue:

```bash
# Make fix
nano {file}

# Test locally first
pytest tests/ -v

# Then push
git add {file}
git commit -m "Fix TGNT-P6.1 regression: atomic write race condition"
git push origin main
```

**Step 5: Re-Mark as COMPLETED**

```markdown
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | 2026-02-18T16:15:00Z | COMPLETED (with fix) |
```

**Step 6: Post-Mortem**

- Why wasn't this caught in initial QA?
- Update test coverage
- Update estimate for similar future tasks

---

## FRP-6: SLO Breach (Task Running 10x Estimate)

**Symptom:** Task estimated ~8min, now running 80+ min (10x over).

**Detection:**

```bash
# Check elapsed time vs estimate
age=$(($(date +%s) - $(date -d "2026-02-18T14:30:00Z" +%s)))
estimate_seconds=$((8 * 60))
if [ $age -gt $((estimate_seconds * 2)) ]; then
  echo "SLO BREACH: Task running $((age / 60)) min vs $((estimate_seconds / 60)) min estimate"
fi
```

### Recovery Steps

**Step 1: Determine Root Cause**

Send message to agent:

```
"TGNT-P6.1 is running long (80m vs 8m estimate).
What's blocking you?
A) Task is more complex than expected
B) Waiting for dependency to unblock
C) Environment/tooling issues
D) Need help/pair programming"
```

**Step 2: Based on Response:**

**If A (Task More Complex):**

- Split task into smaller subtasks
- Complete current subtask, mark as partial completion
- Reassess scope of remaining work
- Example:
  ```markdown
  | TGNT-P6.1 | ... | ~8min | COMPLETED (scope: atomic write only, 40m) |
  | TGNT-P6.1b | ... | ~15min | PENDING (scope: cache coherency, blocked on tooling) |
  ```

**If B (Waiting for Dependency):**

- Escalate dependency blocker (see FRP-8)
- If dependency is far away, consider different approach
- Can agent do other work in parallel?

**If C (Tooling Issues):**

- Provide support, assign troubleshooting agent
- Install missing tools, fix environment
- Restart task once fixed

**If D (Need Help):**

- Pair agent with specialist
- Or bring in second agent to handle sub-part
- Update task to show collaboration

**Step 3: Update Forecast**

```markdown
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | -- | IN_PROGRESS (revised est: 45m vs original 8m, cause: GIT_INDEX complexity higher than expected) |
```

**Step 4: Adjust Future Estimates**

Document lessons learned:

```markdown
# Post-Task Analysis

**Task:** TGNT-P6.1 (GIT_INDEX_FILE management)
**Original Estimate:** 8 min
**Actual Duration:** 45 min (5.6x over)
**Root Causes:**

- GIT_INDEX_FILE semantics more complex than anticipated
- Edge cases in concurrent access not covered by initial design
- Testing + debugging took longer than expected

**Recommendations for Similar Tasks:**

- Estimate should be 20-30 min minimum for git-level operations
- Build in 50% buffer for git testing (very environment-dependent)
- Consider pair programming for git operations (high risk of subtle bugs)

**Estimate Adjustment:** +300% for similar git-level tasks going forward
```

**Step 5: Monitor for Pattern**

If multiple tasks are overshooting:

- Team is overcommitting
- Complexity underestimated
- Consider reducing sprint scope
- Invest in upfront design/architecture

---

## FRP-7: Git Conflict in WORK_STREAM.md

**Symptom:** WORK_STREAM.md shows same task in BOTH CLAIMED and PENDING sections (git merge conflict).

**Detection:**

```bash
# Check for conflict markers
grep -A2 "^<<<<<<< HEAD" docs/reference/WORK_STREAM.md

# Or check git status
git status docs/reference/WORK_STREAM.md
```

### Recovery Steps

**Step 1: Identify Conflicting Versions**

```bash
# Show both versions
git show :1:docs/reference/WORK_STREAM.md | grep TGNT-P6.1  # base
git show :2:docs/reference/WORK_STREAM.md | grep TGNT-P6.1  # ours
git show :3:docs/reference/WORK_STREAM.md | grep TGNT-P6.1  # theirs
```

**Step 2: Merge Manually**

```bash
# Open file in editor
nano docs/reference/WORK_STREAM.md

# Remove conflict markers (<<<<<<, ======, >>>>>>)
# Choose correct version:
# - If task is actively being worked on: keep CLAIMED entry
# - If task just completed: keep COMPLETED entry
# - If both CLAIMED and COMPLETED: check timestamps to see which is newer

# Example:
# <<<<<<< HEAD (ours: we say CLAIMED)
# | TGNT-P6.1 | agent-1 | 2026-02-18T14:30Z | IN_PROGRESS |
# =======
# (theirs: they say COMPLETED)
# | TGNT-P6.1 | agent-1 | 2026-02-18T14:30Z | 2026-02-18T15:00Z | COMPLETED (22m) |
# >>>>>>>

# Decision: Accept COMPLETED (it's newer, more recent status)
# Delete conflict markers, keep COMPLETED row
```

**Step 3: Verify No Duplicates**

```bash
# Count occurrences of each task
awk -F'|' '{print $2}' docs/reference/WORK_STREAM.md | sort | uniq -d
# Should output nothing (no duplicates)
```

**Step 4: Resolve Conflict**

```bash
git add docs/reference/WORK_STREAM.md
git commit -m "Resolve conflict in WORK_STREAM.md: TGNT-P6.1 completed (took more recent status)"
```

**Step 5: Implement Prevention**

Use file locking (see FRP-2, Step 5) to prevent concurrent edits.

---

## FRP-8: Blocker SLO Breach (Task Waiting 30+ Minutes)

**Symptom:** Task blocked waiting for dependency, dependency is not progressing (stuck).

**Detection:**

```bash
# Find blocked tasks waiting > 15 min
grep "BLOCKED" docs/reference/WORK_STREAM.md | while read task; do
  blocked_time=$(echo "$task" | awk -F'|' '{print $(NF-1)}')
  if [ $((blocked_time * 60)) -gt 900 ]; then
    echo "CRITICAL BLOCKER: $task"
  fi
done
```

### Recovery Steps

**Step 1: Check Dependency Status**

```bash
# Is dependency PENDING, CLAIMED, or IN_PROGRESS?
grep "TGNT-P6.5" docs/reference/WORK_STREAM.md

# If PENDING: no one claimed it yet → escalate to L1 (prioritize)
# If CLAIMED: agent claimed but not started → ask agent why
# If IN_PROGRESS: check how long it's been running
```

**Step 2: Escalate to L1**

```
SendMessage type=message recipient="coordinator" \
  content="BLOCKER ALERT: TGNT-P6.7 waiting for TGNT-P6.5 for 30 min.
TGNT-P6.5 status: IN_PROGRESS for 45 min (estimate: 3 min).

Options:
1. Prioritize TGNT-P6.5 (accelerate or reassign)
2. De-prioritize TGNT-P6.7 (start other work)
3. Start TGNT-P6.7 in parallel (risky, may need rework)
4. Escalate TGNT-P6.5 SLO breach (see FRP-6)"
```

**Step 3: L1 Decision & Action**

- **If dependency too slow:** Move dependency to front, assign more agents
- **If dependency is blocked:** Resolve upstream blocker (recursive FRP-8)
- **If dependency is hard:** Split it, make part non-blocking
- **If downstream is non-critical:** De-prioritize, work on other tasks

**Step 4: Update Status**

```markdown
# In WORK_STREAM.md:

| TGNT-P6.7 | ... | BLOCKED | Notes: Escalated to L1 due to 30m wait on TGNT-P6.5 |
```

**Step 5: Automated Escalation Policy**

Add rule to dashboard:

```
if (time_blocked > 15 min):
  severity = MEDIUM
  alert(L1): "Task X blocked for 15 min on Y"

if (time_blocked > 30 min):
  severity = CRITICAL
  auto_escalate_to_l1()
  highlight_on_dashboard(red)
```

---

## FRP-9: Permission/File Locking Issues

**Symptom:** Agent reports "Permission denied" or "File already in use" error.

**Detection:**

```bash
# Agent reports error in task
# Check git output
git status
# Error: could not create work tree dir '{file}': Permission denied

# Or check file locks
lsof {filename}
# Shows process holding file lock
```

### Recovery Steps

**Step 1: Identify File & Lock Holder**

```bash
# Check permissions
ls -la {filename}
stat {filename} | grep Access

# Check locks
lsof {filename}
# Shows PID and process name

# Check git locks
ls -la .git/ | grep lock
```

**Step 2: Determine Cause**

- **Permission:** File owned by different user, wrong mode (chmod)
- **Lock:** Another process or agent holding file (git, editor, build tool)
- **Shared Mount:** Network drive latency or stale NFS cache

**Step 3: Fix Appropriately**

**If Permission:**

```bash
# Fix file permissions
chmod 644 {filename}
# Or fix directory
chmod 755 {directory}

# Check git config
git config core.filemode
# If on Windows/network drive, might be False (ignore mode)
```

**If Lock:**

```bash
# Check what process is holding it
lsof {filename} | awk '{print $2}' | grep -v PID | xargs ps aux | grep
# Terminate if it's a stale process:
kill -9 {PID}

# Or check for git locks:
ls -la .git/ | grep lock
rm -f .git/index.lock .git/HEAD.lock
```

**If Network Drive:**

```bash
# Try remounting NFS with shorter timeouts:
sudo mount -o remount,timeo=10 {mount_point}
# Or restart the network device
```

**Step 4: Retry Task**

Once fixed:

```bash
git status  # Should show no errors
# Agent retries task
```

**Step 5: Log Issue**

```markdown
# In AGENTS_ACTIVE.md notes:

| agent-id | ... | ERROR | TGNT-P6.1 | -- | ... | File lock on git/index. Fixed with: rm .git/index.lock. Retrying now. |
```

---

## FRP-10: Work Stream Depletion (All Tasks Claimed/Complete)

**Symptom:** All PENDING tasks are now CLAIMED or COMPLETED, no more work available.

**Detection:**

```bash
# Check PENDING count
grep "| PENDING" docs/reference/WORK_STREAM.md | wc -l

# If 0:
echo "No more pending work"

# Check CLAIMED count
grep "| CLAIMED\|IN_PROGRESS" docs/reference/WORK_STREAM.md | wc -l

# If > 0, agents are still working
# If = 0, all work complete
```

### Recovery Steps

**Case A: Agents Still Working (CLAIMED/IN_PROGRESS > 0)**

```bash
# Wait for in-progress tasks to complete
# They'll move to COMPLETED section
# Then reassess

# Or, if good to proceed:
# - Start next phase
# - Create new work items for next phase
# - Assign to idle agents
```

**Case B: All Work Complete (No PENDING, No IN_PROGRESS)**

```
Phase Complete!

Actions:
1. Review COMPLETED section (100% items done)
2. Run quality gates (lint, tests, coverage)
3. Merge all work to main branch
4. Create next phase work items
5. Celebrate & document lessons learned
```

**Step 1: Verify All Complete**

```bash
# Count by status
echo "PENDING: $(grep '| PENDING' docs/reference/WORK_STREAM.md | wc -l)"
echo "CLAIMED: $(grep '| CLAIMED' docs/reference/WORK_STREAM.md | wc -l)"
echo "IN_PROGRESS: $(grep '| IN_PROGRESS' docs/reference/WORK_STREAM.md | wc -l)"
echo "COMPLETED: $(grep '| COMPLETED' docs/reference/WORK_STREAM.md | wc -l)"
echo "BLOCKED: $(grep '| BLOCKED' docs/reference/WORK_STREAM.md | wc -l)"

# All should be 0 except COMPLETED
```

**Step 2: Run Quality Gate**

```bash
make quality
# or
task quality

# Should pass: lint, tests, coverage
```

**Step 3: Review Phase Summary**

```markdown
# Create docs/reports/PHASE_6_COMPLETION_SUMMARY.md

## Phase 6: Git Parallelism - Complete

### Summary

- Started: 2026-02-18 14:00 UTC
- Completed: 2026-02-18 17:15 UTC
- Duration: 3h 15m
- Tasks: 12 items, all completed
- Success Rate: 100%
- Regressions: 0

### Metrics

- Avg Cycle Time: 18 min
- SLO Breaches: 1 (TGNT-P6.1, resolved)
- Blockers: 2 (all resolved)
- Quality: ✓ PASS (lint 0, tests 42/42, coverage 94%)

### Key Learnings

1. Git operations need 3-4x estimate buffer (too complex)
2. Atomic writes are hard to test (environment-dependent)
3. Pair programming worked well for tricky sections

### Next Phase: Phase 7 (Monitoring)

- Ready to start immediately
- No blocking dependencies
- First task: Dashboard design & implementation
```

**Step 4: Archive Completed Phase**

```bash
# Move completed task documentation to archive
mkdir -p docs/reference/archive/phase-6
cp docs/reference/WORK_STREAM.md docs/reference/archive/phase-6/
cp docs/reference/AGENTS_ACTIVE.md docs/reference/archive/phase-6/
cp docs/reports/PHASE_6_COMPLETION_SUMMARY.md docs/reference/archive/phase-6/

# Update WORK_STREAM.md for next phase
# Reset CLAIMED and COMPLETED sections (keep for history)
# Add new PENDING items for Phase 7
```

**Step 5: Create Next Phase**

```markdown
# In docs/reference/WORK_STREAM.md, add new section:

### thegent: Phase 7 (Monitoring - PENDING)

| ID        | Title                                             | Type    | Depends On | Effort | Status  |
| --------- | ------------------------------------------------- | ------- | ---------- | ------ | ------- |
| TGNT-P7.1 | Dashboard design (TUI mockup + hotkeys)           | feature | TGNT-P6    | ~15min | PENDING |
| TGNT-P7.2 | Dashboard MVP (parse WORK_STREAM, display header) | feature | TGNT-P7.1  | ~10min | PENDING |
| TGNT-P7.3 | Dashboard agents view (live updates)              | feature | TGNT-P7.2  | ~12min | PENDING |

...
```

**Step 6: Commit & Celebrate**

```bash
git add docs/reference/ docs/reports/
git commit -m "Complete Phase 6: Git Parallelism

All 12 tasks completed successfully.
- Cycle Time: 18 min avg
- Quality: 94% coverage, 0 regressions
- Key Learnings: Git ops need 3-4x estimate buffer

Ready to start Phase 7 (Monitoring)."

git push origin main

# Notify team:
SendMessage type=broadcast \
  content="🎉 Phase 6 Complete! All 12 Git Parallelism tasks done.
Quality gates passing: lint ✓, tests ✓, coverage ✓.
Ready to start Phase 7. Team refresh: 15 min break?"
```

---

## Recovery Decision Tree

```
Failure Detected
  │
  ├─ Agent not responding? ────→ FRP-1: Timeout
  ├─ Same task claimed twice? ──→ FRP-2: Race Condition
  ├─ Circular dependency? ──────→ FRP-3: Break Cycle
  ├─ File merge conflict? ──────→ FRP-4: File Conflict
  ├─ Bug after completion? ─────→ FRP-5: Regression
  ├─ Task running 2x+ estimate? → FRP-6: SLO Breach
  ├─ WORK_STREAM.md has duplicates? → FRP-7: Git Conflict
  ├─ Task blocked 30+ min? ─────→ FRP-8: Blocker SLO
  ├─ Permission error? ─────────→ FRP-9: File Lock
  └─ No more work? ─────────────→ FRP-10: Depletion
```

---

## Escalation Matrix

| Issue          | Severity | Initial Handler   | Escalation            | Time Limit |
| -------------- | -------- | ----------------- | --------------------- | ---------- |
| Agent timeout  | Medium   | L2 (Release task) | L1 (Investigate)      | 30 min     |
| Race condition | High     | L2 (Resolve)      | L1 (Lock WORK_STREAM) | 15 min     |
| Circular dep   | High     | L1 (Break cycle)  | Design review         | 20 min     |
| File conflict  | Medium   | L2 (Manual merge) | L1 (Rebase strategy)  | 10 min     |
| Regression     | High     | Upstream (Fix)    | L1 (Post-mortem)      | 30 min     |
| SLO breach     | High     | L2 (Escalate)     | L1 (Reprioritize)     | 15 min     |
| Blocker 30min  | Critical | L1 (Escalate)     | Team Lead (Override)  | 5 min      |
| File lock      | Low      | Agent (Retry)     | Ops (Fix perms)       | 10 min     |
| No more work   | Low      | L1 (Create more)  | --                    | N/A        |

---

## Version & Maintenance

| Version | Date       | Changes                          | Status |
| ------- | ---------- | -------------------------------- | ------ |
| 1.0     | 2026-02-18 | 10 FRP scenarios + decision tree | Active |

**Maintained By:** L1 Coordinator
**Review Frequency:** After each failure scenario encountered
**Next Review:** 2026-02-25
