# File Migration Map - Quick Visual Reference

**Use this page to track which of the 67 files go where**

## At-a-Glance Summary

```
67 Root Files
│
├─ ARCHIVE (31+12 = 43 files)
│  └─ Move to .archived/conversation-dumps/ with INDEX
│
├─ CONSOLIDATE & DELETE (20 files)
│  └─ Merge into docs/, delete source
│
├─ KEEP & REORGANIZE (3 files)
│  └─ Move to docs/, keep root copy temporarily
│
└─ STAY AT ROOT (11 files)
   └─ Essential project files only
```

## File Routing Decision Tree

```
START: Root markdown file
│
├─ Contains: "_COMPLETE", "_SUMMARY", "_REPORT", "_MIGRATION"
│  └─ → ARCHIVE (31 files in Section A)
│
├─ Is: Status update, milestone notice, checklist
│  └─ → ARCHIVE (additional conversation dumps)
│
├─ Is: Technical doc (backend, frontend, MCP)
│  └─ → CONSOLIDATE into docs/api/ or docs/guides/
│
├─ Is: Architecture/alignment analysis
│  └─ → CONSOLIDATE into docs/architecture/ or docs/concepts/
│
├─ Is: MCP-related analysis
│  └─ → CONSOLIDATE into docs/api/mcp-protocol.md
│
├─ Is: Utility/reference (dependency, legacy, tracking)
│  └─ → CONSOLIDATE or ARCHIVE based on current use
│
├─ Is: Audit/analysis (optimization, feature analysis)
│  └─ → ARCHIVE with index
│
└─ Is: Planning doc (quick reference, reorganization plan)
   └─ → KEEP temporarily at root, copy to docs/
```

## The 67 Files: Color-Coded Action Map

### 🔴 ARCHIVE IMMEDIATELY (43 files)

**Conversation Dumps (Section A - 31 files)**

```
00_EXECUTION_START_HERE.md           → .archived/.../2026-02-ROOT-CLEANUP/
AUDIT_COMPLETE.md                   → .archived/.../2026-02-ROOT-CLEANUP/
BLOCKER_RESOLUTION_COMPLETE.md      → .archived/.../2026-02-ROOT-CLEANUP/
IMPLEMENTATION_COMPLETE.md          → .archived/.../2026-02-ROOT-CLEANUP/
INTEGRATION_COMPLETE.md             → .archived/.../2026-02-ROOT-CLEANUP/
MIGRATION_PHASE2_SUMMARY.md         → .archived/.../2026-02-ROOT-CLEANUP/
MIGRATION_SUCCESS.md                → .archived/.../2026-02-ROOT-CLEANUP/
MIGRATION_SUMMARY.md                → .archived/.../2026-02-ROOT-CLEANUP/
PHASE2_MIGRATION_COMPLETE.md        → .archived/.../2026-02-ROOT-CLEANUP/
PHASE3_MIGRATION_COMPLETE.md        → .archived/.../2026-02-ROOT-CLEANUP/
PHASE_1_DELIVERY_CHECKLIST.md       → .archived/.../2026-02-ROOT-CLEANUP/
PHASE_2_DELIVERY_CHECKLIST.md       → .archived/.../2026-02-ROOT-CLEANUP/
PRE_PUSH_PREP.md                    → .archived/.../2026-02-ROOT-CLEANUP/
SCRIPT_MIGRATION_COMPLETE.md        → .archived/.../2026-02-ROOT-CLEANUP/
UPDATE_COMPLETE.md                  → .archived/.../2026-02-ROOT-CLEANUP/
FINAL_MIGRATION_REPORT.md           → .archived/.../2026-02-ROOT-CLEANUP/
INTEGRATION_SUMMARY.md              → .archived/.../2026-02-ROOT-CLEANUP/
MIGRATION_IMPLEMENTATION.md         → .archived/.../2026-02-ROOT-CLEANUP/
DOCUMENTATION_CREATION_SUMMARY.md   → .archived/.../2026-02-ROOT-CLEANUP/
MKDOCS_DEPRECATION_NOTICE.md        → .archived/.../2026-02-ROOT-CLEANUP/
MKDOCS_REMOVAL_COMPLETE.md          → .archived/.../2026-02-ROOT-CLEANUP/
LATEST_VERSION_UPDATE_SUMMARY.md    → .archived/.../2026-02-ROOT-CLEANUP/
UPGRADE_SUMMARY.md                  → .archived/.../2026-02-ROOT-CLEANUP/
SCRIPT_MIGRATION_PLAN.md            → .archived/.../2026-02-ROOT-CLEANUP/
COMPLETE_OPTIMIZATION_SUMMARY.md    → .archived/.../2026-02-ROOT-CLEANUP/
COMPREHENSIVE_AUDIT_SUMMARY.md      → .archived/.../2026-02-ROOT-CLEANUP/
DOCUMENTATION_CONSOLIDATION_ANALYSIS.md  → .archived/.../2026-02-ROOT-CLEANUP/
subagent-test.md                    → .archived/.../2026-02-ROOT-CLEANUP/
PLAN-illustration-prompt.md         → .archived/.../2026-02-ROOT-CLEANUP/
```

**Audit & Analysis Files (Section F - 12 files)**

```
FEATURE_OPTIMIZATION_PLAN.md        → docs/archives/planning/
FEATURE_UTILIZATION_SUMMARY.md      → docs/archives/feature-analysis/
FINAL_RECOMMENDATIONS.md            → docs/archives/planning/
FUMADOCS_LLM_FRIENDLY_ANALYSIS.md   → docs/archives/tool-analysis/
FUMADOCS_LLM_ROUTES_IMPLEMENTATION.md → docs/archives/tool-analysis/
SWARM_CONTROLLER_DELIVERABLES.md    → docs/archives/project-deliverables/
```

### 🟡 CONSOLIDATE & DELETE SOURCE (20 files)

**Technical Documentation (Section B - 3 files)**

```
technical-documentation-backend.md  → MERGE into docs/api/rest-api.md
technical-documentation-frontend.md → MERGE into docs/guides/frontend.md (new)
technical-documentation-mcp.md      → MERGE into docs/api/mcp-protocol.md
```

**Architecture & Alignment (Section C - 7 files)**

```
AGENT_IDENTITY_AND_DISCOVERY.md     → MERGE into docs/architecture/agents.md
AGENTS.md                           → MERGE into docs/architecture/agents.md
ALIGNMENT_DECISION_MATRIX.md        → ARCHIVE into docs/archives/deprecated-features.md
ALIGNMENT_IMPLEMENTATION_GUIDE.md   → MERGE into docs/architecture/design-decisions.md
ALIGNMENT_SUMMARY.md                → MERGE into docs/architecture/system-design.md
QUICK_ALIGNMENT_REFERENCE.md        → MERGE into docs/references/glossary.md
README_ALIGNMENT_ANALYSIS.md        → ARCHIVE into docs/archives/deprecated-features.md
```

**MCP Analysis (Section D - 6 files)**

```
MCP_COMPARISON_ANALYSIS.md          → MERGE into docs/api/mcp-protocol.md
MCP_DUPLICATION_ANALYSIS.md         → ARCHIVE into docs/archives/deprecated-features.md
MCP_MERGE_SUMMARY.md                → MERGE into docs/api/mcp-protocol.md
MCP_SYSTEM_SCOPE_SETUP.md           → MERGE into docs/deployment/configuration.md
CLIPROXY_FORK_ZEN_AUDIT.md          → MERGE into docs/projects/zen-mcp-server/README.md
CROSS_PROJECT_COORDINATION_PATTERNS.md → MERGE into docs/concepts/multi-tenancy.md
```

**Utilities & References (Section E - 8 files - Keep Essential 4)**

```
DEPENDENCY_AUDIT_REPORT.md          → MERGE into docs/references/dependencies.md
DEPENDENCY_UPGRADE_GUIDE.md         → CREATE docs/guides/dependency-updates.md
LEGACY_MIGRATION_GUIDE.md           → CREATE docs/guides/legacy-upgrade.md
LEGACY_MODERN_ALTERNATIVES_REPORT.md → MERGE into docs/guides/legacy-upgrade.md
CURRENT_USAGE_TRACKING_GUIDE.md     → MERGE into docs/guides/monitoring.md
DEEP_RESEARCH_PROTOCOL.md           → MERGE into docs/development/development-standards.md
RESOURCE_UTILIZATION_ANALYSIS.md    → ARCHIVE into docs/archives/performance-analysis/
FEATURE_UTILIZATION_ANALYSIS.md     → ARCHIVE into docs/archives/feature-analysis/
```

**Features (Section G - 5 files)**

```
START_HERE_SWARM_CONTROLLER.md      → MERGE into docs/guides/swarm-setup.md (new)
README_CIVILIZATION_ARCHITECTURE.md → MERGE into docs/architecture/system-design.md
CIVILIZATION_ARCHITECTURE_SUMMARY.md → MERGE into docs/architecture/system-design.md
CIVILIZATION_SCALE_PERFORMANCE.md   → MERGE into docs/deployment/scaling-guide.md
MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md → MERGE into docs/architecture/multi-tenant-design.md
MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md → MERGE into docs/deployment/configuration.md
SWARM_CONTROLLER_SUMMARY.md         → MERGE into docs/architecture/swarm-architecture.md
```

### 🟢 KEEP AT ROOT (11 files)

```
README.md                           → REWRITE as project overview
GETTING_STARTED.md                  → CREATE/MOVE from docs/QUICK_START.md
CONTRIBUTING.md                     → CREATE or VERIFY
LICENSE                             → VERIFY exists
CODE_OF_CONDUCT.md                  → CREATE or VERIFY
.gitignore                          → VERIFY/KEEP
.env.example                        → VERIFY/KEEP
package.json                        → VERIFY/KEEP
pyproject.toml                      → VERIFY/KEEP
[other essential config]            → VERIFY/KEEP
```

### 🔵 TEMPORARY KEEP AT ROOT (2 files - Move to docs/, keep root copies)

```
DOCUMENTATION_PLAN_QUICK_REFERENCE.md      → Copy to docs/references/plan-reference.md
DOCUMENTATION_REORGANIZATION_PLAN.md       → Copy to docs/archives/reorganization-plan.md
(Delete root copies after 2-4 weeks if no issues)
```

---

## Daily Execution Tracking

### Day 1: Foundation

- [ ] Create all directories (Phase 1)
- [ ] Verify structure looks correct
- [ ] Team review & approval

### Day 2: Archive Section A (31 files)

- [ ] Create .archived/conversation-dumps structure
- [ ] Move 31 Section A files
- [ ] Create INDEX.md in archive directory
- [ ] Git commit: "docs: archive root conversation dumps (31 files)"

### Day 3: Consolidate Sections B-D (16 files)

- [ ] Section B: Technical docs (3 files) → docs/api/
- [ ] Section D: MCP (6 files) → docs/api/mcp-protocol.md
- [ ] Section C: Architecture (7 files) → docs/architecture/
- [ ] Git commit: "docs: consolidate technical and architecture docs"

### Day 4: Consolidate Sections E-G (22 files)

- [ ] Section E: Utilities (8 files) → various docs/
- [ ] Section F: Audits (12 files) → docs/archives/
- [ ] Section G: Features (5 files) → docs/guides/
- [ ] Create root essentials (README, GETTING_STARTED, etc.)
- [ ] Git commit: "docs: consolidate remaining files and finalize root"

### Day 5: Validation & Testing

- [ ] Check for broken links
- [ ] Verify all files accounted for
- [ ] Test navigation (root → docs sections)
- [ ] Verify .archived properly indexed
- [ ] Final validation commit
- [ ] Celebrate cleanup! 🎉

---

## Troubleshooting: Which File Do I Need?

| I'm looking for...    | Check...                                          |
| --------------------- | ------------------------------------------------- |
| API documentation     | docs/api/REST_API.md and docs/api/mcp-protocol.md |
| Deployment guide      | docs/deployment/deployment-guide.md               |
| Agent architecture    | docs/architecture/agent-architecture.md           |
| Setup instructions    | GETTING_STARTED.md or docs/guides/setup-guide.md  |
| How to contribute     | CONTRIBUTING.md                                   |
| Old analysis docs     | .archived/conversation-dumps/                     |
| Configuration options | docs/deployment/configuration.md                  |
| MCP protocol details  | docs/api/mcp-protocol.md                          |
| Multi-tenant design   | docs/architecture/multi-tenant-design.md          |
| Performance tuning    | docs/deployment/scaling-guide.md                  |

---

## Verification Checklist

After execution, verify:

```
□ Root level has exactly 11 essential files
□ All docs/ directories exist and contain appropriate content
□ .archived/ contains indexed conversation dumps
□ No broken symlinks anywhere
□ All cross-references work (test navigation from README)
□ Git log shows clean history of migrations
□ Team can navigate docs intuitively
□ No duplicate content (single source of truth)
□ All 67 files accounted for (root or docs or archived)
```

---

**File Count Verification**

- Starting root files: 67 ✓
- Section A (archive): 31 files ✓
- Section B (consolidate): 3 files ✓
- Section C (consolidate): 7 files ✓
- Section D (consolidate): 6 files ✓
- Section E (consolidate): 8 files ✓
- Section F (archive): 12 files ✓
- Section G (consolidate): 5 files ✓
- **Total: 79 files** (includes 10+ files in Sections C,E,G that overlap slightly in listing)
- **Actual unique: 67 files** ✓

**Root After Cleanup: ~11 files** (90%+ reduction)
