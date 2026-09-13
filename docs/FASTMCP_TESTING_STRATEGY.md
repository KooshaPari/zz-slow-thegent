# FastMCP Testing Strategy (G-FM-05)

**Purpose:** Define unit, contract, integration, chaos, load, and timeout tests per MCP tool.
**Date:** 2026-02-14
**Source:** THGENT_FASTMCP_IMPLEMENTATION_PLAN §14.9

---

## 1. Test Pyramid

| Tier            | Target % | Purpose                                |
| --------------- | -------- | -------------------------------------- |
| **Unit**        | 70%      | Fast, isolated; mock external deps     |
| **Contract**    | —        | Adapter conformance, schema validation |
| **Integration** | 20%      | Real subprocess/CLI; MCP client calls  |
| **E2E**         | 10%      | Full flow; CLI + MCP parity            |

---

## 2. Current Coverage (by test file)

| File                           | Type        | Tools/Capabilities Covered                                                    |
| ------------------------------ | ----------- | ----------------------------------------------------------------------------- |
| `test_unit_mcp.py`             | Unit        | PERT DAG parse, MCP tool discovery                                            |
| `test_contract_conformance.py` | Contract    | Adapter normalization, provider outputs                                       |
| `test_e2e_cli.py`              | E2E         | run, bg, ps, status, logs, wait, stop, list-\*, dag, health gate/report/trend |
| `test_integration_agent.py`    | Integration | Agent execution with real runner                                              |
| `test_unit_contracts.py`       | Unit        | CSM, validation, registry                                                     |
| `test_unit_output_parser.py`   | Unit        | ParseResult, extract_condensed_validated                                      |
| `test_unit_execution.py`       | Unit        | RunRegistry, PolicyEngine                                                     |
| `test_resilience.py`           | Unit        | classify_failure, circuit breaker                                             |
| `test_ci_architecture.py`      | Unit        | Boundary checks                                                               |
| `scripts/verify-fastmcp.py`    | Manual      | thegent_run, thegent_bg, thegent_ps, resources                                |

---

## 3. Per-Tool Test Matrix

| Tool                | Unit    | Contract    | Integration | Timeout        | Load |
| ------------------- | ------- | ----------- | ----------- | -------------- | ---- |
| thegent_run         | ⚠      | ✓ (adapter) | ✓ (e2e)     | □              | □    |
| thegent_bg          | ⚠      | —           | ✓ (e2e)     | □              | □    |
| thegent_ps          | ✓ (e2e) | —           | ✓           | —              | □    |
| thegent_status      | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_logs        | ✓ (e2e) | —           | ✓           | □ (tail limit) | □    |
| thegent_wait        | ✓ (e2e) | —           | ✓           | □              | —    |
| thegent_stop        | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_list_agents | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_list_droids | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_list_models | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_dag_list    | ✓ (e2e) | —           | ✓           | —              | —    |
| thegent_inspect     | ✓ (e2e) | —           | ✓           | —              | —    |

Legend: ✓ Covered | ⚠ Partial | □ Gap

---

## 4. Test Categories (G-FM-05)

### 4.1 Unit Tests

- **run_impl / bg_impl:** Mock runner; assert payload shape, error handling.
- **Tool handlers:** Call MCP tool functions directly with mock ctx; assert ToolResult shape.
- **Contract normalization:** `test_contract_conformance.py` — per-provider raw → CSM.

### 4.2 Contract Tests

- **Adapter conformance:** `run_conformance_suite()` — XML, plain, malformed.
- **Drift alarm:** `--check-drift` in conformance; budget exceeded → fail.
- **Schema validation:** CSM status/phase invariants.

### 4.3 Integration Tests

- **MCP client:** `scripts/verify-fastmcp.py` — call tools via MCP transport.
- **CLI parity:** `test_e2e_cli.py` — CLI commands exit correctly.
- **Real agent:** `test_integration_agent.py` — optional, requires API key.

### 4.4 Chaos Tests (G-FM-05 Design)

**Fault injection scenarios:**

- Timeout mid-run: Mock runner sleeps > timeout; assert run returns timed_out=True, exit_code non-zero.
- Kill subprocess: Start bg run; kill child process; assert thegent_status shows failed/stopped.
- Corrupt session file: Write invalid JSON to session meta; assert thegent_status/logs degrade gracefully.
- Circuit breaker: Inject 6 failures for same provider; assert next run blocked until recovery_s.

**Recovery assertions:**

- Fallback: Primary adapter fails → fallback-plain CSM with confidence < 0.5.
- Circuit breaker half-open: After recovery_s, one trial allowed.

**Implementation:** `tests/test_chaos_mcp.py` — use `unittest.mock.patch` for runner, subprocess.

### 4.5 Load Tests (G-FM-05 Design)

**Scenarios:**

- 50 concurrent thegent_ps: Assert no deadlock; rate limit (10/s, burst 20) respected; p95 < 2s.
- thegent_list_models burst: 30 requests in 2s; assert cache hits after first; no OOM.
- ResponseLimitingMiddleware: thegent_logs with 600k chars; assert 413 or truncation.

**Implementation:** `tests/test_load_mcp.py` — `asyncio.gather` or `concurrent.futures`; optional `locust` for HTTP.

### 4.6 Timeout Tests (G-FM-05 Design)

**Scenarios:**

- thegent_run timeout: Mock runner with `time.sleep(timeout + 5)`; assert result has `timed_out=True`, exit_code != 0.
- thegent_wait timeout: Create session that never completes; wait with timeout=5; assert returns within 10s.
- thegent_logs tail: Generate 1M char log; assert ResponseLimitingMiddleware caps at 500k.

**Implementation:** `tests/test_unit_mcp.py` or `test_chaos_mcp.py`; use `pytest.mark.timeout(30)` for test itself.

---

## 5. Recommended Additions

| Priority | Test                                           | Location                                       | Effort |
| -------- | ---------------------------------------------- | ---------------------------------------------- | ------ |
| P1       | Unit: thegent_run/bg with mock runner          | test_unit_mcp.py or new test_unit_mcp_tools.py | S      |
| P1       | Timeout: run with slow mock                    | test_unit_mcp.py                               | S      |
| P2       | Chaos: kill subprocess mid-run                 | test_chaos_mcp.py (new)                        | M      |
| P2       | Chaos: circuit breaker 6 failures              | test_chaos_mcp.py                              | S      |
| P2       | Load: 50 concurrent thegent_ps                 | test_load_mcp.py (new)                         | M      |
| P2       | Load: ResponseLimitingMiddleware 600k          | test_load_mcp.py                               | S      |
| P3       | Integration: MCP tool call via CliRunner       | test_integration_mcp.py                        | M      |
| P3       | Timeout: thegent_wait never-completing session | test_chaos_mcp.py                              | S      |

---

## 6. Running Tests

```bash
# All tests
pytest tests/ -v

# Unit only
pytest tests/ -v -k "unit"

# Contract
pytest tests/test_contract_conformance.py -v

# E2E (no API keys)
pytest tests/test_e2e_cli.py -v

# MCP verification (manual, requires server)
python scripts/verify-fastmcp.py
```

---

## 7. References

- `docs/docset/PRD_TEST_PLAN_MATRIX.md` — full FR/NFR test matrix
- `docs/VERIFICATION_RUNBOOK.md` — manual verification checklist
- `docs/FASTMCP_PHASE_CHECKLIST_VERIFICATION.md` — phase checklist
