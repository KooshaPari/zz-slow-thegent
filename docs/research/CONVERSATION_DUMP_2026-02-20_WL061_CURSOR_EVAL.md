<DONE>
# Conversation Dump 2026-02-20 — WL-061 Cursor API Phase 2 Necessity Evaluation

## Issues Addressed

WL-061: Determine whether implementing a native Python ConnectRPC Cursor client (WL-054) is necessary, or whether the existing cursor-api binary dependency is acceptable.

## Research Performed

1. Read `docs/GAP_ANALYSIS_AND_REMEDIATION.md` section 6 (G-CA-01): confirms WL-054 is a P4 deferred item; binary dep acceptable for now.
2. Read `docs/plans/CURSOR_API_INTEGRATION_RESEARCH.md`: prior research covering 4 cursor-related repos; Phase 1 (cursor-api server) was recommended; Phase 2 (native Python) was marked optional/high-effort.
3. Read `src/thegent/agents/cursor_api_runner.py`: CursorApiRunner delegates to `codex exec` with `OPENAI_BASE_URL` pointed at a user-run cursor-api server — does NOT exec the cursor-api binary itself.
4. Read `src/thegent/routing/cursor_provider.py`: CursorTokenProvider reads `sk-...` token from disk (`~/.cursor-server/session-token.txt` etc.); CursorExecutorManager handles token rotation and httpx session rebinding.
5. Fetched `github.com/wisdgod/cursor-api/releases`: confirmed pre-built static binaries for macOS (x64, ARM64), Linux (x64, ARM64), Windows (x64, ARM64). Latest release v0.4.0-pre.23 dated 2026-02-20. Docker images discontinued; static binaries replace them.

## Decisions Made

**Keep binary dependency. Defer WL-054 to P3 with explicit trigger conditions.**

Rationale:

- WL-018 (CursorApiRunner + CursorTokenProvider) is already implemented.
- cursor-api binary is available on all relevant platforms as pre-built static binaries.
- Binary is NOT bundled with Cursor IDE; users must self-host — acceptable.
- Native Python path (WL-054) requires HTTP/2, ConnectRPC, binary protobuf, SQLite token extraction, and custom checksum computation — high effort and maintenance liability with no current operational need.
- cursor-api project is actively maintained (10 months, 624 stars, same-day release).

## Fixes Applied

None (research-only task).

## Documents Written

- `docs/research/CURSOR_API_EVALUATION_2026-02-20.md` — full evaluation with platform matrix, current state, native Python scope, installation guide, and WL-054 implementation outline.
- `docs/reference/WORK_STREAM.md` — WL-061 status updated from `research needed` to `research done` with one-line finding.

## Open Questions

- WL-018 (CLIProxy Phase 2 cursor: schema, patch, config examples) remains pending at P1. This evaluation does not block or change WL-018.
- If cursor-api's `pre` release tag resolves to a stable release, no action needed. If the project becomes unmaintained, revisit WL-054.

## Next Steps

- An agent picking up WL-018 can proceed directly using the install/config guide in `docs/research/CURSOR_API_EVALUATION_2026-02-20.md` section 5.
- WL-054 remains at P3. No action until trigger conditions in section 4.1 of the evaluation are met.
