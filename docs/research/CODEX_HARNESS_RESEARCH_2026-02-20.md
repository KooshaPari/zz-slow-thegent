<DONE>
# Codex Harness Research — 2026-02-20

## Summary

This report is a dense technical synthesis of the OpenAI Codex ecosystem as it stands in February 2026, based on direct source analysis of the upstream `codex-upstream` repository at `/Users/kooshapari/temp-PRODVERCEL/485/API/codex-upstream/`, supplemented by live web research. It covers the full API surface, programmatic SDK, multi-modal inputs, app-server protocol, MCP server mode, IDE integration, and recommended overhaul approach for the thegent Codex harness.

---

## 1. Architecture Overview

Codex is a Rust binary (`codex-rs`) with a TypeScript CLI shim (`codex-cli`) and a TypeScript SDK (`sdk/typescript`). As of 2026, the architecture is organized as:

```
codex (binary, Rust)
├── codex-rs/app-server          ← App Server daemon (JSON-RPC 2.0 over stdio)
├── codex-rs/app-server-protocol ← Protocol schemas (v1 + v2, TypeScript + JSON exported)
├── codex-rs/mcp-server          ← MCP server mode (subset, stdio)
├── codex-rs/codex-api           ← Backend client (Responses API, Chat API, WebSocket)
├── codex-rs/responses-api-proxy ← Local HTTP proxy for Responses API (test tool)
├── codex-rs/exec                ← `codex exec` non-interactive subcommand
├── codex-rs/tui                 ← Terminal UI (Ratatui-based)
└── sdk/typescript               ← @openai/codex-sdk (Node.js 18+)
```

The App Server is the unified backend powering ALL surfaces: CLI, VS Code extension, JetBrains plugin, Xcode extension, macOS desktop app, web app, and Codex Cloud. It communicates over bidirectional JSON-RPC-like protocol (see section 3).

---

## 2. OpenAI Backend API: `/v1/responses`

The Codex backend exclusively uses the OpenAI **Responses API** (`/v1/responses`), NOT the Chat Completions API, except for legacy/compat fallback with non-OpenAI providers.

### 2.1 Responses API Request Shape (from `codex-rs/codex-api/src/requests/responses.rs`)

```rust
pub struct ResponsesApiRequest {
    model: &str,
    instructions: &str,
    input: &[ResponseItem],
    tools: &[Value],
    tool_choice: "auto",
    parallel_tool_calls: bool,
    reasoning: Option<Reasoning>,
    store: bool,
    stream: true,              // always streaming
    include: Vec<String>,
    prompt_cache_key: Option<String>,
    text: Option<TextControls>,  // structured output schema
}
```

Key parameters:

- `stream` is always `true`; Codex never uses non-streaming Responses API
- `store` is provider-dependent (true for Azure, false for direct OpenAI)
- `text.format` is set to `json_schema` with `strict: true` when `output_schema` is provided
- `reasoning` object carries `effort` and `summary` for o-series models
- `include` carries e.g. `"item.input_audio.transcript"` for audio modalities
- `tools` is a JSON array of tool definitions (apply_patch, exec, web_search, image_view, etc.)

### 2.2 Response Events (from `codex-rs/codex-api/src/common.rs`)

The SSE stream from `/v1/responses` surfaces these event types internally:

```rust
pub enum ResponseEvent {
    Created,
    OutputItemDone(ResponseItem),
    OutputItemAdded(ResponseItem),
    ServerReasoningIncluded(bool),    // X-Reasoning-Included header
    Completed { response_id, token_usage },
    OutputTextDelta(String),
    ReasoningSummaryDelta { delta, summary_index },
    ReasoningContentDelta { delta, content_index },
    ReasoningSummaryPartAdded { summary_index },
    RateLimits(RateLimitSnapshot),
    ModelsEtag(String),
}
```

### 2.3 WebSocket Responses API (from `codex-rs/codex-api/src/endpoint/responses_websocket.rs`)

There is a `ResponsesWebsocketClient` and `ResponsesWebsocketConnection` type, indicating support for `wss://` connections to the Responses API for Codex Cloud use cases. This is separate from standard HTTP SSE.

### 2.4 Internal Tool Definitions

Codex registers these tools with the Responses API (inferred from protocol and exec policy sources):

- `apply_patch` — file editing using unified diff format
- `container_exec` / `shell_exec` — command execution in sandbox
- `web_search` — live/cached web search
- `view_image` — multimodal image reading
- Dynamic tools from MCP servers (forwarded to the model as regular tool definitions)
- Dynamic tools from client (via `DynamicToolSpec` in `TurnStartParams`)

---

## 3. App Server Protocol (JSON-RPC 2.0 over stdio)

**Source**: `codex-rs/app-server-protocol/src/`

The App Server is spawned as a child process and communicates over stdin/stdout using newline-delimited JSON (JSONL). The protocol is _not_ strict JSON-RPC 2.0: the `"jsonrpc": "2.0"` field is omitted from the wire.

### 3.1 Wire Types

```
JSONRPCMessage = Request | Notification | Response | Error

JSONRPCRequest  = { id: RequestId, method: String, params?: Value }
JSONRPCNotification = { method: String, params?: Value }
JSONRPCResponse = { id: RequestId, result: Value }
JSONRPCError    = { id: RequestId, error: { code: i64, message: String, data?: Value } }

RequestId = String | Integer
```

### 3.2 Protocol Versioning: v1 (deprecated) vs v2 (current)

There are two protocol namespaces in the schema:

- **v1**: Original API (camelCase methods like `newConversation`, `sendUserTurn`, etc.) — kept for backward compat, actively deprecated
- **v2**: Current API (resource-path methods like `thread/start`, `turn/start`, etc.) — the correct target for all new integrations

**Rule**: All new thegent Codex harness code MUST use the v2 API. Do not call v1 methods.

### 3.3 Client Requests (client → server)

#### Thread Lifecycle (v2)

| Wire Method          | Params                   | Response                   | Notes                          |
| -------------------- | ------------------------ | -------------------------- | ------------------------------ |
| `thread/start`       | `ThreadStartParams`      | `ThreadStartResponse`      | Create new thread              |
| `thread/resume`      | `ThreadResumeParams`     | `ThreadResumeResponse`     | Resume by id, path, or history |
| `thread/fork`        | `ThreadForkParams`       | `ThreadForkResponse`       | Fork existing thread           |
| `thread/archive`     | `ThreadArchiveParams`    | `ThreadArchiveResponse`    | Archive thread                 |
| `thread/unarchive`   | `ThreadUnarchiveParams`  | `ThreadUnarchiveResponse`  | Unarchive thread               |
| `thread/name/set`    | `ThreadSetNameParams`    | `ThreadSetNameResponse`    | Rename thread                  |
| `thread/rollback`    | `ThreadRollbackParams`   | `ThreadRollbackResponse`   | Drop last N turns              |
| `thread/list`        | `ThreadListParams`       | `ThreadListResponse`       | Paginated list                 |
| `thread/loaded/list` | `ThreadLoadedListParams` | `ThreadLoadedListResponse` | In-memory threads              |
| `thread/read`        | `ThreadReadParams`       | `ThreadReadResponse`       | Read with optional turns       |

#### Turn Execution (v2)

| Wire Method      | Params                | Response                | Notes                 |
| ---------------- | --------------------- | ----------------------- | --------------------- |
| `turn/start`     | `TurnStartParams`     | `TurnStartResponse`     | Submit user input     |
| `turn/interrupt` | `TurnInterruptParams` | `TurnInterruptResponse` | Cancel in-flight turn |
| `review/start`   | `ReviewStartParams`   | `ReviewStartResponse`   | Code review turn      |

#### System/Config (v2)

| Wire Method               | Params                      | Response                         | Notes                    |
| ------------------------- | --------------------------- | -------------------------------- | ------------------------ |
| `model/list`              | `ModelListParams`           | `ModelListResponse`              | Paginated model list     |
| `collaborationMode/list`  | —                           | `CollaborationModeListResponse`  | Experimental             |
| `config/read`             | `ConfigReadParams`          | `ConfigReadResponse`             | Read layered config      |
| `config/value/write`      | `ConfigValueWriteParams`    | `ConfigWriteResponse`            | Write config key         |
| `config/batchWrite`       | `ConfigBatchWriteParams`    | `ConfigWriteResponse`            | Batch config write       |
| `configRequirements/read` | —                           | `ConfigRequirementsReadResponse` | MDM/managed requirements |
| `skills/list`             | `SkillsListParams`          | `SkillsListResponse`             | List SKILL.md files      |
| `skills/config/write`     | `SkillsConfigWriteParams`   | `SkillsConfigWriteResponse`      | Enable/disable skill     |
| `app/list`                | `AppsListParams`            | `AppsListResponse`               | App marketplace          |
| `mcpServerStatus/list`    | `ListMcpServerStatusParams` | `ListMcpServerStatusResponse`    | MCP server health        |
| `config/mcpServer/reload` | —                           | `McpServerRefreshResponse`       | Hot reload MCP config    |
| `mcpServer/oauth/login`   | `McpServerOauthLoginParams` | `McpServerOauthLoginResponse`    | MCP OAuth                |
| `command/exec`            | `CommandExecParams`         | `CommandExecResponse`            | One-off shell command    |

#### Account/Auth (v2)

| Wire Method               | Params                     | Response                       | Notes                                     |
| ------------------------- | -------------------------- | ------------------------------ | ----------------------------------------- |
| `account/login/start`     | `LoginAccountParams`       | `LoginAccountResponse`         | Login: apiKey, chatgpt, chatgptAuthTokens |
| `account/login/cancel`    | `CancelLoginAccountParams` | `CancelLoginAccountResponse`   | Cancel OAuth flow                         |
| `account/logout`          | —                          | `LogoutAccountResponse`        | Logout                                    |
| `account/read`            | `GetAccountParams`         | `GetAccountResponse`           | Get account info                          |
| `account/rateLimits/read` | —                          | `GetAccountRateLimitsResponse` | Rate limit snapshot                       |

#### Misc (v2)

| Wire Method       | Params                  | Response                  | Notes           |
| ----------------- | ----------------------- | ------------------------- | --------------- |
| `feedback/upload` | `FeedbackUploadParams`  | `FeedbackUploadResponse`  | Send feedback   |
| `fuzzyFileSearch` | `FuzzyFileSearchParams` | `FuzzyFileSearchResponse` | IDE file picker |

#### Init

| Wire Method       | Params             | Response             | Notes                     |
| ----------------- | ------------------ | -------------------- | ------------------------- |
| `initialize` (v1) | `InitializeParams` | `InitializeResponse` | Handshake; still required |

### 3.4 Server Requests (server → client, requires response)

| Wire Method                             | Params                                  | Response                                  | Notes                                               |
| --------------------------------------- | --------------------------------------- | ----------------------------------------- | --------------------------------------------------- |
| `item/commandExecution/requestApproval` | `CommandExecutionRequestApprovalParams` | `CommandExecutionRequestApprovalResponse` | Human-in-the-loop exec approval                     |
| `item/fileChange/requestApproval`       | `FileChangeRequestApprovalParams`       | `FileChangeRequestApprovalResponse`       | Human-in-the-loop patch approval                    |
| `item/tool/requestUserInput`            | `ToolRequestUserInputParams`            | `ToolRequestUserInputResponse`            | EXPERIMENTAL: user input elicitation                |
| `item/tool/call`                        | `DynamicToolCallParams`                 | `DynamicToolCallResponse`                 | Client-side dynamic tool execution                  |
| `account/chatgptAuthTokens/refresh`     | `ChatgptAuthTokensRefreshParams`        | `ChatgptAuthTokensRefreshResponse`        | For external-auth hosts (unstable, OpenAI-internal) |

### 3.5 Server Notifications (server → client, no response)

| Wire Method                                 | Payload                                   | Notes                       |
| ------------------------------------------- | ----------------------------------------- | --------------------------- |
| `error`                                     | `ErrorNotification`                       | Transient or fatal errors   |
| `thread/started`                            | `ThreadStartedNotification`               | Thread created              |
| `thread/name/updated`                       | `ThreadNameUpdatedNotification`           | Auto-name update            |
| `thread/tokenUsage/updated`                 | `ThreadTokenUsageUpdatedNotification`     | Per-turn token usage        |
| `turn/started`                              | `TurnStartedNotification`                 | Turn began                  |
| `turn/completed`                            | `TurnCompletedNotification`               | Turn finished               |
| `turn/diff/updated`                         | `TurnDiffUpdatedNotification`             | Unified diff update         |
| `turn/plan/updated`                         | `TurnPlanUpdatedNotification`             | Plan streaming update       |
| `item/started`                              | `ItemStartedNotification`                 | Item lifecycle started      |
| `item/completed`                            | `ItemCompletedNotification`               | Item lifecycle completed    |
| `rawResponseItem/completed`                 | `RawResponseItemCompletedNotification`    | Internal (Codex Cloud)      |
| `item/agentMessage/delta`                   | `AgentMessageDeltaNotification`           | Streaming text delta        |
| `item/plan/delta`                           | `PlanDeltaNotification`                   | EXPERIMENTAL plan streaming |
| `item/commandExecution/outputDelta`         | `CommandExecutionOutputDeltaNotification` | Streaming shell output      |
| `item/commandExecution/terminalInteraction` | `TerminalInteractionNotification`         | PTY interaction             |
| `item/fileChange/outputDelta`               | `FileChangeOutputDeltaNotification`       | Streaming patch delta       |
| `item/mcpToolCall/progress`                 | `McpToolCallProgressNotification`         | MCP tool progress           |
| `item/reasoning/summaryTextDelta`           | `ReasoningSummaryTextDeltaNotification`   | Reasoning summary stream    |
| `item/reasoning/summaryPartAdded`           | `ReasoningSummaryPartAddedNotification`   | Reasoning part              |
| `item/reasoning/textDelta`                  | `ReasoningTextDeltaNotification`          | Raw reasoning text          |
| `account/updated`                           | `AccountUpdatedNotification`              | Auth state changed          |
| `account/rateLimits/updated`                | `AccountRateLimitsUpdatedNotification`    | Rate limit change           |
| `account/login/completed`                   | `AccountLoginCompletedNotification`       | OAuth/login done            |
| `thread/compacted`                          | `ContextCompactedNotification`            | Deprecated; use item type   |
| `deprecationNotice`                         | `DeprecationNoticeNotification`           | API deprecation warning     |
| `configWarning`                             | `ConfigWarningNotification`               | Config parse warning        |
| `windows/worldWritableWarning`              | `WindowsWorldWritableWarningNotification` | Windows security warning    |

### 3.6 Client Notification (client → server)

| Wire Method   | Notes                            |
| ------------- | -------------------------------- |
| `initialized` | Sent after `initialize` response |

### 3.7 TurnStartParams — Key Fields

```rust
pub struct TurnStartParams {
    pub thread_id: String,
    pub input: Vec<UserInput>,        // see UserInput union below
    pub cwd: Option<PathBuf>,
    pub approval_policy: Option<AskForApproval>,  // untrusted | on-failure | on-request | never
    pub sandbox_policy: Option<SandboxPolicy>,
    pub model: Option<String>,
    pub effort: Option<ReasoningEffort>,          // minimal | low | medium | high | xhigh
    pub summary: Option<ReasoningSummary>,
    pub personality: Option<Personality>,
    pub output_schema: Option<JsonValue>,         // structured output
    pub collaboration_mode: Option<CollaborationMode>,  // EXPERIMENTAL
}
```

### 3.8 UserInput Union (v2)

```rust
pub enum UserInput {
    Text { text: String, text_elements: Vec<TextElement> },
    Image { url: String },
    LocalImage { path: PathBuf },
    Skill { name: String, path: PathBuf },    // SKILL.md invocation
    Mention { name: String, path: String },   // file mention
}
```

### 3.9 ThreadItem Union (v2 — what the agent produces)

```rust
pub enum ThreadItem {
    UserMessage { id, content: Vec<UserInput> },
    AgentMessage { id, text: String },
    Plan { id, text },                          // EXPERIMENTAL
    Reasoning { id, summary: Vec<String>, content: Vec<String> },
    CommandExecution { id, command, cwd, process_id, status, command_actions, aggregated_output, exit_code, duration_ms },
    FileChange { id, changes: Vec<FileUpdateChange>, status },
    McpToolCall { id, server, tool, status, arguments, result, error, duration_ms },
    CollabAgentToolCall { id, tool, status, sender_thread_id, receiver_thread_ids, prompt, agents_states },
    WebSearch { id, query, action },
    ImageView { id, path },
    EnteredReviewMode { id, review },
    ExitedReviewMode { id, review },
    ContextCompaction { id },
}
```

---

## 4. Programmatic TypeScript SDK (`@openai/codex-sdk`)

**Source**: `sdk/typescript/src/`
**Package**: `npm install @openai/codex-sdk`
**Requirements**: Node.js 18+

The SDK wraps the bundled `codex` binary by spawning `codex exec --experimental-json` as a subprocess and parsing JSONL output. It does NOT communicate via the app-server protocol — it uses the simpler `exec` mode event stream.

### 4.1 SDK Public API

```typescript
class Codex {
  constructor(options: CodexOptions = {});
  startThread(options: ThreadOptions = {}): Thread;
  resumeThread(id: string, options: ThreadOptions = {}): Thread;
}

class Thread {
  get id(): string | null;
  async run(input: Input, turnOptions: TurnOptions = {}): Promise<Turn>;
  async runStreamed(
    input: Input,
    turnOptions: TurnOptions = {},
  ): Promise<StreamedTurn>;
}

// Input types
type Input = string | UserInput[];
type UserInput =
  | { type: "text"; text: string }
  | { type: "local_image"; path: string };

// Turn result
type Turn = { items: ThreadItem[]; finalResponse: string; usage: Usage | null };
type StreamedTurn = { events: AsyncGenerator<ThreadEvent> };

// Options
type CodexOptions = {
  codexPathOverride?: string;
  env?: Record<string, string>;
  config?: CodexConfigObject; // flattened to --config key=val flags
  baseUrl?: string;
  apiKey?: string;
};

type ThreadOptions = {
  model?: string;
  sandboxMode?: "read-only" | "workspace-write" | "danger-full-access";
  workingDirectory?: string;
  skipGitRepoCheck?: boolean;
  modelReasoningEffort?: "minimal" | "low" | "medium" | "high" | "xhigh";
  networkAccessEnabled?: boolean;
  webSearchMode?: "disabled" | "cached" | "live";
  webSearchEnabled?: boolean;
  approvalPolicy?: "never" | "on-request" | "on-failure" | "untrusted";
  additionalDirectories?: string[];
};

type TurnOptions = {
  outputSchema?: object; // JSON Schema for structured output
  signal?: AbortSignal; // for cancellation
};
```

### 4.2 SDK Event Types (exec JSONL stream)

```typescript
type ThreadEvent =
  | { type: "thread.started"; thread_id: string }
  | { type: "turn.started" }
  | { type: "turn.completed"; usage: Usage }
  | { type: "turn.failed"; error: ThreadError }
  | { type: "item.started"; item: ThreadItem }
  | { type: "item.updated"; item: ThreadItem }
  | { type: "item.completed"; item: ThreadItem }
  | { type: "error"; message: string };
```

### 4.3 SDK ThreadItem Types

```typescript
type ThreadItem =
  | AgentMessageItem // { type: "agent_message"; id; text }
  | ReasoningItem // { type: "reasoning"; id; text }
  | CommandExecutionItem // { type: "command_execution"; id; command; aggregated_output; exit_code; status }
  | FileChangeItem // { type: "file_change"; id; changes; status }
  | McpToolCallItem // { type: "mcp_tool_call"; id; server; tool; arguments; result?; error?; status }
  | WebSearchItem // { type: "web_search"; id; query }
  | TodoListItem // { type: "todo_list"; id; items }
  | ErrorItem; // { type: "error"; id; message }
```

### 4.4 How the SDK Invokes the Binary

The SDK calls:

```bash
codex exec --experimental-json \
    [--config key=val]... \
    [--model MODEL] \
    [--sandbox MODE] \
    [--cd DIR] \
    [--add-dir DIR]... \
    [--skip-git-repo-check] \
    [--output-schema FILE] \
    [--image FILE]... \
    [resume THREAD_ID]
```

Prompt is piped to stdin. Output is JSONL on stdout.

The SDK sets `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=codex_sdk_ts` for telemetry differentiation.

---

## 5. MCP Server Mode

**Source**: `codex-rs/mcp-server/src/`

When started with `codex mcp server` (or via the `--mcp-server` flag), Codex runs as a standard MCP server over stdio (JSON-RPC, newline-delimited). It exposes exactly **two tools**:

### 5.1 Tool: `codex`

Starts a new Codex session.

```json
{
  "name": "codex",
  "description": "Run a Codex session. Accepts configuration parameters matching the Codex Config struct.",
  "inputSchema": {
    "type": "object",
    "required": ["prompt"],
    "properties": {
      "prompt": {
        "type": "string",
        "description": "The initial user prompt to start the Codex conversation."
      },
      "model": { "type": "string" },
      "profile": { "type": "string" },
      "cwd": { "type": "string" },
      "approval-policy": {
        "type": "string",
        "enum": ["untrusted", "on-failure", "on-request", "never"]
      },
      "sandbox": {
        "type": "string",
        "enum": ["read-only", "workspace-write", "danger-full-access"]
      },
      "config": { "type": "object", "additionalProperties": true },
      "base-instructions": { "type": "string" },
      "developer-instructions": { "type": "string" },
      "compact-prompt": { "type": "string" }
    }
  },
  "outputSchema": {
    "type": "object",
    "required": ["threadId", "content"],
    "properties": {
      "threadId": { "type": "string" },
      "content": { "type": "string" }
    }
  }
}
```

### 5.2 Tool: `codex-reply`

Continues an existing Codex session.

```json
{
  "name": "codex-reply",
  "description": "Continue a Codex conversation by providing the thread id and prompt.",
  "inputSchema": {
    "type": "object",
    "required": ["prompt"],
    "properties": {
      "threadId": { "type": "string" },
      "conversationId": {
        "type": "string",
        "description": "DEPRECATED: use threadId instead."
      },
      "prompt": { "type": "string" }
    }
  }
}
```

### 5.3 MCP Server Notes

- The MCP server is a "prototype" (denoted by `//! Prototype MCP server.`)
- It does NOT support approval flows, streaming, or fine-grained event observation
- The full App Server is recommended for any serious integration
- OpenAI explicitly rejected MCP as the primary protocol: "maintaining MCP semantics proved difficult" because MCP's tool-oriented design couldn't support streaming diffs, approval flows, and thread persistence
- The MCP server internally uses `SessionSource::Mcp` which maps to `SessionSource::AppServer` in v2

---

## 6. CLI Subcommands and Flags

### 6.1 Primary Subcommands

| Command            | Description                        |
| ------------------ | ---------------------------------- |
| `codex`            | Interactive TUI                    |
| `codex exec`       | Non-interactive (alias: `codex e`) |
| `codex app`        | Launch macOS desktop app           |
| `codex apply`      | Apply cloud task diffs             |
| `codex cloud`      | Cloud task interaction             |
| `codex completion` | Shell completions                  |
| `codex execpolicy` | Evaluate policy rule files         |
| `codex features`   | Manage feature flags               |
| `codex fork`       | Fork previous session              |
| `codex login`      | Authenticate                       |
| `codex logout`     | Remove credentials                 |
| `codex mcp`        | MCP server management              |
| `codex resume`     | Continue previous session          |
| `codex sandbox`    | Run commands under sandbox         |

### 6.2 Key Global Flags

| Flag                                         | Values                                                 | Purpose                      |
| -------------------------------------------- | ------------------------------------------------------ | ---------------------------- |
| `--model, -m`                                | string                                                 | Override model               |
| `--sandbox, -s`                              | `read-only` / `workspace-write` / `danger-full-access` | Sandbox policy               |
| `--ask-for-approval, -a`                     | `untrusted` / `on-request` / `never`                   | Approval policy              |
| `--cd, -C`                                   | path                                                   | Working directory            |
| `--add-dir`                                  | path                                                   | Additional writable dir      |
| `--config, -c`                               | `key=value`                                            | Config override (TOML)       |
| `--profile, -p`                              | string                                                 | Config profile               |
| `--image, -i`                                | path(s)                                                | Attach images                |
| `--full-auto`                                | bool                                                   | Low-friction workspace-write |
| `--dangerously-bypass-approvals-and-sandbox` | —                                                      | No approvals, no sandbox     |
| `--oss`                                      | —                                                      | Use local/OSS model provider |
| `--search`                                   | —                                                      | Enable live web search       |

### 6.3 Exec-Specific Flags

| Flag                        | Values                      | Purpose                               |
| --------------------------- | --------------------------- | ------------------------------------- |
| `--experimental-json`       | —                           | JSONL event output (required for SDK) |
| `--ephemeral`               | —                           | Skip session persistence              |
| `--output-schema`           | path                        | JSON Schema for structured output     |
| `--skip-git-repo-check`     | —                           | Allow running outside git repos       |
| `--output-last-message, -o` | path                        | Write final message to file           |
| `--color`                   | `always` / `never` / `auto` | ANSI output                           |

---

## 7. Input/Output Modalities

### 7.1 Text Input

- Plain string prompt via stdin (exec mode) or `UserInput::Text` (app-server)
- Supports `text_elements` spans for IDE-side annotations (file mentions, skill references)
- Skill invocations: `UserInput::Skill { name, path }` triggers SKILL.md execution

### 7.2 Image Input

- `--image path` CLI flag (one or more)
- `UserInput::LocalImage { path }` in app-server
- `UserInput::Image { url: String }` in app-server (remote URL)
- SDK: `{ type: "local_image", path }` in input array
- Images are passed to the model as multimodal content items

### 7.3 Structured Output (JSON Schema)

- `--output-schema <json-schema-file>` in exec mode
- `output_schema: Option<JsonValue>` in `TurnStartParams`
- `outputSchema` in SDK `TurnOptions`
- Translated to `text.format = { type: "json_schema", strict: true, schema: ... }` in Responses API request

### 7.4 Web Search

- Config: `web_search = "disabled" | "cached" | "live"`
- Legacy: `features.web_search_request = true/false`
- Tool registered as `web_search` with model

### 7.5 Reasoning Control

- `model_reasoning_effort`: `minimal | low | medium | high | xhigh`
- `model_reasoning_summary`: controls summary verbosity
- `model_verbosity`: controls output verbosity
- Maps to `reasoning: { effort, summary }` in Responses API

### 7.6 Computer Use / Operator Mode

Codex does NOT have a dedicated "computer-use" or CUA modality in the current source. There is no `computer_use` tool in the protocol. The "operator" positioning is marketing terminology — Codex operates on files and shell. The `collaboration_mode` experimental field in `TurnStartParams` is a preset that combines model, reasoning effort, and developer instructions but is not computer-use.

---

## 8. Dynamic Tools (Client-Side Tool Registration)

The v2 protocol allows clients to register custom tools that the model can call, with execution delegated back to the client:

### 8.1 Registration (in `ThreadStartParams`)

```rust
pub dynamic_tools: Option<Vec<DynamicToolSpec>>,
// where DynamicToolSpec = { name, description, input_schema: JsonValue }
```

### 8.2 Server Request: `item/tool/call`

When the model invokes a dynamic tool, the server sends:

```json
{
    "method": "item/tool/call",
    "id": 42,
    "params": {
        "callId": "call-xyz",
        "name": "my_tool",
        "arguments": { ... }
    }
}
```

Client must respond with:

```json
{
  "id": 42,
  "result": {
    "output": "tool result text",
    "success": true
  }
}
```

This is how IDE extensions implement IDE-specific tools (e.g., file picker, diagnostics, LSP actions) that Codex can invoke.

---

## 9. MCP Server Integration (Codex as MCP Client)

Codex can also _consume_ MCP servers as a client. The `config/mcpServer/reload` endpoint and `mcpServerStatus/list` endpoint reflect this. When MCP servers are configured, their tools are forwarded to the model as regular tool definitions. Results flow back through `McpToolCall` items in the event stream.

The v2 `ListMcpServerStatusResponse` includes per-server status with:

- `name`: server name
- `tools`: tool definitions (MCP Tool schema)
- `resources`, `resource_templates`: MCP resource definitions
- `auth_status`: `Unsupported | NotLoggedIn | BearerToken | OAuth`

---

## 10. IDE Integration Architecture

### 10.1 VS Code Extension

- Bundles platform-specific `codex` binary as a vendored asset
- Spawns the App Server as a child process on extension activation
- Communicates via the bidirectional JSON-RPC protocol (section 3)
- Session source: `SessionSource::VsCode`
- Supports Cursor, Windsurf (VS Code forks) automatically

### 10.2 JetBrains / Xcode

- "Decoupled partners" model: these IDEs maintain stable clients but point to newer server versions
- Clients implement the app-server protocol; binaries are updated separately
- This is the recommended pattern for third-party harnesses

### 10.3 Web App / Codex Cloud

- Browser communicates via HTTP/SSE with containerized App Server instances
- The App Server binary is the same crate; a different transport (HTTP instead of stdio) wraps it
- The `experimental_raw_events` flag in `ThreadStartParams` is for Codex Cloud internal use

### 10.4 Authentication Modes for IDE Hosts

Three auth modes exist:

1. **`apiKey`**: API key stored by Codex directly
2. **`chatgpt`**: OAuth managed by Codex (token refresh handled internally)
3. **`chatgptAuthTokens`** (UNSTABLE, OpenAI-internal): Tokens supplied by host app, not stored; server sends `account/chatgptAuthTokens/refresh` requests when tokens expire. For Codex app/web only.

---

## 11. Configuration System

### 11.1 Config Layers (precedence low → high)

1. MDM (macOS managed preferences, domain: `com.openai.codex`)
2. System (`managed_config.toml`)
3. User (`~/.codex/config.toml` or `$CODEX_HOME/config.toml`)
4. Project (`.codex/config.toml` files from CWD up to repo root, can be multiple)
5. Session flags (`-c key=value` CLI overrides)
6. Legacy `managed_config.toml` from MDM (being phased out)

### 11.2 Key Config Fields (v2 Config struct)

```toml
model = "gpt-5.1-codex-max"
review_model = "..."
model_provider = "openai"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "live"     # disabled | cached | live
model_reasoning_effort = "high"
model_reasoning_summary = "..."
model_verbosity = "..."
instructions = "..."
developer_instructions = "..."
compact_prompt = "..."

[sandbox_workspace_write]
writable_roots = ["/path1"]
network_access = false
exclude_tmpdir_env_var = false
exclude_slash_tmp = false

[profiles.fast]
model = "gpt-5.1"
approval_policy = "never"
```

### 11.3 Requirements (enterprise MDM enforcement)

`configRequirements/read` returns `ConfigRequirements`:

- `allowed_approval_policies`: restrict which approval policies users can set
- `allowed_sandbox_modes`: restrict sandbox modes
- `enforce_residency`: `"us"` for data residency enforcement

---

## 12. Codex Exec Mode (`codex exec --experimental-json`)

The exec subcommand is a simpler non-interactive mode used by the TypeScript SDK. It:

1. Reads prompt from stdin
2. Starts a session (new or resumed via `resume THREAD_ID`)
3. Emits JSONL events to stdout
4. Exits with code 0 on success, non-zero on failure

This mode is separate from the app-server and has a simpler event model. It does not support approval flows in non-interactive contexts (uses the configured `approval_policy`).

The `--experimental-json` flag is REQUIRED for machine-parseable output. Without it, output is TUI/ANSI.

---

## 13. Skills System

Codex has a SKILL.md/SKILL.json system for reusable agent instructions:

- Skills are discovered from `.codex/skills/` directories up the directory tree
- Scopes: `user`, `repo`, `system`, `admin`
- Each skill has: `name`, `description`, `interface` (display_name, short_description, icon, brand_color, default_prompt), `dependencies` (tool deps)
- Skills are invoked via `UserInput::Skill { name, path }` in turn input
- `skills/list` returns skills per CWD
- `skills/config/write` enables/disables skills per path

---

## 14. Thread Rollout / Persistence

- All sessions are recorded as "rollout files" in `$CODEX_HOME/sessions/`
- Sessions persist the full event log
- `Thread.rollout_path` carries the path
- Resume can be done by `thread_id`, by `path`, or by `history` (in-memory)
- Fork creates a new thread from an existing rollout
- Rollback drops N turns from the end of the history (does NOT revert file changes — client responsible)

---

## 15. What's New in Codex v2 Protocol (0.104+)

Based on source analysis and web research, these are new/changed since the v1 protocol:

1. **v2 thread API**: `thread/start`, `thread/resume`, etc. replacing `newConversation`, `sendUserTurn`
2. **Structured notifications**: per-thread and per-turn notifications with full `Thread`/`Turn` objects
3. **TurnDiffUpdated**: aggregate unified diff streamed in real-time during turn
4. **CollabAgentToolCall**: multi-agent collaboration item type (spawn/send/wait/close agents)
5. **Thread rollback**: drop N turns without reverting files
6. **Thread archive/unarchive**: with server-sent notifications to clients
7. **ThreadNameUpdated**: auto-naming based on first message
8. **TokenUsage tracking**: per-thread total + per-turn last, with model context window
9. **Personality**: `Personality` enum passed to thread start/turn
10. **CollaborationMode presets**: experimental preset that bundles model + effort + developer instructions
11. **Dynamic tools**: client-registered tools the model can invoke
12. **Skills system**: SKILL.md/SKILL.json files discoverable per-CWD
13. **ContextCompaction item**: replaces deprecated `thread/compacted` notification
14. **ExecPolicyAmendment**: user can accept command AND amend execpolicy permanently
15. **ReviewStart**: dedicated review mode (uncommitted changes, base branch diff, commit diff, custom)
16. **Config system overhaul**: layered config with origins/layers tracking, batch writes, requirements

---

## 16. Gaps vs Claude Code, Gemini CLI, Ante

### 16.1 Feature Parity Matrix

| Feature                       | Codex                                  | Claude Code     | Gemini CLI | Ante (thegent) |
| ----------------------------- | -------------------------------------- | --------------- | ---------- | -------------- |
| Streaming agent output        | Yes (SSE + app-server)                 | Yes             | Yes        | Via harness    |
| Structured JSON output        | Yes (`output_schema`)                  | Yes             | Yes        | Via harness    |
| Image input                   | Yes (local + URL)                      | Yes             | Yes        | Partial        |
| Web search                    | Yes (native tool)                      | Yes             | Yes        | Via MCP        |
| Programmatic SDK              | Yes (`@openai/codex-sdk`)              | No (CLI only)   | No         | Via CLI        |
| Multi-agent collab            | Yes (`CollabAgentToolCall`)            | No              | No         | Planned        |
| App-server embedding protocol | Yes (JSON-RPC stdio)                   | No              | No         | Partial        |
| MCP client                    | Yes                                    | Yes             | Yes        | Yes            |
| MCP server                    | Yes (2 tools)                          | No              | No         | Yes (full)     |
| Thread persistence/rollback   | Yes                                    | Yes             | Limited    | Limited        |
| Skills/extensions             | Yes (SKILL.md)                         | Yes (CLAUDE.md) | No         | Yes (skills)   |
| Dynamic client tools          | Yes                                    | No              | No         | No             |
| Code review mode              | Yes (`review/start`)                   | No              | No         | No             |
| Config layer system           | Yes (MDM + system + user + project)    | Limited         | Limited    | Partial        |
| Model reasoning control       | Yes (effort + summary + verbosity)     | Yes             | No         | Via config     |
| Context compaction            | Yes (automated)                        | Yes             | No         | Via harness    |
| Approval flows                | Yes (per-command, per-file)            | Yes             | No         | Via hooks      |
| Sandbox modes                 | Yes (read-only, workspace-write, full) | Limited         | No         | Via OS         |

### 16.2 Key Gaps in thegent's Codex Harness

1. **No app-server protocol client**: thegent talks to Codex via CLI flags, not the app-server JSON-RPC protocol. This means no streaming, no approval flows, no dynamic tools.
2. **No thread persistence integration**: thegent does not resume/fork Codex threads
3. **No structured output forwarding**: `output_schema` is not passed through
4. **No image input forwarding**: `--image` not supported
5. **No reasoning control**: effort/summary/verbosity not configurable
6. **No multi-agent support**: `CollabAgentToolCall` is not observed
7. **Provider routing**: Codex only supports OpenAI/Azure natively; no routing to other providers without a proxy

---

## 17. Overhaul Approach: Fork vs Config vs Wrapper

### 17.1 What Can Be Done with Config Only (No Fork)

- Model selection via `OPENAI_API_KEY` / `CODEX_API_KEY` + `--model` flag
- Sandbox mode via `--sandbox` flag
- Approval policy via `--ask-for-approval` flag
- Base URL override via `OPENAI_BASE_URL` env var (for proxy routing)
- Additional config overrides via `-c key=value` repeated flags
- Working directory via `--cd`
- Web search via `-c web_search="live"`

This covers basic provider routing through a proxy (e.g., thegent's CLIProxy) and model overrides.

### 17.2 What Requires a Wrapper / SDK Usage

- Thread persistence and resumption: Use `@openai/codex-sdk` with `resumeThread(id)`
- Structured output: Pass `outputSchema` in TurnOptions
- Image input: Pass `[{type:"local_image",path}]` as input array
- Reasoning control: Pass `modelReasoningEffort` in ThreadOptions
- Streaming events: Use `runStreamed()` for item-level events
- Web search mode: Pass `webSearchMode` in ThreadOptions

The TypeScript SDK is a clean programmatic interface for all of these. It requires Node.js 18+ and spawns the binary internally.

### 17.3 What Requires a Fork or App-Server Protocol Implementation

- Approval flow handling (exec and patch approvals before they happen)
- Dynamic tool registration (client-side tools the model can call)
- Real-time diff streaming
- Thread archive/unarchive/rollback
- Skills management
- Config layer management
- Account/auth management
- Full multi-agent collab orchestration

Implementing the App Server client is non-trivial but well-specified. The protocol is formally documented in `codex-rs/app-server-protocol/src/protocol/` and TypeScript + JSON Schema exports are generated from the same source.

### 17.4 Recommended Approach for thegent

**Tier 1 (Config/Env — implement immediately):**

- Ensure `OPENAI_BASE_URL` and `CODEX_API_KEY` are forwarded correctly for proxy routing
- Map thegent model aliases to Codex `--model` flag values
- Expose sandbox and approval policy as thegent config options
- Use `--config web_search=...` for web search toggle

**Tier 2 (TypeScript SDK wrapper — short term):**

- Write a thin Node.js wrapper using `@openai/codex-sdk`
- Implement `run()` / `runStreamed()` with proper event forwarding
- Add thread persistence (store/restore `thread.id`)
- Add structured output support
- Add image input support

**Tier 3 (App Server protocol client — medium term):**

- Implement a Rust or Python JSON-RPC client against the app-server protocol
- Gain access to approval flows, dynamic tools, diff streaming, full thread management
- The TypeScript schema exports from the protocol crate enable code generation

**Do NOT fork the binary** unless:

- Custom tools beyond MCP/dynamic tools are needed at the core level
- Provider routing at the API level (not proxy) is required
- The response is required before OpenAI provides it via config

### 17.5 Provider Routing Strategy

Codex does not natively route to non-OpenAI providers. The `model_provider` field exists but only `openai` and Azure are supported at the core level. For other providers:

1. Set `OPENAI_BASE_URL` to point to a compatible proxy (liteLLM, CLIProxy, etc.)
2. Use `CODEX_API_KEY` for the proxy's API key
3. The proxy translates to the target provider

The Responses API is required; the proxy must translate Chat Completions to Responses API format if the target does not support Responses natively.

---

## 18. Observations and Risks

1. **API dependency lock-in**: Codex is deeply coupled to the OpenAI Responses API. The SSE protocol, `response_id`, and token usage fields are Responses API-specific. Any proxy must faithfully translate or the session will fail.

2. **v1 deprecation timeline**: v1 protocol methods (`newConversation`, `sendUserTurn`, etc.) are marked deprecated in comments but no removal date is specified. thegent should NOT build new features against v1.

3. **UNSTABLE flags**: Several fields are marked `[UNSTABLE]` or `FOR OPENAI INTERNAL USE ONLY` — particularly `chatgptAuthTokens` auth mode, `history` in `ThreadResumeParams`, `experimental_raw_events`, and `CollaborationMode`. Do not use these in production integrations.

4. **MCP server is a prototype**: The `//! Prototype MCP server.` comment signals this is not production-grade. Use for simple orchestration only.

5. **Dynamic tools are powerful but fragile**: The `item/tool/call` server request requires low-latency response from the client. In high-latency or unreliable network conditions, the agent turn may fail or produce degraded results.

6. **Binary platform matrix**: The SDK vendors platform-specific binaries for `x86_64-linux-musl`, `aarch64-linux-musl`, `x86_64-darwin`, `aarch64-darwin`, `x86_64-windows-msvc`, `aarch64-windows-msvc`. Any harness wrapping the SDK must account for this.

---

## Sources

- Direct source: `/Users/kooshapari/temp-PRODVERCEL/485/API/codex-upstream/` (OpenAI Codex upstream repository)
- [Codex SDK documentation](https://developers.openai.com/codex/sdk/)
- [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
- [Codex IDE extension](https://developers.openai.com/codex/ide/)
- [OpenAI Codex App Server Architecture (InfoQ, 2026-02)](https://www.infoq.com/news/2026/02/opanai-codex-app-server/)
- [Unlocking the Codex harness (OpenAI blog)](https://openai.com/index/unlocking-the-codex-harness/)
- [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)
- [OpenAI GitHub: openai/codex](https://github.com/openai/codex)
