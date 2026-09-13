# Wave 82 Lane F Report

## 1) Covered items table (issue id/title/status)

| Global # | QOL # | Issue               | Title                                                                                     | Status |
| -------- | ----: | ------------------- | ----------------------------------------------------------------------------------------- | ------ |
| 94       |    15 | CLIProxyAPI#1609    | fix: handle `response.function_call_arguments.done` in codex->claude streaming translator | open   |
| 95       |    16 | CLIProxyAPI#1586    | gemini-cli cannot set custom request headers                                              | open   |
| 96       |    17 | CLIProxyAPI#1580    | add one-click cleanup for invalid auth files                                              | open   |
| 97       |    18 | CLIProxyAPI#1564    | usability complaint / UX friction report                                                  | open   |
| 98       |    19 | CLIProxyAPIPlus#221 | Kiro account blocked                                                                      | open   |
| 99       |    20 | CLIProxyAPI#1548    | root cause request for cursor error                                                       | open   |
| 100      |    21 | CLIProxyAPIPlus#219 | Opus 4.6 issue report (insufficient title detail)                                         | open   |

## 2) thegent impact classification (direct/indirect/external)

| Issue               | Classification | Reason                                                                                            |
| ------------------- | -------------- | ------------------------------------------------------------------------------------------------- |
| CLIProxyAPI#1609    | direct         | Stream translator behavior can affect thegent CLI response handling parity.                       |
| CLIProxyAPI#1586    | indirect       | Header configurability impacts integration flexibility, not core thegent runtime path by default. |
| CLIProxyAPI#1580    | indirect       | Auth-file cleanup improves operability; mostly support/maintenance surface.                       |
| CLIProxyAPI#1564    | indirect       | Signals UX/documentation debt; no specific deterministic defect stated.                           |
| CLIProxyAPIPlus#221 | external       | Account enforcement/provider policy issue outside code-level control.                             |
| CLIProxyAPI#1548    | indirect       | Needs reproducible error signature before mapping to concrete thegent defect.                     |
| CLIProxyAPIPlus#219 | indirect       | Too vague; likely model/provider compatibility, not yet actionable as direct code bug.            |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

- P0: Add/expand streaming translator regression tests for `response.function_call_arguments.done` event handling.
  - Tests: translator stream fixtures covering argument chunk completion and downstream event ordering.
  - Code touchpoint: codex->claude stream translation path.
- P1: Add request-header capability note and explicit constraints for Gemini CLI routing.
  - Docs: operator-facing config docs for allowed custom headers and provider restrictions.
  - Tests: config validation tests for header passthrough/denylist.
- P1: Define auth-artifact maintenance command behavior for stale/invalid credentials cleanup.
  - Code touchpoint: auth management command surface.
  - Tests: dry-run + apply mode tests on mixed valid/invalid auth files.
- P2: Convert vague UX reports (#1564/#1548/#219) into reproducible issue templates.
  - Docs: issue template requiring client/version/model/trace snippet.
  - Tests: none until deterministic reproduction exists.
- P2: Annotate external-account lockout path (#221) in troubleshooting docs.
  - Docs: provider escalation path and expected error classification.

## 4) Blockers/unknowns

- #1548 and #219 lack concrete reproduction details (client version, request payload signature, exact error body).
- #1564 is a sentiment report without specific failing workflow.
- #221 is external policy/account state; no reliable local code fix path.
- #1586 needs confirmation whether limitation is in upstream gemini-cli, CLIProxyAPI routing policy, or both.

## 5) Next 3 executable tasks for this lane

1. Implement and run focused regression tests for #1609 stream argument completion handling.
2. Draft and apply a minimal issue-intake template update for #1548/#1564/#219 to force reproducible data.
3. Draft auth-cleanup command spec (inputs, dry-run behavior, safety checks) and map required unit tests for #1580.
