# Wave 82 Lane A Report (Items #51-#59)

## 1) Covered items table (issue id/title/status)

| Item | Issue               | Title                                                                                                | Status |
| ---- | ------------------- | ---------------------------------------------------------------------------------------------------- | ------ |
| #51  | CLIProxyAPI#797     | Bug: ModelStates (BackoffLevel) lost when auth is reloaded or refreshed                              | Open   |
| #52  | CLIProxyAPI#796     | Stream usage data is merged with finish_reason: "stop", causing Letta AI to crash                    | Open   |
| #53  | CLIProxyAPIPlus#72  | Claude Code WebSearch fails with 400 error when using Kiro/Amazon Q backend                          | Open   |
| #54  | CLIProxyAPIPlus#69  | Vision requests fail for ZAI (glm) and Copilot models with missing header / invalid parameter errors | Open   |
| #55  | CLIProxyAPI#729     | Antigravity Opus + Codex cannot read images                                                          | Open   |
| #56  | CLIProxyAPI#636     | Large prompt failures + Codex SSE missing response.completed                                         | Open   |
| #57  | CLIProxyAPIPlus#43  | Models from Codex (openai) are not accessible when Copilot is added                                  | Open   |
| #58  | CLIProxyAPIPlus#258 | Support `variant` parameter as fallback for `reasoning_effort` in codex models                       | Open   |
| #59  | CLIProxyAPI#1670    | Support image content in tool result messages (OpenAI ↔ Claude translation)                         | Open   |

## 2) thegent impact classification (direct/indirect/external)

| Item | Classification | Basis                                                                                                   |
| ---- | -------------- | ------------------------------------------------------------------------------------------------------- |
| #51  | Indirect       | Upstream auth state/backoff persistence affects reliability of proxied model selection and retries.     |
| #52  | Direct         | Stream event shape/ordering can break thegent-compatible OpenAI stream consumers.                       |
| #53  | Indirect       | WebSearch/tool-call translation bug in upstream provider path may surface in delegated tool flows.      |
| #54  | Direct         | Vision payload/header incompatibility directly impacts image-capable thegent routes.                    |
| #55  | Direct         | Image-read failure for Codex path is a first-order functional break for multimodal runs.                |
| #56  | Direct         | Missing `response.completed` and long-prompt handling are core protocol/streaming contract risks.       |
| #57  | Direct         | Provider/model routing conflict (Codex vs Copilot) directly impacts model availability in thegent.      |
| #58  | Indirect       | Parameter aliasing (`variant` vs `reasoning_effort`) is compatibility surface for codex model controls. |
| #59  | Direct         | Tool-result image content translation is required for multimodal tool outputs end-to-end.               |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

| Priority | Item(s)       | Local action                                                                                                                 | Touchpoints                                                                              |
| -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| P0       | #52, #56      | Add/expand stream-contract tests for usage chunk placement, finish events, and terminal `response.completed` invariants.     | `tests/` stream translation suites; stream adapter contract docs under `docs/reference/` |
| P0       | #54, #55, #59 | Add multimodal regression fixtures for image inputs and tool-result image outputs across OpenAI↔Claude translation.         | Multimodal translation tests in `tests/`; protocol notes in `docs/reference/`            |
| P0       | #57           | Add routing-conflict tests validating Codex model visibility when Copilot provider is enabled.                               | Provider routing tests in `tests/`                                                       |
| P1       | #51           | Add state-persistence regression test for backoff/model state across auth reload/refresh boundaries.                         | Auth/session state tests in `tests/`                                                     |
| P1       | #53           | Add tool/websearch translation test vectors for Kiro/Amazon Q path; verify 400 prevention in transformed payloads.           | Backend translation tests in `tests/`                                                    |
| P2       | #58           | Document codex reasoning parameter normalization policy and add compatibility test matrix (`reasoning_effort` vs `variant`). | Compatibility docs in `docs/reference/`; param normalization tests in `tests/`           |

## 4) Blockers/unknowns

- No per-issue repro artifacts are embedded in `WORK_STREAM_CLIPROXY_ALL.md`; root-cause signatures require upstream issue thread inspection.
- Ownership boundary limits this lane to reporting only; no code/test edits were performed in this pass.
- Exact internal module mapping for each upstream defect is unknown without correlating current thegent adapters against each protocol path.

## 5) Next 3 executable tasks for this lane

1. Build a minimal repro matrix for #52/#56/#54 using existing thegent proxy test harness inputs and expected stream/multimodal outputs.
2. Draft concrete test-case specs (names, fixtures, expected assertions) for #57/#55/#59 and map each to existing `tests/` suites.
3. Open a follow-up implementation checklist (P0 first) that binds each item to explicit file touchpoints and pass/fail criteria.
