# Wave-80 Rolling Replacement Lane AD Report (2026-02-23)

## Scope

- Owner lane: `AD`
- Target repo: `/Users/kooshapari/temp-PRODVERCEL/485/kush/cliproxyapi-plusplus`
- Requested batch: next 10 open cliproxy items
- Implemented batch: `CPB-0511..CPB-0520`

## Implemented Items

1. `CPB-0511` -> set to `implemented-wave80-lane-ad`
2. `CPB-0512` -> set to `implemented-wave80-lane-ad`
3. `CPB-0513` -> set to `implemented-wave80-lane-ad`
4. `CPB-0514` -> set to `implemented-wave80-lane-ad`
5. `CPB-0515` -> set to `implemented-wave80-lane-ad`
6. `CPB-0516` -> set to `implemented-wave80-lane-ad`
7. `CPB-0517` -> set to `implemented-wave80-lane-ad`
8. `CPB-0518` -> set to `implemented-wave80-lane-ad`
9. `CPB-0519` -> set to `implemented-wave80-lane-ad`
10. `CPB-0520` -> set to `implemented-wave80-lane-ad`

## Code Changes

- `pkg/llmproxy/executor/iflow_executor.go`
  - Added explicit `401 Unauthorized` classification for `auth_unavailable`/`no auth available` refresh failures.
- `pkg/llmproxy/executor/proxy_helpers.go`
  - Fixed proxy-aware HTTP client timeout caching semantics so per-call timeouts do not pollute cached base clients.
- `pkg/llmproxy/auth/codex/filename.go`
  - Fixed team filename generation when `hashAccountID` is missing to avoid malformed double-dash names and keep plan disambiguation.

## Test Coverage Added

- `pkg/llmproxy/executor/iflow_executor_test.go`
  - Added regression cases for `auth_unavailable -> 401` and `quota exhausted -> 429` classification.
- `pkg/llmproxy/executor/codex_executor_cpb0106_test.go`
  - Added execute + stream regression tests validating upstream stripping of unsupported `prompt_cache_retention`.
- `pkg/llmproxy/executor/proxy_helpers_test.go` (new)
  - Added timeout cache regression test.
  - Added transport sharing test for timeout wrappers.
  - Added auth-proxy-overrides-config-proxy precedence test.
- `pkg/llmproxy/auth/codex/filename_test.go`
  - Added team-without-hash filename regression test.
  - Added plus-vs-team disambiguation test.

## Planning/Tracking Updates

- Updated board statuses:
  - `docs/planning/CLIPROXYAPI_1000_ITEM_BOARD_2026-02-22.csv` (`CPB-0511..CPB-0520`)
  - `docs/planning/CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv` (matching issue refs `#903,#902,#897,#895,#893,#892,#891,#889,#887,#886`)
- Updated lane reports from `in_progress` to `implemented` with evidence:
  - `docs/planning/reports/issue-wave-cpb-0491-0540-lane-5.md`
  - `docs/planning/reports/issue-wave-cpb-0491-0540-lane-6.md`

## Verification Commands

- `go test ./pkg/llmproxy/executor -run 'TestClassifyIFlowRefreshError|TestNewProxyAwareHTTPClient|TestCodexExecutor_ExecuteStripsPromptCacheRetention|TestCodexExecutor_ExecuteStreamStripsPromptCacheRetention' -count=1`
- `go test ./pkg/llmproxy/auth/codex -run 'TestCredentialFileName_TeamWithoutHashAvoidsDoubleDash|TestCredentialFileName_PlusAndTeamAreDisambiguated|TestCredentialFileName|TestNormalizePlanTypeForFilename' -count=1`
- `rg -n '^CPB-051[1-9]|^CPB-0520' docs/planning/CLIPROXYAPI_1000_ITEM_BOARD_2026-02-22.csv`
- `rg -n 'issue#(903|902|897|895|893|892|891|889|887|886)' docs/planning/CLIPROXYAPI_2000_ITEM_EXECUTION_BOARD_2026-02-22.csv`

## Quality Gate

- Ran `task quality`.
- Result: failed due pre-existing unrelated repository issues outside Lane AD scope (e.g., unresolved symbols and redeclared tests in concurrently edited files).
- Lane AD scoped tests above pass.

## Commit Status

- No commits created (as requested).
