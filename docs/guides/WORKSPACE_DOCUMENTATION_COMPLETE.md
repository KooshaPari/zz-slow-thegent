# Workspace Documentation System - Complete Reference

## Overview

This document maps ALL document types in the workspace ecosystem with usage patterns, locations, and relationships.

---

## I. HUMAN-FACING DOCS

### A. User & Developer Guides

| Type            | Pattern               | Count | Purpose         | Location                    |
| --------------- | --------------------- | ----- | --------------- | --------------------------- |
| USER_GUIDE      | `*USER_GUIDE*.md`     | 2     | End-user docs   | docs/guides, docs/migration |
| QUICK_START     | `*QUICK_START*.md`    | 3     | Getting started | docs/guides                 |
| QUICK_REFERENCE | `*QUICK_REFERENCE.md` | 4     | Rapid ref       | docs/reference              |
| GUIDE           | `*GUIDE*.md`          | 40+   | Deep-dive       | docs/guides                 |
| HANDBOOK        | `*HANDBOOK.md`        | -     | Comprehensive   | docs/guides                 |

### B. Conceptual & Explanatory

| Type       | Pattern           | Purpose        |
| ---------- | ----------------- | -------------- |
| OVERVIEW   | `*OVERVIEW*.md`   | System summary |
| EXPLAINER  | `*EXPLAINER*.md`  | Concept intro  |
| PRINCIPLES | `*PRINCIPLES*.md` | Core beliefs   |

---

## II. TECHNICAL SPECIFICATIONS

### A. Formal Specs

| Type     | Pattern         | Count | Purpose             |
| -------- | --------------- | ----- | ------------------- |
| SPEC     | `SPEC*.md`      | 80+   | Technical spec      |
| PROTOCOL | `*PROTOCOL*.md` | 15+   | Protocol def        |
| CONTRACT | `CONTRACT*.md`  | 10+   | Interface contracts |
| SCHEMA   | `*SCHEMA*.md`   | -     | Data schemas        |
| FORMAT   | `FORMAT*.md`    | -     | Format specs        |

### B. Architecture

| Type         | Pattern             | Count | Purpose               |
| ------------ | ------------------- | ----- | --------------------- |
| ARCHITECTURE | `*ARCHITECTURE*.md` | 3+    | System design         |
| DESIGN       | `DESIGN*.md`        | 16    | Implementation design |
| ADR          | `ADR-*.md`          | 21    | Decisions             |
| BLUEPRINT    | `*BLUEPRINT*.md`    | -     | High-level plan       |

---

## III. PLANNING & TRACKING

### Strategic

| Type        | Pattern            | Purpose             |
| ----------- | ------------------ | ------------------- |
| ROADMAP     | `*ROADMAP*.md`     | Long-term planning  |
| MASTER_PLAN | `*MASTER_PLAN*.md` | Implementation plan |
| STRATEGY    | `*STRATEGY*.md`    | Strategic direction |
| OKR         | `OKR*.md`          | Objectives/results  |

### Tactical

| Type           | Pattern               | Count | Purpose        |
| -------------- | --------------------- | ----- | -------------- |
| PLAN           | `*PLAN*.md`           | 20+   | Implementation |
| IMPLEMENTATION | `*IMPLEMENTATION*.md` | 10+   | Execution      |
| PHASE          | `PHASE*.md`           | -     | Phase planning |
| WBS            | `*WBS.md`             | -     | Work breakdown |

### Tracking

| Type     | Pattern         | Purpose          |
| -------- | --------------- | ---------------- | -------------- |
| TRACKER  | `*TRACKER.md`   | Item tracking    |
| STATUS   | `*STATUS*.md`   | Status reporting |
| PROGRESS | `*PROGRESS*.md` | Progress updates |
| REPORT   | `*REPORT.md`    | 40+              | Status reports |

---

## IV. RESEARCH & EXPLORATION

### Exploratory

| Type          | Pattern              | Count | Purpose          |
| ------------- | -------------------- | ----- | ---------------- |
| RESEARCH      | `*RESEARCH*.md`      | 40+   | Investigation    |
| INVESTIGATION | `*INVESTIGATION*.md` | -     | Deep analysis    |
| AUDIT         | `*AUDIT*.md`         | 3     | Code/state audit |
| ANALYSIS      | `*ANALYSIS*.md`      | -     | Data analysis    |

### Synthesized

| Type      | Pattern          | Purpose           |
| --------- | ---------------- | ----------------- | ----------------------- |
| SYNTHESIS | `*SYNTHESIS*.md` | Combined research |
| SURVEY    | `*SURVEY*.md`    | Landscape survey  |
| BENCHMARK | `BENCHMARK.md`   | Performance data  |
| PATTERNS  | `PATTERNS.md`    | 15+               | Implementation patterns |

---

## V. VALIDATION & QUALITY

### Testing

| Type      | Pattern      | Purpose         |
| --------- | ------------ | --------------- |
| TEST_PLAN | `*TEST*.md`  | Test strategy   |
| MATRIX    | `*MATRIX.md` | Coverage matrix |
| CASES     | `*CASES.md`  | Test cases      |

### Quality Gates

| Type         | Pattern             | Purpose              |
| ------------ | ------------------- | -------------------- |
| VERIFICATION | `*VERIFICATION*.md` | Check results        |
| VALIDATION   | `*VALIDATION*.md`   | Verification results |
| CHECKLIST    | `CHECKLIST.md`      | Manual checks        |

---

## VI. OPERATIONAL

### Runbooks

| Type     | Pattern       | Purpose           |
| -------- | ------------- | ----------------- | ---------------------- |
| RUNBOOK  | `*RUNBOOK.md` | Incident response |
| PLAYBOOK | `PLAYBOOK.md` | 10+               | Operational procedures |

### Monitoring

| Type      | Pattern         | Purpose           |
| --------- | --------------- | ----------------- |
| DASHBOARD | `*DASHBOARD.md` | Dashboards        |
| ALERTING  | `*ALERTING*.md` | Alert definitions |
| METRICS   | `METRICS.md`    | Metrics           |

---

## VII. STANDARDS & GOVERNANCE

### Standards

| Type       | Pattern          | Purpose           |
| ---------- | ---------------- | ----------------- | ------------------ |
| STANDARD   | `*STANDARD.md`   | Coding standards  |
| CONVENTION | `*CONVENTION.md` | Naming/formatting |
| GUIDELINES | `GUIDELINES.md`  | Best practices    |
| TEMPLATE   | `*TEMPLATE.md`   | 5                 | Reusable templates |

### Governance

| Type     | Pattern        | Purpose       |
| -------- | -------------- | ------------- | ------------------- |
| CONTRACT | `*CONTRACT.md` | 10+           | Interface contracts |
| PROCESS  | `*PROCESS.md`  | Workflows     |
| POLICY   | `*POLICY.md`   | Team policies |

---

## VIII. PROJECT LIFECYCLE

### Tracking

| Type          | Pattern          | Purpose             |
| ------------- | ---------------- | ------------------- |
| CHANGELOG     | CHANGELOG.md     | Release history     |
| MILESTONE     | `*MILESTONE.md`  | Release milestones  |
| RETROSPECTIVE | `*RETRO*.md`     | Team retros         |
| POSTMORTEM    | `*POSTMORTEM.md` | Incident postmortem |

---

## Quick Reference

### By Need

| Need           | Use                     |
| -------------- | ----------------------- |
| User docs      | USER_GUIDE, QUICK_START |
| Technical spec | SPEC, PROTOCOL          |
| Decision       | ADR                     |
| Research       | RESEARCH, SURVEY        |
| Implementation | PLAN, PATTERNS          |
| Testing        | TEST_PLAN, VERIFICATION |
| Operations     | RUNBOOK, PLAYBOOK       |

### Lifecycle

| Phase          | Primary Docs            |
| -------------- | ----------------------- |
| Inception      | VISION, ROADMAP         |
| Planning       | PLAN, ADR               |
| Research       | RESEARCH, ANALYSIS      |
| Implementation | SPEC, PATTERNS          |
| Validation     | VERIFICATION, TEST_PLAN |
| Operations     | RUNBOOK, PLAYBOOK       |
| Handoff        | CHANGELOG, SYNTHESIS    |

---

_See MASTER_INDEX_UNIFIED.md for project inventory_
_See DOCUMENTATION_TAXONOMY.md for type taxonomy_
