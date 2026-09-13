# Wave 82 Lane B Report (Sequential Items #60..#68 / Features #3..#11)

## 1) Covered items table (issue id/title/status)

| Seq | Feature # | Issue               | Title                                                                                   | Status |
| --- | --------: | ------------------- | --------------------------------------------------------------------------------------- | ------ |
| 60  |         3 | CLIProxyAPI#1665    | Concerns regarding the removal of Gemini Web support in the early stages of the project | open   |
| 61  |         4 | CLIProxyAPIPlus#253 | Codex support                                                                           | open   |
| 62  |         5 | CLIProxyAPIPlus#246 | fix(cline): add grantType to token refresh and extension headers                        | open   |
| 63  |         6 | CLIProxyAPIPlus#245 | fix(cline): add grantType to token refresh and extension headers                        | open   |
| 64  |         7 | CLIProxyAPI#1615    | Any Plans to support Jetbrains IDE?                                                     | open   |
| 65  |         8 | CLIProxyAPIPlus#232 | Add AMP auth as Kiro                                                                    | open   |
| 66  |         9 | CLIProxyAPI#1547    | [Claude code] ENABLE_TOOL_SEARCH - MCP not in available tools 400                       | open   |
| 67  |        10 | CLIProxyAPI#1540    | feat(thinking): support Claude output_config.effort parameter (Opus 4.6)                | open   |
| 68  |        11 | CLIProxyAPIPlus#213 | Add support for proxying models from kilocode CLI                                       | open   |

## 2) thegent impact classification (direct/indirect/external)

| Seq | Issue               | Classification | Basis                                                                                                    |
| --- | ------------------- | -------------- | -------------------------------------------------------------------------------------------------------- |
| 60  | CLIProxyAPI#1665    | external       | Product-direction item in upstream CLIProxyAPI; no explicit thegent module reference.                    |
| 61  | CLIProxyAPIPlus#253 | indirect       | Codex compatibility affects thegent runtime interoperability but primarily upstream proxy capability.    |
| 62  | CLIProxyAPIPlus#246 | indirect       | OAuth/token refresh header behavior can affect thegent integrations that rely on CLIProxyAPIPlus routes. |
| 63  | CLIProxyAPIPlus#245 | indirect       | Same as #246; duplicate subject area with potential parity drift risk.                                   |
| 64  | CLIProxyAPI#1615    | external       | IDE support request scoped to CLIProxyAPI product surface, not thegent core.                             |
| 65  | CLIProxyAPIPlus#232 | indirect       | Auth-provider support can impact thegent connector paths where AMP/Kiro auth is consumed.                |
| 66  | CLIProxyAPI#1547    | direct         | MCP tool-availability error maps to thegent MCP/runtime integration and command execution paths.         |
| 67  | CLIProxyAPI#1540    | indirect       | Thinking-effort translation affects model behavior consumed by thegent but implemented upstream.         |
| 68  | CLIProxyAPIPlus#213 | indirect       | New client/proxy support influences thegent compatibility matrix and docs, not immediate core code.      |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

| Priority | Area      | Action                                                                                                                                        | Touchpoints                                                          |
| -------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| P0       | tests     | Add/extend MCP integration tests for tool enumeration and `ENABLE_TOOL_SEARCH` pass-through; assert no `available tools 400` regression path. | `tests/`, `thegent/src/thegent/mcp/`, `thegent/src/thegent/runtime/` |
| P0       | code      | Audit request translation for tool-search flags and provider-specific capability negotiation in thegent MCP bridge.                           | `thegent/src/thegent/mcp/`, `thegent/src/thegent/connectors/`        |
| P1       | docs      | Update compatibility matrix for Codex, KiloCode CLI, JetBrains support status, and explicit ownership boundary (thegent vs CLIProxyAPI/Plus). | `docs/reference/`, `docs/guides/`                                    |
| P1       | tests     | Add OAuth refresh contract tests for required `grantType` propagation and extension headers in integration harness.                           | `tests/integration/`, `thegent/src/thegent/auth/`                    |
| P2       | code/docs | De-duplicate handling assumptions for duplicated upstream issues (#245/#246) and document canonical mapping in tracker.                       | `docs/reference/`, `docs/reports/`                                   |

## 4) Blockers/unknowns

- Sequential index mapping (`#60..#68`) is not encoded in `docs/reference/WORK_STREAM_CLIPROXY_ALL.md`; this report maps them to Features `#3..#11` per lane instructions.
- No linked reproduction artifacts (logs, payload samples, failing test IDs) are provided for issues #1547, #245, #246, #253, #213.
- Upstream ownership split between `CLIProxyAPI` and `CLIProxyAPIPlus` is not annotated with maintainer SLA or merge dependency order.
- Duplicate feature entries (#245 and #246) may represent one fix tracked twice; confirmation needed before implementation branching.

## 5) Next 3 executable tasks for this lane

1. Create failing integration test for Feature #9 / `CLIProxyAPI#1547` covering `ENABLE_TOOL_SEARCH` and MCP tool list translation.
2. Implement and validate `grantType` + extension header propagation checks in auth refresh integration tests for Features #5/#6.
3. Publish a concise compatibility note (Codex/KiloCode/JetBrains/AMP auth) in docs with explicit direct vs indirect thegent ownership tags.
