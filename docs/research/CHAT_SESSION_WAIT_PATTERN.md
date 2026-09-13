<DONE>
# Chat Session Wait Pattern

**Date:** 2026-02-17
**Issue:** Chat sessions terminating instead of waiting for next notification

---

## Problem

- Chat session finishes when work is ongoing
- Background processes don't keep chat session alive
- Need proper blocking wait to keep session active

---

## Solution: Proper Wait Commands

### Pattern 1: Block Until Work Available (RECOMMENDED)

**Command:** `thegent plan wait-next --timeout 0 --poll 10`

**Behavior:**

- Blocks indefinitely (keeps chat session alive)
- Polls every 10 seconds for work
- Returns when work becomes available
- Keeps session active between work items

**Use Case:** When idle, waiting for next work item

### Pattern 2: Continuous Work Loop

**Command:** `thegent plan loop --max 1000 --sleep 30`

**Behavior:**

- Processes work items continuously
- Sleeps 30s between iterations
- Keeps session active while processing
- Stops after max iterations or no work

**Use Case:** Continuous autonomous work processing

### Pattern 3: Wait for Specific Session

**Command:** `thegent wait <session_id> --timeout 300`

**Behavior:**

- Blocks until specific session completes
- Times out after specified seconds
- Keeps session active while waiting

**Use Case:** Waiting for specific agent to complete

---

## Implementation Status

✅ **`wait_next_impl()`** - Implemented blocking wait function
✅ **Wait Loop** - Background process running
✅ **CLAUDE.md Updated** - Instructions for proper wait patterns

---

## Key Points

1. **Don't finish conversation** when work is ongoing
2. **Use blocking wait commands** to keep session active
3. **Run wait in foreground** (not background) to block chat
4. **Poll at reasonable intervals** (10-30s) to avoid busy-waiting

---

**Status:** ✅ **WAIT PATTERNS DOCUMENTED AND IMPLEMENTED**
