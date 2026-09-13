# Lane E Report - Wave 82 (Items #86-#93)

## 1) Covered items table (issue id/title/status)

| Global # | QOL # | Issue               | Title                                                                                | Status |
| -------- | ----: | ------------------- | ------------------------------------------------------------------------------------ | ------ |
| 86       |     7 | CLIProxyAPI#1655    | All credentials for model claude-sonnet-4-6 are cooling down                         | open   |
| 87       |     8 | CLIProxyAPI#1651    | Claude Sonnet 4.5 models are deprecated - please remove from panel                   | open   |
| 88       |     9 | CLIProxyAPI#1649    | Gemini API integration: incorrect renaming of `parameters` to `parametersJsonSchema` | open   |
| 89       |    10 | CLIProxyAPI#1637    | Google blocked my 3 email id at once                                                 | open   |
| 90       |    11 | CLIProxyAPI#1630    | Claude Sonnet 4.5 is no longer available. Please switch to Claude Sonnet 4.6.        | open   |
| 91       |    12 | CLIProxyAPIPlus#241 | context length for models registered from github-copilot should always be 128K       | open   |
| 92       |    13 | CLIProxyAPI#1621    | Question: applyClaudeHeaders() - how were these defaults chosen?                     | open   |
| 93       |    14 | CLIProxyAPI#1617    | Session-Aware Hybrid Routing Strategy                                                | open   |

## 2) thegent impact classification (direct/indirect/external)

| Issue               | Classification | Rationale                                                                                     |
| ------------------- | -------------- | --------------------------------------------------------------------------------------------- |
| CLIProxyAPI#1655    | indirect       | Upstream credential cooldown behavior affects reliability perceived by thegent users.         |
| CLIProxyAPI#1651    | indirect       | Deprecated model cleanup in provider panel impacts model selection validity downstream.       |
| CLIProxyAPI#1649    | direct         | Translator/schema mapping bug can break tool payloads in thegent-mediated flows.              |
| CLIProxyAPI#1637    | external       | Provider/account enforcement event; no local code fix in thegent alone.                       |
| CLIProxyAPI#1630    | indirect       | Model availability drift impacts defaults and docs used by thegent users.                     |
| CLIProxyAPIPlus#241 | direct         | Context length registration affects request shaping and truncation behavior in thegent paths. |
| CLIProxyAPI#1621    | indirect       | Header-default rationale/doc gap impacts operability and troubleshooting.                     |
| CLIProxyAPI#1617    | direct         | Routing strategy feature materially impacts session behavior thegent depends on.              |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

| Priority | Scope      | Action                                                                                                                                                        | Touchpoints                                             |
| -------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| P0       | tests      | Add regression tests for Gemini tool schema mapping to assert `parameters` is preserved where required and no invalid rename occurs.                          | translator tests around Gemini/OpenAI schema conversion |
| P0       | tests      | Add model registry tests enforcing Copilot-derived model context length = 128K where policy requires fixed max context.                                       | model registration + config normalization tests         |
| P1       | docs       | Add explicit support matrix for deprecated/unavailable Claude variants (4.5 vs 4.6) and expected fallback behavior (fail-fast messaging, no silent fallback). | model support reference docs, troubleshooting docs      |
| P1       | code       | Add startup/runtime validation warnings for deprecated model IDs in configured defaults and panel-fed selections.                                             | model validation path, config load validation           |
| P1       | docs       | Document `applyClaudeHeaders()` defaults with source/rationale and override guidance.                                                                         | auth/header reference docs                              |
| P2       | code+tests | Prototype session-aware hybrid routing policy flags behind explicit config and validate deterministic route selection in tests.                               | routing policy module + integration tests               |
| P2       | ops docs   | Add runbook note for provider cooldown/account blocks to classify as external incident vs code defect.                                                        | incident triage docs                                    |

## 4) Blockers/unknowns

- Exact ownership boundary between CLIProxyAPI and CLIProxyAPIPlus for implementing `#1617` routing semantics is not fully explicit.
- No confirmed canonical policy source for `applyClaudeHeaders()` default values in current references.
- Copilot 128K expectation (`#241`) needs confirmation against provider hard limits per model family.
- Account block/cooldown issues (`#1637`, partly `#1655`) may require provider-side evidence not available locally.

## 5) Next 3 executable tasks for this lane

1. Draft and land translator regression tests for `#1649` (schema mapping: `parameters` vs `parametersJsonSchema`) and run focused test target.
2. Add model context-length normalization test cases for Copilot registrations (`#241`) and update validation logic if mismatch is confirmed.
3. Write/update docs for deprecated Claude model handling + `applyClaudeHeaders()` defaults (`#1651`, `#1630`, `#1621`) with explicit operator guidance.
