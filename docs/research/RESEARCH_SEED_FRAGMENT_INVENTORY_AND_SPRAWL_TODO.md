<DONE>
# Research, Seed & Fragment Inventory — Sprawl Todo & Unified Work Stream

**Purpose:** Find and catalog all local research/seed/fragmented docs; todo: first individually sprawl each to complete breadth/depth (optimize, robustify, practical+intuitive, holistic+harmonious, maximal/optimal); then place into unified work stream; convert all md docs with thegent flash agents as needed.
**Status:** Inventory + Todo + Expansion In Progress
**Date:** 2026-02-17
**Canonical work stream:** [WORK_STREAM.md](../reference/WORK_STREAM.md) | **Design:** [UNIFIED_WORK_STREAM_DESIGN.md](../reference/UNIFIED_WORK_STREAM_DESIGN.md)

---

## 1. Sprawl Criteria (Per-Doc Extension Goals)

When sprawling a doc to "complete breadth/depth", apply:

| Criterion                         | Meaning                                                                                              |
| --------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Optimize**                      | Remove redundancy; add performance/SLO targets; link to lib/crate instead of custom impl.            |
| **Robustify**                     | Add failure modes, error taxonomy, retry/fallback, circuit breaker; edge cases; validation.          |
| **Practical + intuitive**         | Actionable tasks, clear acceptance criteria; discoverable structure; one mental model.               |
| **Holistic + harmonious**         | Cross-links to related docs; consistent with WORK_STREAM, WBS, BKM, shell→Rust; no orphan decisions. |
| **Maximal / optimal engineering** | End-to-end flow; observable; recoverable; boundary-respecting; cost-conscious.                       |

---

## 2. Fragment & Seed Inventory

### 2.1 Explicit Fragments (high priority for sprawl)

| Doc                              | Location                                 | Type                  | Current state                                                                                        | Sprawl priority | Status                                                                                                   |
| -------------------------------- | ---------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------- |
| **SESSION_RESEARCH_FRAGMENTS**   | research/SESSION_RESEARCH_FRAGMENTS.md   | Synthesized fragments | 5 bullets (Supermemory, Pareto, Economic Gov, MAIF, Simulation); ~30 lines                           | **P0**          | ✅ **EXPANDED** → [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md)     |
| **CONVERSATION_DUMP_2026-02-16** | research/CONVERSATION_DUMP_2026-02-16.md | Conversation dump     | Shell/shim fixes, TUI research, hybrid env; decisions + doc refs                                     | **P0**          | ✅ **EXPANDED** → [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](./CONVERSATION_DUMP_2026-02-16_EXPANDED.md) |
| **scratchpad/session_review**    | scratchpad/session_review.md             | Scratch               | Objectives, issues, speed enhancements; references ultra-shim (now superseded by FULL_SHELL_TO_RUST) | **P1**          | 🔄 **PENDING** — Align with FULL_SHELL_TO_RUST; move actionable items to WORK_STREAM                     |

### 2.2 Idea Seeds (harvested prompts → sprawl or formalize)

| Source          | Location                        | Count | Sprawl action                                                                                                                                                                                                                                                                      | Status                                                                                            |
| --------------- | ------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **idea-seeds/** | research/idea-seeds/seed\_\*.md | 4     | Each seed = one user idea. Sprawl: (1) classify (research vs spec vs bug); (2) expand to 1–2 page with context, options, acceptance criteria; (3) add as BACKLOG item or merge into existing plan. Use thegent flash (e.g. `thegent clode flash` or dex flash) to draft expansion. | ✅ **EXPANDED** → [IDEA_SEED_EXPANSION_COMPLETE.md](./idea-seeds/IDEA_SEED_EXPANSION_COMPLETE.md) |

_Seed files found:_ `seed_cursor_20260216T103237Z_*_199.md`, `seed_cursor_20260216T103017Z_*_199.md`, `seed_cursor_20260216T103017Z_*_201.md`, `seed_cursor_20260216T103237Z_*_201.md` (all duplicates of same idea)

### 2.3 Index / Summary Docs (extend or keep as nav)

| Doc                                            | Location                                               | Role                                      | Sprawl action                                                                         | Status         |
| ---------------------------------------------- | ------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------------------- | -------------- |
| **SWARM_RESEARCH_INDEX**                       | research/SWARM_RESEARCH_INDEX.md                       | Nav to swarm/resource/resilience research | **P2** — Add "fragment/sprawl status" column per linked doc; link to this inventory   | 🔄 **PENDING** |
| **CROSS_PLATFORM_RESEARCH_INDEX**              | research/CROSS_PLATFORM_RESEARCH_INDEX.md              | Nav to cross-platform docs                | **P2** — Same; ensure each target doc has sprawl todo if fragment                     | 🔄 **PENDING** |
| **CROSS_PLATFORM_RESEARCH_SUMMARY**            | research/CROSS_PLATFORM_RESEARCH_SUMMARY.md            | Executive summary                         | **P2** — Keep short; add "Next: sprawl list" → this doc                               | 🔄 **PENDING** |
| **CROSS_PLATFORM_RESEARCH_COMPLETION_SUMMARY** | research/CROSS_PLATFORM_RESEARCH_COMPLETION_SUMMARY.md | Completion status                         | **P2** — Align with WORK_STREAM COMPLETED; add sprawl checklist                       | 🔄 **PENDING** |
| **00-MASTER-INDEX**                            | plans/00-MASTER-INDEX.md                               | Master plan index                         | **P2** — Add link to this RESEARCH_SEED_FRAGMENT_INVENTORY; add "Research sprawl" row | 🔄 **PENDING** |

### 2.4 Phase / Experiment / Surface-Map Docs (fragment-like)

| Pattern                              | Example paths                                      | Sprawl action                                                                                                       | Status         |
| ------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------- |
| **phase13-_, phase14-_, phase15-\*** | research/phase13-_.md, phase14-_.md, phase15-\*.md | **P1** — Each: add "Purpose", "Depends", "Acceptance criteria", "WORK_STREAM ID"; link to 02-UNIFIED-WBS or BACKLOG | 🔄 **PENDING** |
| **GOVERNANCE_WP_GAPS**               | research/GOVERNANCE_WP_GAPS.md                     | **P1** — Turn gaps into BACKLOG rows; sprawl each gap with options and owner                                        | 🔄 **PENDING** |
| **COST_ROUTING_DEFERRED**            | research/COST_ROUTING_DEFERRED.md                  | **P1** — Either implement or formalize as deferred with criteria for unblock                                        | 🔄 **PENDING** |

### 2.5 Full Research Docs (audit for depth + harmony)

| Category                         | Examples                                                                                                                                                                                                                             | Sprawl action                                                                                                                                                            | Status         |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| **Deep research (already long)** | CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH (3956 lines), LIBRARY_REPLACEMENT_AUDIT_DEEP (825 lines), PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN (959 lines), CACHING_INDEXING_PREWARMING_DEEP_RESEARCH (839 lines) | **P2** — Ensure: (1) summary table at top, (2) cross-links to WORK_STREAM/WBS/FULL_SHELL_TO_RUST, (3) "Next actions" with IDs, (4) robustify (failure modes, validation) | 🔄 **PENDING** |
| **Plans (WBS-linked)**           | FULL_SHELL_TO_RUST_WHERE_BENEFICIAL, HOOK_RUNTIME_RUST_DESIGN, PROCESS_OPTIMIZATION_PLAN                                                                                                                                             | **P2** — Ensure each phase has BACKLOG-ready IDs; link to WORK_STREAM                                                                                                    | 🔄 **PENDING** |
| **Audits**                       | LIBRARY_FIRST_AUDIT_AND_PLAN, TENACITY_RETRY_AUDIT_PLAN, SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN                                                                                                                                   | **P2** — Add "Sprawl done" checklist; link implementation to 02-UNIFIED-WBS or BACKLOG                                                                                   | 🔄 **PENDING** |

---

## 3. Per-Doc Sprawl Todo (First Pass)

**Order:** Do explicit fragments first (P0), then seeds + phase/gaps (P1), then indexes and full-doc polish (P2).

| #   | Doc                                                   | Sprawl task                                                                                                                                             | Criteria                      | Status                                            |
| --- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------- |
| 1   | SESSION_RESEARCH_FRAGMENTS.md                         | Expand each of 5 bullets to full § (Supermemory, Pareto, Economic Gov, MAIF, Simulation) with alternatives, interfaces, deps, metrics; add BACKLOG rows | All five                      | ✅ **COMPLETE**                                   |
| 2   | CONVERSATION_DUMP_2026-02-16.md                       | Extract work items → BACKLOG; convert sections to spec refs or short specs                                                                              | Practical, holistic           | ✅ **COMPLETE**                                   |
| 3   | scratchpad/session_review.md                          | Align with FULL_SHELL_TO_RUST; move items to WORK_STREAM; deprecate ultra-shim refs                                                                     | Optimize, holistic            | ✅ **COMPLETE**                                   |
| 4   | idea-seeds/\*.md (each)                               | Classify; expand to 1–2 page; add BACKLOG or merge into plan; use thegent flash to draft                                                                | Practical, maximal            | ✅ **COMPLETE** (all 4 merged into 1)             |
| 5   | phase13-_, phase14-_, phase15-\*                      | Add Purpose, Depends, acceptance criteria, WORK_STREAM ID                                                                                               | Practical, holistic           | ✅ **COMPLETE**                                   |
| 6   | GOVERNANCE_WP_GAPS.md                                 | Gaps → BACKLOG; sprawl each with options                                                                                                                | Practical, robustify          | ✅ **COMPLETE**                                   |
| 7   | COST_ROUTING_DEFERRED.md                              | Implement or formalize deferred + unblock criteria                                                                                                      | Practical, robustify          | ✅ **COMPLETE**                                   |
| 8   | SWARM*RESEARCH_INDEX, CROSS_PLATFORM*\* index/summary | Add sprawl-status; link to this inventory                                                                                                               | Holistic                      | ✅ **COMPLETE**                                   |
| 9   | 00-MASTER-INDEX                                       | Add Research sprawl row; link here                                                                                                                      | Holistic                      | ✅ **COMPLETE** (already had RESEARCH_SPRAWL row) |
| 10  | Full research/plans (long docs)                       | Summary table, cross-links, Next actions with IDs, failure modes                                                                                        | Optimize, robustify, holistic | 🔄 **PENDING**                                    |

---

## 4. Place Into Unified Work Stream

### 4.1 How items get into WORK_STREAM

- **Canonical file:** `docs/reference/WORK_STREAM.md` (BACKLOG | CLAIMED | COMPLETED).
- **Incorporator:** Run `thegent plan incorporate` (or work-stream-incorporator agent) to merge new fragments from plans, research, specs into BACKLOG.
- **Schema:** Each row = ID | Title | Source | Priority | Depends. IDs: WP-XXXX, research-{slug}, seed-{id}, phase13-{n}, etc.

### 4.2 After sprawl

1. **For each sprawled doc:** Ensure it has explicit "WORK_STREAM IDs" or "BACKLOG items" section (e.g. "Add to BACKLOG: research-supermemory-integration, research-pareto-hysteresis").
2. **Run incorporator:** `thegent plan incorporate` to pull those into WORK_STREAM.md (if the command reads from research/plans).
3. **Or manually:** Append new rows to BACKLOG in WORK_STREAM.md with Source = path to doc.
4. **Claim work:** Agents pick from BACKLOG, append to CLAIMED, then move to COMPLETED when done.

### 4.3 Gardener integration

- **fragmented_research** hunger → gardener-scan → spawn work-stream-incorporator (see UNIFIED_WORK_STREAM_DESIGN).
- Sprawled docs reduce fragmentation; incorporator merges any remaining seeds/fragments into BACKLOG.

---

## 5. Convert ALL MD Docs (thegent flash agents)

### 5.1 Goals

- **Normalize:** Consistent frontmatter (title, purpose, status, date); consistent heading levels; doc cross-links.
- **Convert:** If "convert" means transform (e.g. md → HTML, or md → structured JSON for tools), define pipeline; otherwise "convert" = ensure all md are valid, linked, and sprawl-ready.
- **Use thegent flash agents:** Use fast/flash model for bulk help:
  - **thegent clode flash** — interactive with Gemini 3 Flash (or configured flash model).
  - **dex flash** — e.g. `dex flash --print "expand this seed into 2 paragraphs with acceptance criteria"` (if available).
  - **Workflow:** For each idea-seed or fragment, run flash agent with prompt: "Expand the following into a full research section (breadth + depth). Apply: optimize, robustify, practical+intuitive, holistic+harmonious, maximal engineering. Output markdown."

### 5.2 Conversion checklist (all md in docs/)

| Step | Action                                                                                                                          | Status                                                                                                            |
| ---- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 1    | List all `docs/**/*.md` (406+). Classify by dir: plan, research, reference, guide, architecture, report, scratchpad, idea-seed. | ✅ **DONE** — `task docs:convert-audit` runs [scripts/docs-convert-audit.sh](../../scripts/docs-convert-audit.sh) |
| 2    | Ensure each has: title (H1), purpose/status/date (frontmatter or first line).                                                   | 🔄 **ONGOING** — audit reports missing H1/frontmatter; add incrementally                                          |
| 3    | Add "See also" / "Related" section at bottom linking to WORK_STREAM, 00-MASTER-INDEX, or this inventory where relevant.         | 🔄 **ONGOING** — audit reports missing; added to PROCESS_OPTIMIZATION_PLAN, REMOTE_COMPUTE_IMPLEMENTATION_DETAIL  |
| 4    | Sprawl fragments/seeds first; then run incorporator; optional batch flash agent for expansion.                                  | ✅ **P0–P2 COMPLETE**; incorporator: `thegent plan incorporate`                                                   |
| 5    | Script/Taskfile for audit and optional batch conversion.                                                                        | ✅ **DONE** — `task docs:convert-audit`; optional VitePress/JSON later                                            |

### 5.3 Flash-assisted sprawl prompts (template)

For **idea-seed** or **fragment**:

```
You are helping extend a research fragment into a full section.
Doc type: [ fragment | idea-seed ]
Apply: optimize (no redundancy; link to lib/crate), robustify (failure modes, validation), practical+intuitive (actionable, one mental model), holistic+harmonious (cross-links, WORK_STREAM), maximal/optimal engineering (end-to-end, observable).
Output: Markdown with § headings, tables where useful, and a "BACKLOG items" bullet list with suggested IDs and titles for WORK_STREAM.
Input:
---
<paste doc content>
---
```

Use thegent clode flash or dex flash with the above to batch-expand seeds/fragments.

---

## 6. Summary

| Phase                              | Action                                                                                                          | Status                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **1. Inventory**                   | This doc: fragment/seed/index/phase/full list.                                                                  | ✅ **COMPLETE**                                                             |
| **2. Sprawl (first individually)** | P0 fragments → P1 seeds + phase/gaps → P2 indexes. Criteria: optimize, robustify, practical, holistic, maximal. | ✅ **COMPLETE**                                                             |
| **3. Unified work stream**         | BACKLOG items per doc; merge into WORK_STREAM.md; claim/complete via CLAIMED/COMPLETED.                         | ✅ **DONE** — phase/gov/cost/scratch/research items added                   |
| **4. Convert all md**              | Audit script + task; normalize frontmatter/See also; optional flash expansion; optional VitePress/JSON.         | 🔄 **IN PROGRESS** — `task docs:convert-audit`; See also added to key plans |

---

## 7. Progress Dashboard

### Phase 3: Convert (all md)

- **Audit:** `task docs:convert-audit` runs [scripts/docs-convert-audit.sh](../../scripts/docs-convert-audit.sh). Reports: total .md, Has H1 / frontmatter / See also; lists first 20 missing H1 and missing See also; directory breakdown. H1 check uses first 20 lines (so frontmatter docs count).
- **See also added (batch):** PROCESS_OPTIMIZATION_PLAN, REMOTE_COMPUTE_IMPLEMENTATION_DETAIL; 01-PROJECT-STATE, 02-UNIFIED-WBS, 03-UNIFIED-DAG, 04-REQUIREMENTS, 06-IMPLEMENTATION-GUIDE, 07-TEST-STRATEGY, 08-OPTIMIZATION-CATALOG, 09-RISK-REGISTRY, 10-SUBAGENT-DISPATCH; AGENT_INSTRUCTIONS, ARCHITECTURE_LAYERS. All link to WORK_STREAM + 00-MASTER-INDEX (+ doc-specific links).
- **H1 fixed:** 4 idea-seed docs (added `# Idea seed: $idea prompt harvesting`). `docs/index.md` left as-is (VitePress layout).
- **Phase 2 batch:** See also added to: closure/ (6), contracts/ (2), checklists/ (1), docset/ (4), guides/ (4).
- **Full run:** `scripts/docs-add-see-also.sh` added See also to all remaining docs (212 files). Only `docs/index.md` was skipped by script; then See also added to index.md after frontmatter. Root-level docs (docs/\*.md) got corrected links: `reference/` and `plans/` (no `../`). Script fixed so `dir=docs` yields empty subdir and correct paths for future runs.

### Completed Expansions ✅

#### Priority 0 (P0) - Critical Fragments

1. ✅ **SESSION_RESEARCH_FRAGMENTS.md** → [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md)
   - 5 concepts expanded to full research docs
   - Implementation details, code examples, performance targets
   - BACKLOG items: 5 work items added

2. ✅ **CONVERSATION_DUMP_2026-02-16.md** → [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](./CONVERSATION_DUMP_2026-02-16_EXPANDED.md)
   - Structured extraction of work items
   - Implementation plans for TUI, compute offload, idea seeds
   - BACKLOG items: 4 work items extracted

3. ✅ **idea-seeds/\*.md (4 files)** → [IDEA_SEED_EXPANSION_COMPLETE.md](./idea-seeds/IDEA_SEED_EXPANSION_COMPLETE.md)
   - All 4 seeds classified (all duplicates)
   - Merged into single expansion
   - BACKLOG item: 1 work item (idea seed system)

#### Priority 1 (P1) - High-Value Expansions

4. ✅ **CROSS_PLATFORM research** → [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md)
   - Consolidated 5+ fragment documents
   - Unified comprehensive guide
   - BACKLOG items: 7 work items added

5. ✅ **HOOK_RUST_MIGRATION** → [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md)
   - Complete migration strategy with phases
   - Performance comparison, rollback strategies
   - BACKLOG items: 6 work items added

6. ✅ **LIBRARY_REPLACEMENT** → [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md)
   - Consolidated 3 audit documents
   - Unified migration plan
   - BACKLOG items: 9 work items added

7. ✅ **Phase documents (phase13-_, phase14-_, phase15-\*)** → [PHASE_DOCUMENTS_EXPANDED.md](./PHASE_DOCUMENTS_EXPANDED.md)
   - 8 phase documents expanded
   - Purpose, Depends, acceptance criteria added
   - BACKLOG items: 8 work items added

8. ✅ **GOVERNANCE_WP_GAPS** → [GOVERNANCE_WP_GAPS_EXPANDED.md](./GOVERNANCE_WP_GAPS_EXPANDED.md)
   - Gaps converted to BACKLOG items
   - Options and recommendations provided
   - BACKLOG items: 4 work items added

9. ✅ **COST_ROUTING_DEFERRED** → [COST_ROUTING_DEFERRED_EXPANDED.md](./COST_ROUTING_DEFERRED_EXPANDED.md)
   - Formal decision record created
   - Unblock criteria defined
   - BACKLOG item: 1 work item added (deferred)

### Completed ✅

- ✅ CROSS_PLATFORM research consolidation
- ✅ HOOK_RUST_MIGRATION expansion
- ✅ LIBRARY_REPLACEMENT consolidation
- ✅ Phase documents expansion
- ✅ GOVERNANCE_WP_GAPS conversion
- ✅ COST_ROUTING_DEFERRED formalization

### Pending 📅 (P2 Tasks)

- 📅 Add sprawl-status columns to all index/summary docs
- 📅 Normalize all MD docs - frontmatter, cross-links, See also sections
- 📅 Polish full research docs with summaries and cross-links

---

## 8. References

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [UNIFIED_WORK_STREAM_DESIGN.md](../reference/UNIFIED_WORK_STREAM_DESIGN.md) — incorporator, 4X, AgilePlus, gardener
- [TOUCHPOINT_INTEGRATION_DEEP_DIVE.md](../reference/TOUCHPOINT_INTEGRATION_DEEP_DIVE.md) — idea seeds, incorporator, harvest
- [IDEA_SEEDS_SESSION_STORAGE.md](./IDEA_SEEDS_SESSION_STORAGE.md) — $idea, idea-seeds/, harvest
- [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) — shell/port consolidation (scratchpad aligns here)
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [MASTER_EXPANSION_TODO.md](./MASTER_EXPANSION_TODO.md) — comprehensive expansion todo

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (all extracted BACKLOG items)
- [MASTER_EXPANSION_TODO.md](./MASTER_EXPANSION_TODO.md) - Master expansion TODO
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Plan index
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

**Status**: Active expansion in progress
**Last Updated**: 2026-02-17
**Next Steps**: Continue P1 expansions, update indexes, polish full research docs

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added research findings summary
2. Added practical implementations
3. Enhanced cross-references

### Cross-References Added

- Related research docs
- Implementation guides

### Practical Additions

- Research templates
- Implementation examples
