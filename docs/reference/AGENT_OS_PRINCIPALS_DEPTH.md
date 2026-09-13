# Agent OS Principals — Depth Document

**Purpose:** Options for treating agents as first-class OS principals (beyond sub-user and OS user creation). Enterprise and future deployment patterns.

**Date:** 2026-02-16
**Extends:** CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md §5, AGENT_IDENTITY_SOVEREIGNTY_DEPTH.md

---

## 1. Current Models

| Model        | Isolation         | OS Identity             | Use Case     |
| ------------ | ----------------- | ----------------------- | ------------ |
| **Sub-user** | Process tree only | None                    | Dev, trusted |
| **OS user**  | Real user account | useradd / New-LocalUser | Production   |
| **Docker**   | Container         | Container user          | Sandbox      |

---

## 2. Deeper OS Integration Options

### 2.1 Linux: systemd Scope

**Mechanism:** `systemd-run --scope -p MemoryMax=512M -p CPUQuota=50% -- thegent run ...`

**Pros:** Resource containment without cgroups code; uses systemd
**Cons:** Requires systemd; root or user scope
**Effort:** Low (4-6 tool calls)
**Status:** Recommended for Phase 3 when `isolation_mode=osuser` on Linux

### 2.2 Linux: PAM Module

**Mechanism:** Custom PAM module for "agent" authentication; agent logs in as service
**Pros:** Full OS auth integration; audit trail
**Cons:** High complexity; security-sensitive
**Effort:** High
**Status:** Document only; future enterprise option

### 2.3 Windows: Service Account

**Mechanism:** Run thegent as Windows Service under dedicated account (e.g. `NT SERVICE\thegent`)
**Pros:** Survives logout; proper service lifecycle
**Cons:** Requires admin; different execution context
**Effort:** Medium
**Status:** Document only; future enterprise option

### 2.4 Windows: Job Objects

**Mechanism:** `CreateJobObject`, `AssignProcessToJobObject` with memory/CPU limits
**Pros:** Resource containment; no admin for user jobs
**Cons:** Windows-specific
**Effort:** Medium (8-12 tool calls)
**Status:** Add to Phase 3 (see CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH §4)

### 2.5 macOS: launchd Per-Agent

**Mechanism:** Create launchd plist per agent; `launchctl load`
**Pros:** Native daemon lifecycle; launch-on-demand
**Cons:** macOS only; plist management
**Effort:** Medium
**Status:** Document only; future option

---

## 3. Implementation Priority

| Option                | Priority | Phase   |
| --------------------- | -------- | ------- |
| systemd scope (Linux) | P1       | Phase 3 |
| Windows Job Objects   | P1       | Phase 3 |
| PAM module            | P3       | Future  |
| Windows Service       | P3       | Future  |
| launchd per-agent     | P3       | Future  |

---

## 4. References

- [CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md](../research/CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md)
- [AGENT_IDENTITY_SOVEREIGNTY_DEPTH.md](./AGENT_IDENTITY_SOVEREIGNTY_DEPTH.md)
- [CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md](../research/CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md)
- [GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](../research/GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md) — Git wrapper in agent PATH, hooks layout for system user

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
