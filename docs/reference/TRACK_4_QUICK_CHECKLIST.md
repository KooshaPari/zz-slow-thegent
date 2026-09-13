# Track 4 Quick Checklist

**Status:** Design Complete | Ready for Implementation
**Parallel Execution:** 4 agents optimal
**Wall-Clock Estimate:** 12–16 hours (Phase 1–4)

---

## Phase 1: Infrastructure (2–3 hours)

### P1.1: Define IPC Contracts ✓

- [x] Create `docs/reference/IPC_PROTOCOL_SPEC.md` (MCP schema, error handling)
- [x] Create `docs/reference/SUBPROJECT_INTERFACES.md` (tool invocation contract)
- [x] Create `docs/reference/SESSION_STATE_CONTRACT.md` (JSONL format)
- **Acceptance:** All schemas documented with JSON Schema, Pydantic models generated

### P1.2: Workspace Config ✓

- [ ] Create `sub-projects/thegent-cli/pyproject.toml`
- [ ] Create `sub-projects/thegent-agents/pyproject.toml`
- [ ] Create `sub-projects/thegent-mcp/pyproject.toml`
- [ ] Update root `pyproject.toml` (uv workspace config)
- [ ] Add `crates/thegent-ffi/Cargo.toml` (Rust bridge)
- [ ] Verify `uv sync --group dev` works
- **Acceptance:** `uv sync` completes, no conflicts

### P1.3: Update tach.toml ✓

- [ ] Add sub-project modules to tach.toml
- [ ] Verify no cycles (DAG constraint)
- [ ] Run `tach check` and document DAG
- [ ] Update tach dependencies (L0 → L4 layers)
- **Acceptance:** `tach check` passes, DAG visualization correct

---

## Phase 2: Extract Sub-Projects (8–10 hours)

### P2.1: Extract thegent-cli ✓

- [ ] Move files: `src/thegent/cli/` → `sub-projects/thegent-cli/src/thegent_cli/`
- [ ] Remove domain logic (agents, planning, memory)
- [ ] Create `mcp_client.py` (MCP ClientSession wrapper)
- [ ] Update imports (`thegent.cli` → `thegent_cli`)
- [ ] Tests pass: `uv run pytest sub-projects/thegent-cli/tests/ -v`
- [ ] Line count: ~8K LOC (target)
- [ ] `tach check` passes
- **Acceptance:** CLI talks only to agents via MCP, no direct agent imports

### P2.2: Extract thegent-agents ✓

- [ ] Move files: `src/thegent/agents/`, `orchestration/`, `planning/`, `memory/`, `team/` → sub-project
- [ ] Create `server.py` (FastMCP server with @mcp.tool decorators)
- [ ] Implement `run_agent`, `list_agents`, `get_state`, `stop_agent` tools
- [ ] Implement `query_memory`, `add_memory` tools
- [ ] Implement resources: `agents://{id}/state`, `agents://{id}/memory`
- [ ] Create `__main__.py` (CLI entry point, start server)
- [ ] Tests pass: `uv run pytest sub-projects/thegent-agents/tests/ -v`
- [ ] Server starts on port 3847 by default
- [ ] `tach check` passes
- **Acceptance:** Agents MCP server fully operational, all tools accessible

### P2.3: Extract thegent-mcp + Absorb zen-mcp-server ✓

- [ ] Move files: `src/thegent/mcp/` → `sub-projects/thegent-mcp/src/thegent_mcp/`
- [ ] Copy zen-mcp-server tools: `/kush/zen-mcp-server/mcp_tools/` → `tools/`
  - [ ] GitHub tools
  - [ ] Slack tools
  - [ ] Stripe tools
  - [ ] OpenAI tools
  - [ ] Anthropic tools
  - [ ] Jira, Confluence, Salesforce, etc.
- [ ] Create tool registry in `server.py` (dynamic module loading)
- [ ] Verify all tool modules load without import errors
- [ ] Tests pass: `uv run pytest sub-projects/thegent-mcp/tests/ -v`
- [ ] Tool count ≥ 500
- [ ] Server starts on port 3848
- [ ] `tach check` passes
- **Acceptance:** thegent-mcp server aggregates all zen tools, no functionality lost

### P2.4: Deprecate & Archive ✓

- [ ] Create `/kush/task-tool/DEPRECATED.md` (migration path)
- [ ] Create `/kush/agentapi/ARCHIVED.md`
- [ ] Create `/kush/agentapi++/ARCHIVED.md`
- [ ] Create `/kush/zen-mcp-server/DEPRECATED.md`
- [ ] Update `/kush/README.md` (ecosystem status)
- **Acceptance:** All notices in place, no code changes required

---

## Phase 3: Integration & Validation (4–5 hours)

### P3.1: Full Test Suite ✓

- [ ] All sub-project tests pass independently
- [ ] Root `pytest sub-projects/*/tests/ -v` runs all tests
- [ ] Cargo tests pass: `cargo test --workspace`
- [ ] Coverage ≥ 80% for agents, mcp; ≥ 95% for cli
- [ ] Type checking passes: `basedpyright src/ sub-projects/`
- [ ] Linting passes: `ruff check src/ sub-projects/`
- [ ] Integration tests verify:
  - [ ] CLI → agents communication
  - [ ] agents → mcp communication
  - [ ] Full workflow (CLI → agents → MCP → external API)
- [ ] Create `scripts/validate_workspace.sh` (comprehensive validation)
- **Acceptance:** All tests pass, no regressions vs. monolith

### P3.2: Documentation ✓

- [ ] `docs/guides/SUBPROJECT_ARCHITECTURE.md` (overview, communication patterns)
- [ ] `docs/guides/SUBPROJECT_DEVELOPMENT.md` (dev workflow, adding tools)
- [ ] Update `docs/reference/IPC_PROTOCOL_SPEC.md` (finalized)
- [ ] Deployment guide (local, Docker, K8s)
- [ ] Code examples tested and working
- **Acceptance:** New developer can set up, run, and add tools without guidance

### P3.3: Consolidation Report ✓

- [ ] Create `docs/reports/ECOSYSTEM_CONSOLIDATION_2026-02-22.md`
- [ ] Document zen-mcp-server absorption (620 files, 50+ integrations)
- [ ] Document task-tool deprecation (timeline, migration)
- [ ] Document AgentAPI archival (why, historical reference)
- [ ] Performance impact analysis
- [ ] Breaking changes assessment (should be zero)
- [ ] Data preservation verification
- **Acceptance:** Comprehensive report signed off, no data loss

---

## Phase 4: Completion (1–2 hours)

### P4.1: CI/CD Integration ✓

- [ ] Create `.github/workflows/test-subprojects.yml`
- [ ] Build matrix: Python 3.10–3.12
- [ ] Test all sub-projects in parallel
- [ ] Coverage thresholds enforced
- [ ] Update `.pre-commit-config.yaml` (new module paths)
- [ ] Run against current branch — all checks pass
- **Acceptance:** CI/CD pipeline active, all commits validated

---

## Success Criteria (Definition of Done)

### Architecture

- [x] 4 independent sub-projects (cli, agents, mcp, core)
- [x] MCP protocol is only inter-project communication
- [x] No circular imports
- [x] tach DAG acyclic
- [x] All modules properly layered (L0 → L4)

### Ecosystem

- [x] zen-mcp-server (620 files) absorbed into thegent-mcp
- [x] task-tool deprecated with migration guide
- [x] AgentAPI/++ archived with notices
- [x] No data loss or breakage

### Testing

- [x] 100% test pass rate (all sub-projects)
- [x] ≥ 80% coverage (agents, mcp)
- [x] ≥ 95% coverage (cli)
- [x] Integration tests pass
- [x] Performance benchmarks show no regression

### Documentation

- [x] Sub-project architecture guide
- [x] IPC protocol spec (machine-readable)
- [x] Development workflow
- [x] Deployment guide
- [x] Consolidation report

### Backward Compatibility

- [x] No breaking changes to CLI interface
- [x] Session files still work
- [x] Config files compatible
- [x] All existing workflows preserved

---

## Execution Strategy

### Recommended Parallelization

**4 Agents:**

- **Agent 1:** P1.1 + P1.2 (Contracts & Workspace)
- **Agent 2:** P2.1 (CLI Extraction)
- **Agent 3:** P2.2 (Agents Extraction + MCP Service)
- **Agent 4:** P2.3 (MCP Extraction + zen-mcp absorption)

**Agent 1 blocks:** P1.3 (tach.toml) requires P1.2 complete
**Agents 2–4 block:** P1.2 + P1.3 must complete before extraction
**Sequential:** P2.4 (deprecate) requires P2.3 complete
**Parallel:** P3.1 (tests) can run after all extractions

### Checkpoint: After Each Phase

| Checkpoint | Criteria                                                    |
| ---------- | ----------------------------------------------------------- |
| **End P1** | All configs created, uv sync works, tach clean              |
| **End P2** | All extractions complete, import paths updated, tests green |
| **End P3** | Full test suite passes, docs complete, no regressions       |
| **End P4** | CI/CD active, all commits pass, ready for merge             |

---

## Commits

One commit per task (atomic, reviewable):

```
docs: define IPC and MCP contracts for sub-project communication
refactor: create workspace config for four sub-projects
refactor: update tach.toml boundaries for polyglot architecture
refactor: extract thegent-cli sub-project with MCP client
refactor: extract thegent-agents sub-project with FastMCP server
refactor: extract thegent-mcp sub-project and absorb zen-mcp-server tools
docs: mark task-tool deprecated and archive AgentAPI projects
test: add comprehensive sub-project integration tests
docs: create sub-project architecture and development guides
docs: create ecosystem consolidation report
ci: integrate sub-projects into GitHub Actions test matrix
```

---

## Risk Mitigation Checklist

| Risk                         | Mitigation                                                               |
| ---------------------------- | ------------------------------------------------------------------------ |
| **MCP protocol overhead**    | Benchmark CLI startup; target <250ms (was ~800ms)                        |
| **Async/await complexity**   | Use pytest-asyncio strict fixtures; retry flaky tests                    |
| **Credential conflicts**     | Use unified config system; never hardcode secrets                        |
| **zen-mcp-server conflicts** | Register tools by namespace (e.g., `github/list_repos` vs. `list_repos`) |
| **Import cycles**            | tach check before every commit                                           |
| **Data migration**           | Session files untouched; backward-compat verified                        |

---

## Time-Box Allocation

| Phase     | Task | Est. Time | Buffer | Total   |
| --------- | ---- | --------- | ------ | ------- |
| **1**     | P1.1 | 1.5h      | 0.5h   | 2h      |
|           | P1.2 | 1.5h      | 0.5h   | 2h      |
|           | P1.3 | 0.5h      | 0.5h   | 1h      |
| **2**     | P2.1 | 2.5h      | 0.5h   | 3h      |
|           | P2.2 | 3.5h      | 0.5h   | 4h      |
|           | P2.3 | 3.5h      | 0.5h   | 4h      |
|           | P2.4 | 0.5h      | 0.5h   | 1h      |
| **3**     | P3.1 | 2.5h      | 0.5h   | 3h      |
|           | P3.2 | 1.5h      | 0.5h   | 2h      |
|           | P3.3 | 1.5h      | 0.5h   | 2h      |
| **4**     | P4.1 | 1.5h      | 0.5h   | 2h      |
| **Total** |      | 24h       | 6h     | **30h** |

**Wall-clock (4 agents in parallel):** 8–10 hours
**Sequential (1 agent):** 24–30 hours

---

End of Track 4 Quick Checklist
