# Discovery Surface (G-DS)

**Purpose:** Document all discovery endpoints (CLI + MCP) for schema versions, contracts, and capabilities.
**Date:** 2026-02-14
**Scope:** G-DS-01 through G-DS-05

---

## 1. Single Source for Schema Versions: thegent://meta

**Endpoint:** MCP resource `thegent://meta`
**Implementation:** `get_server_meta_impl()` in `cli_impl.py`

| Field                           | Description                                        |
| ------------------------------- | -------------------------------------------------- |
| `route_schema_version`          | Route/catalog schema (integer, currently 1)        |
| `output_parser_schema_version`  | Output parser contract (e.g. "output-parser-v1")   |
| `contract_schema_version`       | CSM contract (e.g. "csm-v1")                       |
| `health_payload_schema_version` | Health payload schema                              |
| `health_payload_types`          | List of health payload types (gate, report, trend) |
| `health_policy_profiles`        | Available policy profiles                          |
| `operations`                    | Universal operation taxonomy                       |
| `orchestration_modes`           | Multi-agent modes                                  |
| `capabilities`                  | Server capabilities list                           |

**CLI equivalent:** `thegent meta` (if exposed) or via MCP only.

---

## 2. Contract Introspection

| Surface | Endpoint / Command                                      | Purpose                                                      |
| ------- | ------------------------------------------------------- | ------------------------------------------------------------ |
| MCP     | `thegent_list_models(include_contract=True)`            | Route contract with schema_version, routes (model→providers) |
| MCP     | `thegent_resolve_model_route(model, provider?, policy)` | Resolved route contract for a model                          |
| CLI     | `thegent session-contracts`                             | Session-level contract health                                |
| CLI     | `thegent models contract`                               | Catalog contract view                                        |

---

## 3. Health Payload Discovery

| Payload Type | Schema                        | Endpoint                                                                             |
| ------------ | ----------------------------- | ------------------------------------------------------------------------------------ |
| gate         | health_payload_schema_version | `thegent_session_contract_health_gate`, `thegent://sessions/contracts/health` (gate) |
| report       | health_payload_schema_version | `thegent_session_contract_health_report`, `thegent://sessions/contracts/report`      |
| trend        | health_payload_schema_version | `thegent_session_contract_health_trend`, `thegent://sessions/contracts/trend`        |

All health outputs include `schema_version` and `payload_type`.

---

## 4. Provider Capability Discovery (G-DS-04)

| Surface | Command / Tool                                      | Output                                                                    |
| ------- | --------------------------------------------------- | ------------------------------------------------------------------------- |
| CLI     | `thegent list-models`                               | by_provider: {provider: [model_ids]}                                      |
| CLI     | `thegent list-models --by-model`                    | by_model: model_id → [providers] (unified routing view)                   |
| MCP     | `thegent_list_models(provider?, include_contract?)` | With include_contract: routes (model→route details); without: by_provider |

**Verification:** `list-models --by-model` shows e.g. `gemini-3-flash: gemini, cursor-agent, antigravity`. MCP `thegent_list_models(include_contract=True)` returns `routes` with model_id → list of {provider, backend_type, model_alias, ...}.

---

## 5. MCP Resource Discovery

| Resource URI                                          | Purpose                                             |
| ----------------------------------------------------- | --------------------------------------------------- |
| `thegent://meta`                                      | Server metadata, schema versions, operations, modes |
| `thegent://sessions{?include_contract}`               | Session list                                        |
| `thegent://sessions/{id}`                             | Single session                                      |
| `thegent://sessions/contracts/health{?owner,all,...}` | Contract health gate                                |
| `thegent://sessions/contracts/report{?owner,all,...}` | Contract health report                              |
| `thegent://sessions/contracts/trend{?...}`            | Contract health trend                               |
| `thegent://models{?provider,include_contract}`        | Model catalog                                       |
| `thegent://dag{?cd}`                                  | DAG task list                                       |
| `thegent://operations{?operation}`                    | Operation taxonomy                                  |
| `thegent://modes{?mode}`                              | Orchestration modes                                 |

---

## 6. Health Route

| Endpoint  | Method | Response                                |
| --------- | ------ | --------------------------------------- |
| `/health` | GET    | `{"status": "ok", "server": "thegent"}` |

**Implementation:** `@mcp.custom_route("/health", methods=["GET"])` in `mcp_server.py`

---

## 7. Audit Summary

| G-DS    | Item                           | Status                                                                                          |
| ------- | ------------------------------ | ----------------------------------------------------------------------------------------------- |
| G-DS-01 | Schema discovery consolidation | Done — thegent://meta exposes route_schema_version, output_parser_schema_version, health schema |
| G-DS-02 | Contract introspection         | Done — models contract, resolve-model-route, session-contracts                                  |
| G-DS-03 | Health payload discovery       | Done — gate/report/trend have schema_version, payload_type                                      |
| G-DS-04 | Provider capability discovery  | Done — list-models --by-model, MCP include_contract with routes                                 |
| G-DS-05 | MCP resource discovery         | Done — thegent://meta, sessions, models, dag, operations, modes                                 |

---

## 8. References

- `src/thegent/cli_impl.py` — get_server_meta_impl
- `src/thegent/mcp_server.py` — resources, tools
- `docs/VERIFICATION_RUNBOOK.md` — manual verification checklist
