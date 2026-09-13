# TUI Dashboard Design & Implementation

**Status:** Design Phase | **Last Updated:** 2026-02-18 | **Purpose:** Real-time coordination monitoring

---

## Overview

The TUI Dashboard provides L1 coordinators with real-time visibility into:

- Work stream status (PENDING, CLAIMED, COMPLETED)
- Active agents and their progress
- Blockers and dependencies
- Health metrics and SLO status
- Phase progress and predictions

### Design Principles

1. **Dense Information** - Show as much relevant data as possible in fixed screen space
2. **Actionable** - Highlight issues that require immediate action
3. **Auto-Refresh** - Update every 2-5 seconds without user intervention
4. **Keyboard-Driven** - Navigate and interact via hotkeys, no mouse required
5. **Color-Coded** - Use colors for status (green=good, yellow=warning, red=critical)
6. **ASCII-Safe** - Use Unicode box drawing, compatible with all terminals

---

## Full Dashboard Layout (160x40 minimum)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ KUSH COORDINATION MONITOR - 2026-02-18 15:30:45 UTC [PHASE 6: Git Parallel]│
├────────────────────────────────────────────────────────────────────────────┤
│ Status: ●ACTIVE │ PENDING: 12 │ CLAIMED: 3 │ COMPLETED: 5 │ BLOCKED: 2   │
├─────────────────────────────────────────────────┬──────────────────────────┤
│ ACTIVE AGENTS (3/5)                             │ PHASE 6: 45% COMPLETE   │
├────────────┬────────────┬─────────────────┬──────┼──────────────────────────┤
│ Agent      │ Task ID    │ Task Title      │ Elapsed      │ Est  │ Status    │
├────────────┼────────────┼─────────────────┼─────────────┼──────┼───────────┤
│ dev-1      │ TGNT-P6.1  │ GIT_INDEX ...   │ [████░░░] 15m│ 8m   │ On track │
│ tester     │ TGNT-P6.3  │ CAS ref update  │ [██░░░░░] 4m │ 5m   │ Early    │
│ integrator │ TGNT-P6.5  │ git status cmd  │ [███░░░░] 7m │ 3m   │ Over     │
├─────────────────────────────────────────────────┴──────────────────────────┤
│ BLOCKERS & DEPENDENCIES (2)                                                │
├────────────┬───────────────────────┬─────────────┬──────────────────────────┤
│ Blocked ID │ Blocked By (Ready?)   │ Time Waiting│ Action                   │
├────────────┼───────────────────────┼─────────────┼──────────────────────────┤
│ TGNT-P6.7  │ TGNT-P6.5 (2m left)   │ 5 min       │ Will auto-unblock soon  │
│ TGNT-P7.1  │ PHASE 6 (50%, 8m ETA) │ 18 min      │ Start parallel prep work?│
├────────────────────────────────────────────────────────────────────────────┤
│ NEXT AVAILABLE (top 5)                                                      │
├────────────┬─────────────────────────────┬──────┬────────┬──────────────────┤
│ Task ID    │ Title                       │ Est. │ Ready? │ Recommended Agent│
├────────────┼─────────────────────────────┼──────┼────────┼──────────────────┤
│ TGNT-P6.6  │ Performance benchmarks       │ 10m  │ ✓ YES  │ Idle agent-2     │
│ TGNT-P6.8  │ Documentation updates       │ 5m   │ ✓ YES  │ Idle agent-4     │
│ TGNT-P6.9  │ Integration test suite      │ 15m  │ ✗ WAIT │ Waiting: P6.7    │
├────────────────────────────────────────────────────────────────────────────┤
│ RECENT COMPLETIONS (last 30 min)                                           │
├────────────┬────────────────┬────────────────┬──────────────────────────────┤
│ Task ID    │ Agent          │ Completed      │ Duration │ Quality Check    │
├────────────┼────────────────┼────────────────┼──────────┼──────────────────┤
│ TGNT-P6.4  │ dev-2          │ 15:18 (12m ago)│ 22 min   │ ✓ PASS (tests)   │
│ TGNT-P6.2  │ implementation │ 15:05 (25m ago)│ 18 min   │ ✓ PASS (lint)    │
│ TGNT-P6.0  │ research       │ 14:55 (35m ago)│ 10 min   │ ✓ PASS (review)  │
├────────────────────────────────────────────────────────────────────────────┤
│ HEALTH METRICS                                                             │
├────────────────────────────────────────────────────────────────────────────┤
│ • Avg Task Duration:    18 min (est: 8 min, +125%) ⚠ SLO WATCH             │
│ • Cycle Time:           18 min (target: 15 min) ⚠ Trending upward         │
│ • Agent Utilization:    60% (3/5 active) ✓ Healthy                        │
│ • Success Rate:         100% (0 errors in last 10 tasks) ✓ Good           │
│ • Blocker Count:        2 (1 medium, 1 low) ✓ Acceptable                  │
│ • Phase ETA:            16:45 UTC (45 min from now)                        │
│ • Quality Gate:         ✓ PASS (lint, tests, coverage) – Ready to merge    │
├────────────────────────────────────────────────────────────────────────────┤
│ COMMANDS: [A]gents [W]orkstream [B]lockers [S]tats [H]elp [Q]uit • F5 refresh
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen Breakdowns

### 1. Header (Fixed Top)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ KUSH COORDINATION MONITOR - 2026-02-18 15:30:45 UTC [PHASE 6: Git Parallel]│
├────────────────────────────────────────────────────────────────────────────┤
│ Status: ●ACTIVE │ PENDING: 12 │ CLAIMED: 3 │ COMPLETED: 5 │ BLOCKED: 2   │
└────────────────────────────────────────────────────────────────────────────┘
```

**Components:**

- **Title**: Always visible, shows project and current phase
- **Timestamp**: UTC time, auto-updates every second
- **Status Indicator**: Colored dot (● green=healthy, ● yellow=warning, ● red=critical)
- **Quick Stats**: Count of items in each state

**Color Coding:**

- Green: All metrics healthy, no blockers
- Yellow: 1-2 warnings, SLO approaching, 1-2 blockers
- Red: Active failures, multiple blockers, critical SLO breaches

### 2. Active Agents Section (Scrollable)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACTIVE AGENTS (3/5)                                                         │
├────────────┬────────────┬─────────────────┬────────────┬──────┬──────────────┤
│ Agent      │ Task ID    │ Task Title      │ Elapsed    │ Est  │ Status       │
├────────────┼────────────┼─────────────────┼────────────┼──────┼──────────────┤
│ dev-1      │ TGNT-P6.1  │ GIT_INDEX...    │ [████░░░] │ 8m   │ ✓ On track   │
│            │            │                 │ 15m / 8m   │      │              │
├────────────┼────────────┼─────────────────┼────────────┼──────┼──────────────┤
│ tester     │ TGNT-P6.3  │ CAS ref update  │ [██░░░░░] │ 5m   │ ✓ Early      │
│            │            │                 │ 4m / 5m    │      │              │
├────────────┼────────────┼─────────────────┼────────────┼──────┼──────────────┤
│ integrator │ TGNT-P6.5  │ git status cmd  │ [███░░░░] │ 3m   │ ⚠ Over time  │
│            │            │                 │ 7m / 3m    │      │              │
└────────────┴────────────┴─────────────────┴────────────┴──────┴──────────────┘
```

**Columns:**

- **Agent**: Assigned agent name (e.g., `dev-1`, `tester`)
- **Task ID**: Work item identifier (e.g., `TGNT-P6.1`)
- **Task Title**: Shortened title (truncated to fit)
- **Elapsed**: Progress bar + time (current / estimate)
  - Green bar if on track (< 100%)
  - Yellow bar if approaching limit (100-150%)
  - Red bar if over (> 150%)
- **Est**: Original estimate (e.g., `8m`, `15min`)
- **Status**: Badge with emoji
  - ✓ On track (80-100%)
  - ✓ Early (< 80%)
  - ⚠ Over time (100-150%)
  - 🔴 SLO breach (> 150%)

**Scrolling:** If >10 agents, use arrow keys to scroll (max 10 visible)

### 3. Blockers Section (Always Visible)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ BLOCKERS & DEPENDENCIES (2)                                                  │
├───────────────┬──────────────────────────────┬──────────────┬────────────────┤
│ Blocked ID    │ Blocked By (Ready?)           │ Time Waiting │ Action         │
├───────────────┼──────────────────────────────┼──────────────┼────────────────┤
│ TGNT-P6.7     │ TGNT-P6.5 (✓ ready in 2m)    │ 5 min        │ Auto-unblock   │
│ TGNT-P7.1     │ PHASE 6 (█████░░░░░░ 50%, 8m)│ 18 min       │ Start prep?    │
└───────────────┴──────────────────────────────┴──────────────┴────────────────┘
```

**Columns:**

- **Blocked ID**: Task waiting for dependency
- **Blocked By**: Dependency status
  - ✓ ready (dependency will complete soon)
  - 🔴 stuck (dependency not progressing)
  - ⏳ not started (dependency not yet claimed)
  - Progress bar if in progress
- **Time Waiting**: How long blocked (triggers alert if > 15 min)
- **Action**: Suggested action for L1
  - "Auto-unblock soon" - dependency almost done
  - "Escalate to L1" - dependency stuck
  - "Start parallel prep?" - dependency will take time, start parallel work

**Colors:**

- Green: Blocker resolving soon (< 5 min)
- Yellow: Blocker moderate (5-15 min)
- Red: Blocker critical (> 15 min or stuck)

### 4. Next Available (Always Visible)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ NEXT AVAILABLE (top 5, sorted by priority & dependencies)                    │
├─────────────┬──────────────────────────────────┬──────┬────────┬─────────────┤
│ Task ID     │ Title                            │ Est. │ Ready? │ Rec. Agent  │
├─────────────┼──────────────────────────────────┼──────┼────────┼─────────────┤
│ TGNT-P6.6   │ Performance benchmarks           │ 10m  │ ✓ YES  │ idle agent-2│
│ TGNT-P6.8   │ Documentation updates           │ 5m   │ ✓ YES  │ idle agent-4│
│ TGNT-P6.9   │ Integration test suite          │ 15m  │ ✗ WAIT │ (need P6.7)│
│ TGNT-P6.10  │ Deployment validation           │ 8m   │ ✗ WAIT │ (need P6.9)│
│ TGNT-P7.1   │ Phase 7 kickoff planning        │ 8m   │ ✗ WAIT │ (Phase 6)   │
└─────────────┴──────────────────────────────────┴──────┴────────┴─────────────┘
```

**Columns:**

- **Task ID**: Unique identifier
- **Title**: Brief description
- **Est.**: Time estimate
- **Ready?**:
  - ✓ YES (all dependencies met, can start immediately)
  - ✗ WAIT (blocked by dependency or in-progress task)
- **Rec. Agent**: Recommended idle agent or reason for wait

**Usage:** L1 can press [C]laim to assign selected task to idle agent

### 5. Health Metrics (Always Visible)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ HEALTH METRICS                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ • Avg Task Duration:    18 min (est: 8 min, +125%) ⚠ SLO WATCH              │
│ • Cycle Time:           18 min (target: 15 min)    ⚠ Trending upward       │
│ • Agent Utilization:    60% (3/5 active)           ✓ Healthy                │
│ • Success Rate:         100% (last 10 tasks)       ✓ Good                   │
│ • Blocker Count:        2 (1 medium, 1 low)        ✓ Acceptable             │
│ • Phase ETA:            16:45 UTC (45 min)         ✓ On schedule             │
│ • Quality Gate:         ✓ PASS (lint, tests, cov.) – Ready to merge          │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Metrics Explained:**

| Metric            | Formula                               | Good     | Warning   | Critical |
| ----------------- | ------------------------------------- | -------- | --------- | -------- |
| Avg Task Duration | Sum(completed durations) / count      | 80-120%  | 120-150%  | >150%    |
| Cycle Time        | Median(CLAIMED → COMPLETED)           | <15 min  | 15-25 min | >25 min  |
| Agent Utilization | Active agents / Total agents          | >50%     | 30-50%    | <30%     |
| Success Rate      | (Total - Errors) / Total \* 100       | >95%     | 85-95%    | <85%     |
| Blocker Count     | Count(BLOCKED tasks)                  | <3       | 3-5       | >5       |
| Phase ETA         | Based on remaining tasks & cycle time | On time  | ±15%      | >±15%    |
| Quality Gate      | Lint + test + coverage status         | All PASS | 1 WARN    | 1+ FAIL  |

### 6. Footer (Fixed Bottom)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ COMMANDS: [A]gents [W]orkstream [B]lockers [S]tats [H]elp [Q]uit • F5 refresh
└──────────────────────────────────────────────────────────────────────────────┘
```

**Hotkeys:**

- `[A]` → Show extended agents view (more details, edit mode)
- `[W]` → Show full work stream (sortable by status, priority, team)
- `[B]` → Show detailed blocker analysis (manual resolution options)
- `[S]` → Show extended statistics (trends, predictions, performance)
- `[H]` → Show help (command reference)
- `[Q]` → Quit dashboard
- `F5` or `[R]` → Manual refresh (auto-refreshes every 2-5s)

---

## Extended Views (Press Key for More Detail)

### View A: Extended Agents

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EXTENDED AGENTS VIEW - Press [W] for workstream, [B] for blockers           │
├──────────────────────────────────────────────────────────────────────────────┤
│ • dev-1 (active: 15m on TGNT-P6.1)                                          │
│   Session ID: mcp-task-abc123                                               │
│   Task: Per-agent GIT_INDEX_FILE management (est: 8m, status: on-track)     │
│   Last Update: 14:45:23 UTC (45 seconds ago)                                │
│   Progress: [████░░░░░] 15m / 8m estimate                                   │
│   Notes: GIT_INDEX_FILE init/copy working. Now testing atomic writes.       │
│   Next Check: 14:50:00 (timeout if no update by 15:15:00)                   │
│                                                                              │
│ • tester (active: 4m on TGNT-P6.3)                                          │
│   Session ID: mcp-task-def456                                               │
│   Task: CAS ref update with backoff (est: 5m, status: early)                │
│   Last Update: 14:46:15 UTC (15 seconds ago)                                │
│   Progress: [██░░░░░░░] 4m / 5m estimate                                    │
│   Notes: CAS logic complete. Writing tests now.                             │
│   Next Check: 14:51:00 (on track)                                           │
│                                                                              │
│ [IDLE AGENTS]                                                               │
│ • research-agent (idle)                                                      │
│ • dev-agent-2 (idle)                                                        │
│ • integration-agent (idle)                                                  │
│                                                                              │
│ Actions: [C]laim task [M]essage agent [K]ill (force) [R]estart [Q]uit view │
└──────────────────────────────────────────────────────────────────────────────┘
```

### View W: Full Work Stream

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ FULL WORK STREAM (sortable, filterable) - Sort: [P]riority [D]uetime [S]tatus│
├──────────────────────────────────────────────────────────────────────────────┤
│ Filter: All | [P]ending [C]laimed [I]n-Progress [C]ompleted [B]locked       │
│                                                                              │
│ COMPLETED (12)                                                               │
│  TGNT-P5.5   test-runner       22m  ✓ L1 vs L2 benchmark command           │
│  TGNT-P5.4   dev-2             10m  ✓ Rules suggestion engine              │
│  ...         ...               ...  ...                                     │
│                                                                              │
│ IN_PROGRESS (3)                                                              │
│  TGNT-P6.1   dev-1             15m  ⚠ Per-agent GIT_INDEX_FILE mgt        │
│  TGNT-P6.3   tester            4m   ✓ CAS ref update with backoff         │
│  TGNT-P6.5   integration       7m   ⚠ harness git status per-agent view   │
│                                                                              │
│ CLAIMED (2)                                                                  │
│  TGNT-P6.4   dev-2             --   (just claimed, not started)            │
│  TGNT-P6.8   research-agent    --   (just claimed, not started)            │
│                                                                              │
│ PENDING (12)  -- Press [C] to claim, [D] to view dependencies               │
│  TGNT-P6.6   --                10m  ✓ Ready: Performance benchmarks        │
│  TGNT-P6.8   --                5m   ✓ Ready: Documentation updates         │
│  TGNT-P6.9   --                15m  ⏳ Blocked by TGNT-P6.7 (5m left)      │
│  TGNT-P6.10  --                8m   ⏳ Blocked by TGNT-P6.9                 │
│  TGNT-P7.1   --                8m   ⏳ Blocked by Phase 6 (50%, 8m left)    │
│  ...                                                                        │
│                                                                              │
│ Actions: Select task and press [D]etail [C]laim [U]nclaim [M]odify [Q]uit  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### View B: Blocker Analysis

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ BLOCKER ANALYSIS - Automated detection & resolution suggestions             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ ACTIVE BLOCKERS (2)                                                          │
│                                                                              │
│ 1. TGNT-P6.7 blocked by TGNT-P6.5 (2m left) - Wait time: 5m                │
│    └─ Dependency: TGNT-P6.5 (dev: 3m est, now 7m) - Over estimate         │
│    └─ Options:                                                              │
│       (A) Wait 2 more minutes (safe, P6.5 will complete)                   │
│       (B) Start parallel prep for P6.7 while P6.5 finishes                 │
│       (C) Escalate P6.5 SLO breach to L1 (it's 7m vs 3m estimate)          │
│    └─ Recommendation: Option A - will auto-resolve in 2m                   │
│                                                                              │
│ 2. TGNT-P7.1 blocked by PHASE 6 (50% done, 8m ETA) - Wait time: 18m        │
│    └─ Dependency: 6 pending items in PHASE 6 (est: 45m total)              │
│    └─ Options:                                                              │
│       (A) Wait for PHASE 6 completion (safe, clear blockers)                │
│       (B) Start PHASE 7 discovery/design work now (parallelizes planning)  │
│       (C) Deprioritize PHASE 7, focus on Phase 6 completions               │
│    └─ Recommendation: Option B - start Phase 7 planning while Phase 6 runs  │
│                                                                              │
│ CIRCULAR DEPENDENCIES: 0 (healthy)                                          │
│ CRITICAL BLOCKERS (>15m wait): 1 (TGNT-P7.1) - Monitor                     │
│ RECOVERY ACTIONS: [A]uto-unblock [M]anual resolve [E]scalate [Q]uit        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### View S: Extended Stats

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EXTENDED STATISTICS - Trends, predictions, performance analysis             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ CYCLE TIME TREND (last 10 completions)                                       │
│  Completion 1:  12 min ████░░░░░░                                            │
│  Completion 2:  15 min █████░░░░░                                            │
│  Completion 3:  18 min ██████░░░░  ← Current avg (18 min)                   │
│  ...                                                                        │
│  Completion 10: 22 min ███████░░░░ (target: 15 min) ⚠ Drifting upward      │
│  Trend: ▲ +10% (tasks getting slower)                                       │
│  Prediction: If trend continues, cycle time will be 25 min by Phase 7       │
│  Recommendation: Investigate why tasks are slowing (complexity? blockers?)   │
│                                                                              │
│ AGENT UTILIZATION TREND                                                      │
│  Time | Active | Idle | Waiting (blocked by deps)                          │
│  14:00│ ●●●●● │ ░░   │ (5/5 agents in use)                                 │
│  14:15│ ●●●░░ │ ██   │ (3/5 agents in use)                                 │
│  14:30│ ●●●░░ │ ██   │ (3/5 agents in use)                                 │
│  14:45│ ●●●░░ │ ██   │ (3/5 agents in use) ← Current                       │
│  Trend: ▼ -40% from start (may need more agents or prioritize next phase)   │
│                                                                              │
│ PHASE PROGRESS & ETA                                                         │
│  Phase 6 Progress: ████████░░░░░░░░░░ 45% (5/12 items completed)            │
│  Remaining Tasks: 7 items, total estimate: 56 min                           │
│  Avg Cycle Time: 18 min (used for prediction)                               │
│  Projected Completion: 16:45 UTC (+45 min from now)                         │
│  Confidence: 75% (high variance in cycle times)                             │
│                                                                              │
│ QUALITY METRICS                                                              │
│  Lint Checks: ✓ 100% pass (0 failures)                                      │
│  Test Coverage: ✓ 94% (target: 90%)                                         │
│  Type Checking: ✓ 0 errors, 2 warnings                                      │
│  Git Conflicts: ✓ 0 (no merge conflicts yet)                                │
│  Regressions: ✓ 0 (no downstream failures)                                  │
│                                                                              │
│ ACTIONS: [T]rends [P]redictions [Q]uality [H]elp [Q]uit                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: MVP Dashboard (Week 1)

```
1. Parse WORK_STREAM.md every 2-5 seconds
2. Display header + active agents + blockers + next available + health metrics
3. Hotkeys: [Q]uit, F5 [R]efresh, [A]gents detail
4. Color-coded status indicators
```

**Tech Stack:**

- Language: Bash or Python (curses/blessed)
- Data Source: `docs/reference/WORK_STREAM.md` (parsed as markdown table)
- Refresh: Simple file poll + terminal clear/redraw

### Phase 2: Extended Views (Week 2)

```
1. Implement [W]orkstream, [B]lockers, [S]tats views
2. Add sorting/filtering
3. Improve responsiveness (async file reads)
```

### Phase 3: Interactivity (Week 3)

```
1. [C]laim task with agent selection
2. [M]essage agent directly
3. Manual blocker resolution
4. Task detail editing
```

### Phase 4: Predictions & Automation (Week 4)

```
1. Phase completion ETA calculation
2. Auto-unblock ready tasks
3. Automated escalation alerts
4. Dashboard replay/history
```

---

## Color Palette

```
Status Colors:
- ✓ Green   (0/255/0) - Healthy, on track
- ⚠ Yellow  (255/255/0) - Warning, approaching limits
- 🔴 Red    (255/0/0) - Critical, action needed
- ⏳ Cyan   (0/255/255) - Waiting/blocked
- ░ Gray   (128/128/128) - Idle, not started

Text Colors:
- Title: Bold white
- Headers: Bold green
- Values: Normal white
- Warnings: Bold yellow
- Errors: Bold red
- Metrics: Green/yellow/red (depending on value)
```

---

## Example Session: Real Interaction

```
User starts dashboard:
$ thegent dashboard

[Dashboard loads]
- Shows dev-1 working on TGNT-P6.1 (15m elapsed, 8m est)
- Shows TGNT-P6.7 blocked by TGNT-P6.5 (5m wait)
- Suggests claiming TGNT-P6.6 (ready now, 10m)

[2 minutes pass, F5 auto-refresh]
- TGNT-P6.5 completes
- TGNT-P6.7 auto-unblocks (moves to PENDING)
- Dashboard highlights TGNT-P6.7 and TGNT-P6.6 as "ready now"

User presses [A] for agents view:
- Shows idle agent-2 available
- User selects TGNT-P6.6 from next available list
- Presses [C]laim
- Agent-2 is assigned TGNT-P6.6
- Dashboard immediately updates to show agent-2 as ACTIVE

[Process continues until phase complete]
```

---

## Version & Maintenance

| Version | Date       | Status  | Changes                          |
| ------- | ---------- | ------- | -------------------------------- |
| 1.0     | 2026-02-18 | Design  | Initial mockup and specification |
| 1.1     | TBD        | Planned | MVP implementation (Phase 1)     |
| 2.0     | TBD        | Planned | Extended views + sorting         |

**Maintained By:** L1 Coordinator
**Feedback & Issues:** File in docs/research/FEEDBACK\_\*.md
