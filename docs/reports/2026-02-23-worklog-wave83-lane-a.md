# Wave 83 Lane A Report (Items #101-#109)

## 1) Covered items table (issue id/title/status)

| Global Item | QOL Item | Issue               | Title                                                                             | Status |
| ----------- | -------: | ------------------- | --------------------------------------------------------------------------------- | ------ |
| #101        |      #22 | CLIProxyAPI#1538    | Gemini-3-pro-high Corrupted thought signature                                     | Open   |
| #102        |      #23 | CLIProxyAPI#1531    | Invalid JSON payload received: Unknown name `deprecated`                          | Open   |
| #103        |      #24 | CLIProxyAPI#1526    | 反重力逻辑加载失效                                                                | Open   |
| #104        |      #25 | CLIProxyAPI#1509    | 反重力 claude-opus-4-6-thinking 模型如何通过 () 实现强行思考                      | Open   |
| #105        |      #26 | CLIProxyAPI#1493    | Feature request [allow to configure RPM, TPM, RPD, TPD]                           | Open   |
| #106        |      #27 | CLIProxyAPI#1486    | Antigravity Ultra plan: Opus 4.6 gets 429 on CLIProxy but runs with Opencode-Auth | Open   |
| #107        |      #28 | CLIProxyAPIPlus#200 | gemini能不能设置配额,自动禁用,自动启用?                                           | Open   |
| #108        |      #29 | CLIProxyAPI#1475    | [feat]更新很频繁,可以内置软件更新功能吗                                           | Open   |
| #109        |      #30 | CLIProxyAPIPlus#183 | why no kiro in dashboard                                                          | Open   |

## 2) thegent impact classification (direct/indirect/external)

| Global Item | Issue               | Classification | Basis                                                                                                      |
| ----------- | ------------------- | -------------- | ---------------------------------------------------------------------------------------------------------- |
| #101        | CLIProxyAPI#1538    | Indirect       | Provider translation integrity issue; affects reliability of proxied model behavior seen by thegent users. |
| #102        | CLIProxyAPI#1531    | Direct         | Payload schema incompatibility can break request flow initiated by thegent/Codex-style clients.            |
| #103        | CLIProxyAPI#1526    | External       | Antigravity internal loading behavior; no clear thegent-owned code path from issue text alone.             |
| #104        | CLIProxyAPI#1509    | External       | Usage/how-to request around forcing thinking mode; operational guidance, not a thegent runtime defect.     |
| #105        | CLIProxyAPI#1493    | External       | Rate-limit feature request in proxy platform; outside thegent code ownership.                              |
| #106        | CLIProxyAPI#1486    | Indirect       | 429 behavior impacts user outcomes in thegent via upstream proxy/account policy interactions.              |
| #107        | CLIProxyAPIPlus#200 | External       | Quota auto-disable/enable request targets proxy product controls, not thegent.                             |
| #108        | CLIProxyAPI#1475    | External       | Built-in updater request for upstream product; no direct thegent implementation requirement.               |
| #109        | CLIProxyAPIPlus#183 | External       | Dashboard product gap; unrelated to thegent runtime path.                                                  |

## 3) Proposed local actions (tests/docs/code touchpoints) with priority P0/P1/P2

- P0: Add/extend translator contract tests to hard-fail on unsupported/unknown schema fields (`deprecated`-like keys) in request payload transformations.
  Touchpoints: translator/normalization tests, fixture coverage for strict schema validation.
- P0: Add regression tests for 429 propagation and retry-hint handling surfaced to CLI users (ensure no silent fallback behavior).
  Touchpoints: streaming/error translation tests, retry metadata mapping assertions.
- P1: Document a lane-owned compatibility matrix for known upstream issue patterns (#1538/#1531/#1486) and expected user-visible behavior in thegent.
  Touchpoints: docs under governance/worklog references.
- P1: Add observability assertions in integration tests for payload rejection paths (explicit error codes/messages preserved end-to-end).
  Touchpoints: integration tests around provider adapter boundaries.
- P2: Triage ticket templates for external-only items to reduce churn (required repro fields, provider/account metadata, expected ownership labels).
  Touchpoints: issue triage docs/process notes.

## 4) Blockers/unknowns

- Unknown current parity between thegent translator tests and upstream schema changes that triggered #1531.
- Missing reproducible artifact for #1538 (exact input/response samples not included in work-stream index).
- No direct acceptance criteria in source for #1526/#1509/#1493/#1475/#183/#200 to convert into thegent code tasks.
- Upstream policy/config details for #1486 (Ultra plan limits, route policy, cooldown semantics) are not available in this document.

## 5) Next 3 executable tasks for this lane

1. Implement a failing regression test for unknown/unsupported payload fields (`deprecated`) at translator boundary; then patch normalizer/validator behavior to pass.
2. Implement a failing regression test for upstream 429 handling to verify retry metadata propagation and explicit user-facing error semantics.
3. Draft a compact compatibility/ownership note mapping items #101-#109 to `direct/indirect/external`, then link required evidence fields for future triage.
