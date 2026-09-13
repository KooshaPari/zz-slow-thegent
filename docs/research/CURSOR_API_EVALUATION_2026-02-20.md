<DONE>
# Cursor API Integration: Phase 2 Necessity Evaluation

**WL-061 — Research Output**
**Date:** 2026-02-20
**Author:** Agent (Claude Sonnet 4.6)
**Status:** Research complete

---

## Summary Recommendation

**Keep the `cursor-api` binary dependency (wisdgod/cursor-api). Do NOT implement WL-054 (native Python ConnectRPC client) at this time.**

Rationale: The `cursor-api` binary is actively maintained, ships pre-built static binaries for all target platforms (macOS x64/ARM, Linux x64/ARM, Windows x64/ARM), and thegent's `CursorApiRunner` (WL-018, already implemented) uses it correctly through a standard OpenAI-compatible HTTP interface. The native Python path (WL-054) would require implementing HTTP/2, ConnectRPC, and binary protobuf from scratch — high effort with no tangible benefit given the binary dep is already available and stable.

WL-054 should remain `pending` at P3 priority and only be revisited if a concrete need arises (e.g., CI environments where the binary cannot be installed, or the upstream project becomes unmaintained).

---

## 1. Current State: What the Binary Dependency Is and Where It Comes From

### 1.1 What `cursor-api` Is

`cursor-api` (github.com/wisdgod/cursor-api) is a self-hosted Rust HTTP server that reverse-engineers the Cursor IDE backend protocol and re-exposes it as an OpenAI-compatible API surface:

- `POST /v1/chat/completions` — chat completions (streaming + non-streaming)
- `GET /v1/models` — dynamic model list (~30 min cache)

It is NOT part of Cursor IDE. It is a third-party open-source project written by an independent developer.

### 1.2 How thegent Uses It

thegent's `CursorApiRunner` (`src/thegent/agents/cursor_api_runner.py`) does NOT invoke the `cursor-api` binary directly. Instead, it:

1. Checks if a `cursor-api` server instance is reachable at `THGENT_CURSOR_API_URL` (default `http://127.0.0.1:3000`) via `GET /v1/models`.
2. If reachable, delegates to `codex exec` with `OPENAI_BASE_URL` pointed at the cursor-api server and `OPENAI_API_KEY` set to the cursor token.
3. `codex` (the OpenAI Codex CLI) handles the actual HTTP communication to the cursor-api server.

So the dependency chain is:

```
thegent CursorApiRunner
  → codex CLI (required, already a thegent dep)
      → cursor-api server (user-run, separate process)
          → cursor.sh backend
```

The `CursorTokenProvider` and `CursorExecutorManager` (`src/thegent/routing/cursor_provider.py`) handle token file discovery and rotation — they read a token from `~/.cursor-server/session-token.txt` (or equivalent paths) and provide `Authorization: Bearer <token>` headers. This logic is already implemented as part of WL-018.

### 1.3 Authentication

The cursor-api server uses a `WorkosCursorSessionToken` cookie or a `/build-key` endpoint to obtain a `sk-...` bearer token. The user must run their own cursor-api instance and provide the token either via:

- `THGENT_CURSOR_API_TOKEN` environment variable, or
- A token file at one of the auto-discovered paths (`~/.cursor-server/session-token.txt`, `~/.cursor/session-token.txt`, `~/.config/cursor/session-token.txt`)

---

## 2. Platform Availability

### 2.1 cursor-api Binary Availability

As of 2026-02-20, the latest release is `v0.4.0-pre.23` (released 2026-02-20). Pre-built static binaries are available for all relevant platforms:

| Platform | Architecture          | Available                                                 |
| -------- | --------------------- | --------------------------------------------------------- |
| macOS    | x86_64                | Yes (`x86_64-darwin`, `x86_64-darwin-compat`)             |
| macOS    | ARM64 (Apple Silicon) | Yes (`aarch64-darwin`)                                    |
| Linux    | x86_64                | Yes                                                       |
| Linux    | ARM64                 | Yes (`aarch64-linux`, `aarch64-linux-compat`)             |
| Windows  | x86_64                | Yes (`x86_64-windows.exe`)                                |
| Windows  | ARM64                 | Yes (`aarch64-windows.exe`, `aarch64-windows-compat.exe`) |

All binaries use static linking (no libc or system library dependencies). SHA256 checksums are provided.

Note: Docker images were discontinued by the upstream maintainer. The binary releases replace Docker for self-hosted deployment.

### 2.2 CI/CD Availability

The cursor-api binary is NOT available in any public CI base image (GitHub Actions, CircleCI, etc.) because it requires live Cursor session tokens, which are personal credentials. This means:

- The `cursor-api` provider is inherently a local/user workstation feature, not a CI feature.
- CI pipelines should not use the `cursor-api` or `cursor-native` provider.
- This is the same constraint as all other Cursor-based providers (e.g., `cursor-agent`).

This is not a blocking limitation: no CI workflow should be using Cursor credentials.

### 2.3 Stability Assessment

The project has been in active development for approximately 10 months (as of the research date). The developer describes the current version as stable (`当前版本已稳定`). The release cadence is active (v0.4.0-pre.23 released the same day as this evaluation). The project has 624 GitHub stars.

Risks:

- The project is a reverse-engineered third-party tool. If Cursor changes its backend protocol, cursor-api may break until patched.
- The project is maintained by a single developer (community contributions exist).
- Version `v0.4.0-pre.23` carries a `pre` tag — pre-release versions may have instability.

Mitigations in thegent's current code:

- `_is_cursor_api_reachable()` checks availability before use and returns a clear error if the server is not running.
- The runner fails loudly (non-zero exit, descriptive stderr) rather than silently.
- Users are directed to start or configure cursor-api manually.

---

## 3. Alternative: Native Python Client (WL-054)

### 3.1 What WL-054 Would Require

The `eisbaw/cursor_api_demo` reference implementation uses:

- **HTTP/2** (`httpx` with `h2` backend or `httpx[http2]`)
- **ConnectRPC** (gRPC-Web protocol over HTTP/2 with binary protobuf)
- **Binary protobuf** — hand-encoded messages for `StreamUnifiedChatWithTools` RPC
- **SQLite token extraction** — reads `~/.config/Cursor/User/globalStorage/state.vscdb` on Linux, equivalent paths on macOS/Windows
- **Checksum computation** — Cursor's backend includes a proprietary checksum in requests

This is a significant reverse-engineering effort with ongoing maintenance burden. Any Cursor backend protocol change would require updating the native client.

### 3.2 Comparative Assessment

| Criterion                 | cursor-api (current, WL-018 done)    | Native Python (WL-054)       |
| ------------------------- | ------------------------------------ | ---------------------------- |
| Implementation effort     | Done (WL-018 complete)               | High (L — full day+)         |
| Maintenance burden        | Low (upstream maintains)             | High (own the fork)          |
| Platform availability     | Pre-built binaries for all platforms | No binary needed             |
| External process required | Yes (cursor-api server)              | No                           |
| Auth mechanism            | Bearer token (manual or file)        | SQLite auto-read             |
| OpenAI compat             | Yes (standard httpx calls via codex) | No (custom protocol)         |
| CI usability              | No (requires Cursor session)         | No (requires Cursor session) |
| Protocol stability        | Depends on cursor-api upstream       | Depends on Cursor backend    |
| Protobuf/gRPC required    | No                                   | Yes                          |

The native Python path provides one UX benefit: auto-reading the SQLite session token from Cursor IDE's local database, removing the need for the user to run a separate server. However:

- The token can already be sourced via the token file approach in `CursorTokenProvider`.
- The cursor-api server is a one-time self-hosted setup, not a per-invocation overhead.
- The protobuf/ConnectRPC stack is a significant complexity and maintenance liability.

---

## 4. Recommendation

### 4.1 Decision: Keep Binary Dependency, Defer WL-054

**Keep the current `cursor-api` server approach (WL-018 already implemented).**

The binary dependency is:

- Available on all relevant platforms as pre-built static binaries.
- Not bundled with Cursor IDE — users must install it separately (acceptable).
- Actively maintained with a recent release.
- Already correctly handled in thegent with fail-fast error messaging.

**WL-054 (native Python client) should remain deferred at P3** with the following trigger conditions for re-evaluation:

1. The wisdgod/cursor-api project becomes unmaintained or is abandoned.
2. A concrete operational requirement emerges to use Cursor in an environment where the binary cannot be installed.
3. Cursor significantly tightens access controls, making third-party proxy servers non-viable.

### 4.2 What Still Needs Doing: WL-018

The code infrastructure (`CursorTokenProvider`, `CursorExecutorManager`, `CursorApiRunner`) is already in place. WL-018 (`CLIProxy Cursor Phase 2: Native Token Provider and Refresh`) remains pending and covers the CLIProxy-side integration (adding `cursor:` schema, verifying the patch, updating config examples). That work is separate from this evaluation and is still needed.

---

## 5. Installation and Configuration Guide (for implementing agents)

This section documents how to configure the cursor-api dependency so another agent can implement WL-018's remaining items.

### 5.1 Installing cursor-api

Download the pre-built binary for the target platform from:

```
https://github.com/wisdgod/cursor-api/releases
```

Select the appropriate asset:

- macOS Intel: `x86_64-darwin`
- macOS Apple Silicon: `aarch64-darwin`
- Linux x64: `x86_64-linux`
- Linux ARM64: `aarch64-linux`
- Windows x64: `x86_64-windows.exe`

Make executable (`chmod +x` on macOS/Linux) and run.

### 5.2 Starting cursor-api

```sh
# Set the auth token (WorkosCursorSessionToken from browser cookies)
export AUTH_TOKEN=sk-your-cursor-token

# Start on default port 3000
./cursor-api

# Or with explicit port
PORT=3000 ./cursor-api
```

### 5.3 thegent Configuration

```sh
# Required: URL of the running cursor-api server
export THGENT_CURSOR_API_URL=http://127.0.0.1:3000

# Required: bearer token for cursor-api auth
export THGENT_CURSOR_API_TOKEN=sk-your-cursor-token

# Or configure via token file (auto-discovered)
echo "sk-your-cursor-token" > ~/.cursor-server/session-token.txt
```

### 5.4 Verifying the Integration

```sh
# Check cursor-api is reachable
curl http://127.0.0.1:3000/v1/models -H "Authorization: Bearer $THGENT_CURSOR_API_TOKEN"

# Run thegent via cursor-api provider
thegent run cursor-api "Hello, world"
```

---

## 6. Native Python Client: What to Implement (if WL-054 is ever activated)

If conditions change and WL-054 is unblocked, an implementing agent should:

1. **Auth**: Read SQLite from `~/.config/Cursor/User/globalStorage/state.vscdb`, extract `cursorAuth/accessToken` (or equivalent key). Use `aiosqlite` for async access.
2. **HTTP/2 client**: Use `httpx[http2]` — add `h2` as a dependency.
3. **ConnectRPC transport**: Implement binary protobuf framing for `StreamUnifiedChatWithTools` RPC at `https://api2.cursor.sh` or `https://agent.api5.cursor.sh`. Reference `eisbaw/cursor_api_demo` for message shapes.
4. **Proto definitions**: Reference `Jordan-Jarvis/cursor-grpc` for `.proto` files (`server_chat.proto`, `server_stream.proto`). Use `betterproto` or `grpcio-tools` to generate Python stubs.
5. **Checksum**: Cursor's backend validates a checksum field in requests. The `eisbaw/cursor_api_demo` `cursor_http2_client.py` contains the checksum computation logic.
6. **Provider registration**: Add `cursor-native` to the provider registry alongside `cursor-api`.
7. **Fail fast**: If SQLite file is not found, raise `RuntimeError` with clear instructions — do not silently fall back.

ConnectRPC endpoints to implement (minimum viable):

- `aiserver.v1.AiService/StreamUnifiedChatWithTools` — main chat stream
- (Optional) `aiserver.v1.AiService/GetModels` — model list

---

## References

- WL-018: `docs/reference/WORK_STREAM.md`
- WL-054: `docs/reference/WORK_STREAM.md`
- WL-061: `docs/reference/WORK_STREAM.md`
- Gap analysis item: `docs/GAP_ANALYSIS_AND_REMEDIATION.md` (section 6, G-CA-01)
- Existing research: `docs/plans/CURSOR_API_INTEGRATION_RESEARCH.md`
- Current binary dep impl: `src/thegent/agents/cursor_api_runner.py`
- Token/refresh impl: `src/thegent/routing/cursor_provider.py`
- wisdgod/cursor-api releases: https://github.com/wisdgod/cursor-api/releases (verified 2026-02-20)
- eisbaw/cursor_api_demo: https://github.com/eisbaw/cursor_api_demo
- Jordan-Jarvis/cursor-grpc: https://github.com/Jordan-Jarvis/cursor-grpc
