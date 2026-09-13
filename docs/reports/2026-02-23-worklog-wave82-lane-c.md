# Wave 82 Lane C Report (2026-02-23)

## 1) Covered items table (issue id/title/status)

| Item              | Issue               | Title                                                           | Status |
| ----------------- | ------------------- | --------------------------------------------------------------- | ------ |
| #69 (Feature #12) | CLIProxyAPI#1525    | support openai image generations api (`/v1/images/generations`) | open   |
| #70 (Feature #13) | CLIProxyAPIPlus#198 | Cursor CLI / Auth Support                                       | open   |
| #71 (Feature #14) | CLIProxyAPIPlus#179 | OpenAI-MLX-Server and vLLM-MLX support                          | open   |
| #72 (Feature #15) | CLIProxyAPIPlus#169 | Kimi Code support                                               | open   |
| #73 (Feature #16) | CLIProxyAPI#1384    | Support nested object parameter mapping in payload config       | open   |
| #74 (Feature #17) | CLIProxyAPI#1322    | Add `generateImages` endpoint support for Gemini API            | open   |
| #75 (Feature #18) | CLIProxyAPI#1084    | Add support for Text Embedding API (`/v1/embeddings`)           | open   |
| #76 (Feature #19) | CLIProxyAPIPlus#97  | ADD TRAE IDE support                                            | open   |
| #77 (Feature #20) | CLIProxyAPIPlus#94  | Add Veo video generation support                                | open   |

## 2) thegent impact classification (direct/indirect/external)

| Issue | Classification | Basis                                                                                                                             |
| ----- | -------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| #1525 | indirect       | Primary implementation is cliproxy endpoint support; thegent impact is capability detection, routing, and diagnostics.            |
| #198  | indirect       | Auth support is upstream, while thegent can add preflight checks and clearer auth-state reporting.                                |
| #179  | external       | MLX/vLLM backend support is provider/runtime-side and outside thegent code ownership.                                             |
| #169  | external       | New provider/model-family onboarding is upstream cliproxy/provider integration work.                                              |
| #1384 | direct         | Nested payload mapping can break local transform paths; thegent request shaping/parity tests can directly validate compatibility. |
| #1322 | indirect       | Gemini image endpoint support is upstream; thegent can verify route-level behavior and error surfacing.                           |
| #1084 | indirect       | Embeddings support is upstream API surface; thegent can add contract checks where embeddings are routed/blocked.                  |
| #97   | external       | IDE integration request is outside thegent runtime boundary except documentation of compatibility expectations.                   |
| #94   | external       | Veo video generation support is upstream media API expansion, not a thegent-local feature.                                        |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

| Priority | Action                                                                                                                              | Local touchpoints                                                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P0       | Add cliproxy transform parity tests for nested payload mappings (object nesting, deep key paths, failure-on-invalid map).           | `tests/test_unit_cliproxy_adapter.py`, `src/thegent/cliproxy_request_transform.py`, `src/thegent/cliproxy_adapter.py`                                            |
| P0       | Add capability-gate tests for image/embedding/video endpoint classes so unsupported routes fail loudly with deterministic messages. | `tests/routing/test_litellm_responses_handler.py`, `src/thegent/utils/routing_impl/litellm_responses_handler.py`, `src/thegent/utils/routing_impl/transforms.py` |
| P1       | Extend doctor/auth diagnostics for Cursor/CLI auth prerequisites and actionable remediation output.                                 | `src/thegent/doctor.py`, `src/thegent/agents/cliproxy_manager.py`, `tests/test_unit_cliproxy_manager.py`                                                         |
| P1       | Add integration matrix cases labeling upstream-only feature gaps vs local transform defects for features #12..#20.                  | `tests/integration/test_parity_legacy_vs_cliproxy_migration.py`, `tests/auth/test_parity_oauth_vs_cliproxy.py`                                                   |
| P2       | Add a short reference note linking items #69..#77 to local ownership boundaries (direct vs upstream).                               | `docs/reports/2026-02-23-worklog-wave82-lane-c.md`                                                                                                               |

## 4) Blockers/unknowns

- Work-stream entries are title-only and do not include payload examples, provider constraints, or acceptance criteria.
- For #179, #169, #97, and #94, no thegent-local implementation seam is specified; ownership appears upstream/external.
- For #1525, #1322, and #1084, endpoint semantics (request/response contract, streaming/non-streaming behavior, auth scopes) are unspecified.
- For #198, required auth flow details (token type, refresh path, storage expectations) are not provided.

## 5) Next 3 executable tasks for this lane

1. Add focused unit tests for nested payload mapping behavior (#1384) in cliproxy transform/adapter paths.
2. Add route capability-gate tests for image and embedding endpoint classes (#1525, #1322, #1084) with explicit fail-loud assertions.
3. Implement and test enhanced doctor/cliproxy-manager auth diagnostics for Cursor CLI auth readiness (#198).
