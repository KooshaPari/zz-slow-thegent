# Worklog: Provider/Adapter/Harness Hardening + Domain Expansion Plan

Date: 2026-02-23  
Scope: `thegent` + `cliproxyapi-plusplus` setup/login/provider management, long-term control plane, and CLI/MCP management interfaces across environments.

## 1) Executive Capture (everything consolidated)

This report consolidates:

- setup hang investigation and remediation work,
- provider coverage expansion requests (including `cline`, `amp`, `factory-api`),
- provider vs adapter architecture clarification,
- web research for hardening and optimization,
- expanded scope/domain plan across envs and management interfaces.

Operator-observed setup result (captured):

- success: Antigravity, Claude, Codex, Copilot, Gemini, Glm, Iflow, Kilo, Kimi, Kiro, NVIDIA NIM, OpenRouter, OpenCode Zen
- timed out: MiniMax (90s), Qwen (90s)
- failed: Roo (exit code 1)
- missing from setup summary prior to promotion: Cline, Amp, Factory API

## 2) What has already been implemented

### 2.1 Setup/login hang resilience and visibility (thegent)

Implemented:

- bounded provider login timeout and non-hanging setup behavior,
- provider-level timeout/failure continuation with explicit messages,
- delegated setup path to `cli-proxy-api-plus -setup` with fail-fast handling,
- MiniMax path tightened for interactive behavior and clearer non-TTY failure.

Touched surfaces:

- `thegent/src/thegent/agents/cliproxy_manager.py`
- `thegent/src/thegent/cli/commands/model_cmds_setup_helpers.py`
- `thegent/src/thegent/cli/commands/model_cmds.py`
- `thegent/tests/test_unit_cliproxy_manager.py`

### 2.2 Shortcut install completion (`roid`, `fanta`, etc.)

Implemented:

- interactive shim link install now includes `clode`, `roid`, `droid`, `fanta`, `anen`.

Touched surfaces:

- `thegent/src/thegent/clode_main.py`
- `thegent/tests/test_unit_clode_main.py`

### 2.3 Provider promotion to setup/login (`cline`, `amp`, `factory-api`)

Implemented on thegent side:

- provider definitions and login discoverability updated,
- factory key pattern matching for promoted providers.

Touched surfaces:

- `thegent/src/thegent/agents/cliproxy_data/provider_definitions.json`
- `thegent/src/thegent/agents/cliproxy_manager.py`
- `thegent/tests/test_unit_cliproxy_manager.py`

Implemented on cliproxy side:

- generic API-key login handlers for `cline`, `amp`, `factory-api`,
- setup wizard options include these providers.

Touched surfaces:

- `cliproxyapi-plusplus/pkg/llmproxy/cmd/generic_apikey_login.go`
- `cliproxyapi-plusplus/pkg/llmproxy/cmd/setup.go`
- `cliproxyapi-plusplus/pkg/llmproxy/cmd/setup_test.go`

Validation previously run and passing (focused):

- Python unit tests for setup/login/provider paths,
- Go unit tests for setup option coverage.

## 3) Provider vs Adapter in this architecture

### 3.1 Provider (domain-level integration)

Provider is the upstream model service identity and credential boundary.

Responsibilities:

- auth material and login method (OAuth/API key/token file),
- provider-specific model aliases and compatibility mapping,
- provider-specific base URL and routing metadata,
- provider-specific health/readiness checks.

Examples in current repo context:

- `minimax`, `qwen`, `roo`, `cline`, `amp`, `factory-api`, etc.

### 3.2 Adapter (transport/API-surface mediation)

Adapter is a local compatibility surface between client expectations and backend proxy/server capabilities.

Responsibilities:

- API-surface normalization (e.g., Responses surface, websocket behavior),
- protocol translation and shape adaptation,
- strict readiness/health gating for adapted surface.

Examples in current repo context:

- `THGENT_CLIPROXY_ADAPTER` behavior in `cliproxy_manager.py`,
- adapter launcher (`scripts/start_proxy_with_adapter.py`) and `/v1/responses` expectation checks.

### 3.3 Boundary rule

- Providers define who/where you authenticate and route.
- Adapters define how requests are surfaced/translated locally.
- These concerns should stay orthogonal in code and config.

## 4) Local codebase QoL and extensibility audit

### 4.1 Workstream logic duplication

Observed multiple overlapping implementations around workstream parsing/ops/integration:

- `thegent/src/thegent/integration/work_stream.py`
- `thegent/src/thegent/commands/workstream.py`
- `thegent/src/thegent/planning/work_stream.py`
- `thegent/src/thegent/utils/workstream.py`
- `thegent/src/thegent/utils/workstream_automation.py`
- `thegent/src/thegent/utils/workstream_ops.py`

Risk:

- drift in schema assumptions,
- inconsistent lock/write semantics,
- increased maintenance and bug surface.

QoL scope add:

- converge to one canonical workstream domain package with strict API boundaries,
- deprecate wrappers with a compatibility window and contract tests.

### 4.2 Setup/provider registry split across Python and Go

Current split:

- Python side owns substantial setup/login orchestration and provider registry logic,
- Go side also owns setup wizard and auth actions.

Risk:

- duplicated behavior definitions,
- partial upgrades and inconsistent UX,
- longer incident MTTR due to dual control planes.

QoL scope add:

- Go-first source-of-truth for setup/auth/provider routing domain,
- Python becomes strict delegator (machine-contract only).

### 4.3 Docs/governance surface size

Signal:

- `docs/` currently contains 3117 files.

Risk:

- knowledge fragmentation and stale guidance pockets.

QoL scope add:

- define docs ownership boundaries and lifecycle states,
- enforce index + archival policy by automation.

## 5) Web research findings for hardening and optimization

### 5.1 Data contracts and schema governance

Findings:

- JSON Schema Draft 2020-12 is stable and suitable for machine-validated CLI/MCP contracts.
- MCP spec is versioned by date and uses JSON-RPC 2.0 message structures, with capability/version negotiation requirements.

Implication:

- define `schema_version` in all setup/auth/doctor JSON outputs,
- treat version compatibility as first-class in CLI delegation and MCP tools.

Sources:

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12
- MCP spec overview/versioning: https://modelcontextprotocol.io/specification/
- MCP 2025-11-25 basic overview: https://modelcontextprotocol.io/specification/2025-11-25/basic

### 5.2 Configuration model across environments

Findings:

- YAML remains human-friendly but semantically complex; v1.2.2 clarifies status with no normative behavior change from 1.2.
- TOML v1.0.0 is simpler and strongly typed for many config scenarios.
- CUE provides constraint-driven validation and generation over YAML/JSON ecosystems.
- Twelve-Factor still supports environment-variable separation for deploy-varying config/secrets.

Implication:

- Authoring format recommendation: YAML for operator-facing provider/adapter/harness manifests.
- Validation recommendation: enforce JSON Schema 2020-12 at load-time and CI.
- Advanced roadmap: evaluate CUE as a schema-authoring and generation layer if rule complexity grows.
- Secrets rule: deploy-varying secrets via env/KMS/Vault/SOPS-backed flows, not committed plain configs.

Sources:

- YAML 1.2.2: https://yaml.org/spec/1.2.2/
- TOML v1.0.0: https://toml.io/en/v1.0.0
- CUE docs: https://cuelang.org/docs/
- Twelve-Factor config: https://www.12factor.net/config
- SOPS docs: https://getsops.io/docs/

### 5.3 CLI/TUI implementation stack

Findings:

- Cobra remains a strong command-tree and lifecycle baseline for Go CLIs.
- Bubble Tea + Bubbles ecosystem remains a practical fit for step-based, live-updating setup TUI UX.

Implication:

- keep `cliproxyctl` command surface on Cobra,
- implement setup TUI as Bubble Tea model with deterministic event log and JSON mirror.

Sources:

- Cobra docs: https://cobra.dev/docs/tutorials/getting-started/
- Cobra project: https://cobra.dev/
- Bubbles: https://github.com/charmbracelet/bubbles
- Bubble Tea template: https://github.com/charmbracelet/bubbletea-app-template

### 5.4 Observability baseline

Findings:

- OpenTelemetry semantic conventions continue to provide common attribute/event naming for logs/metrics/traces.

Implication:

- standardize setup/auth events (provider, step, result, duration_ms, error.type),
- expose stable telemetry fields for alerting and SLOs.

Sources:

- OTel general semantic conventions: https://opentelemetry.io/docs/specs/semconv/general/
- OTel semantic conventions overview: https://opentelemetry.io/docs/specs/otel/semantic-conventions/

## 6) Target architecture and management interfaces

### 6.1 Control plane ownership

Decision:

- `cliproxyctl` (Go) owns provider/auth/setup/doctor/route-resolution domain behavior.
- `thegent` delegates and renders, but does not own provider business logic.

### 6.2 Command/API surface (proposed)

CLI (`cliproxyctl`):

- `cliproxyctl setup [--providers ...] [--tui] [--json]`
- `cliproxyctl login <provider> [--force] [--json]`
- `cliproxyctl auth list|status|refresh [--json]`
- `cliproxyctl route resolve --model <model> [--json]`
- `cliproxyctl doctor [--json]`
- `cliproxyctl registry validate|lint [--json]`

MCP mgmt interface:

- `mgmt.providers.list`
- `mgmt.providers.login.start`
- `mgmt.providers.login.poll`
- `mgmt.providers.setup.run`
- `mgmt.route.resolve`
- `mgmt.auth.status`
- `mgmt.doctor.run`

All mgmt operations return versioned JSON payloads with deterministic machine fields.

### 6.3 Environment model

Environments:

- local-dev
- ci
- staging
- production

Env policy requirements:

- immutable release artifact + externalized runtime secrets,
- config layering: base -> env overlay -> runtime overrides,
- strict secret-source provenance and rotation metadata.

## 7) Provider/adapter/harness registry design recommendation

Recommendation (long-term):

- Keep operator-edited manifests in YAML for readability.
- Validate manifests against JSON Schema 2020-12.
- Generate typed Go/Python structs from schema where possible.
- Optionally add CUE as higher-order constraint authoring when policy complexity exceeds JSON Schema ergonomics.

Proposed top-level registry split:

- `registry/providers/*.yaml`
- `registry/adapters/*.yaml`
- `registry/harness/*.yaml`
- `registry/envs/*.yaml`
- `registry/schemas/*.schema.json`

Reasoning:

- clean domain boundaries,
- diff-friendly lifecycle,
- machine enforcement without giving up operator ergonomics.

## 8) UX plan for setup status and summaries

Target UX behavior per provider:

- static heading: `Setting up <Provider>...`
- live steps (rewritten in place): `checking`, `open-url`, `wait-login`, `validate`, `write-config`
- terminal collapse to one final line: success/fail/timeout with duration

Global behavior:

- cumulative provider summary list (success/fail/timeout),
- deterministic exit codes and machine-readable recap JSON,
- never hang: per-step timeout, per-provider timeout, global timeout.

## 9) Work breakdown structure (WBS)

### Wave 1: Contract + control-plane skeleton

- scaffold `cliproxyctl` commands and `--json` contracts,
- define JSON Schema for setup/login/doctor payloads,
- add contract tests and golden fixtures.

### Wave 2: Move provider login/setup logic into Go domain

- centralize provider registry and auth strategy matrix,
- implement timeout/cancellation policy and error taxonomy,
- complete promoted providers (`cline`, `amp`, `factory-api`) parity checks.

### Wave 3: TUI setup and telemetry

- Bubble Tea setup model with step events and live rewrite UX,
- emit structured event stream and stable summary output,
- instrument with OpenTelemetry semantic field baseline.

### Wave 4: thegent delegation hard-cut

- shell out exclusively to `cliproxyctl ... --json`,
- remove duplicated provider/login decision logic from Python,
- keep compatibility shim for one release cycle.

### Wave 5: MCP management layer + multi-env policy

- expose mgmt MCP methods over the same domain APIs,
- add environment overlays + policy checks + doctor gates,
- document operator runbooks and CI/CD gates.

## 10) Risks and mitigations

Risk: dual control-plane drift during migration.  
Mitigation: contract tests in both repos; one authoritative schema package.

Risk: interactive login edge-cases (TTY/non-TTY/OAuth browser constraints).  
Mitigation: explicit mode flags, deterministic fallback codes, clear non-interactive guidance.

Risk: config complexity explosion.  
Mitigation: registry separation + schema lint gates + lifecycle policy.

Risk: setup regressions hidden by only human-readable logs.  
Mitigation: mandatory JSON summary and CI replay tests.

## 11) Acceptance criteria

- `thegent setup` no longer owns provider-specific business logic.
- all setup/login/doctor operations have stable JSON contracts and schema versioning.
- provider timeout behavior is deterministic and non-hanging.
- provider vs adapter registries are separate and schema-validated.
- setup UX shows step-level progress and final cumulative summary.
- MCP mgmt surface can trigger and observe same domain operations as CLI.

## 12) Immediate next execution queue

1. Implement `cliproxyctl --json` schema package and fixtures.
2. Port remaining Python provider decision paths into Go domain package.
3. Build setup TUI event model and one provider end-to-end path.
4. Wire `thegent` delegation for setup/login/auth-status with compatibility shim.
5. Add CI gates: schema validation, golden output tests, timeout regression tests.

## 13) Notes on provider coverage status (as of this run)

- Promoted providers (`cline`, `amp`, `factory-api`) have been added to setup/login surfaces in both repos.
- Setup stalls for MiniMax/Qwen/Roo were treated as reliability failures to be constrained by deterministic timeout/exit semantics.
- Additional provider onboarding should now follow the same registry + contract + test path, not ad-hoc Python wiring.

## 14) Execution Update: Worktrees + Child Agents (this run)

Execution mode used:

- dedicated worktrees:
  - `thegent`: `/Users/kooshapari/temp-PRODVERCEL/485/kush/wt/thegent-provider-plane` (`codex/provider-plane-wave1`)
  - `cliproxyapi-plusplus`: `/Users/kooshapari/temp-PRODVERCEL/485/kush/wt/cliproxyctl-plane` (`codex/cliproxyctl-wave1`)
- child worker agents used for parallel implementation lanes (Go lane + Python lane).

Implemented in `cliproxyapi-plusplus`:

- Added new binary entrypoint and contract artifacts:
  - `cliproxyapi-plusplus/cmd/cliproxyctl/main.go`
  - `cliproxyapi-plusplus/cmd/cliproxyctl/main_test.go`
  - `cliproxyapi-plusplus/contracts/cliproxyctl-response.schema.json`
- `cliproxyctl` currently supports:
  - `setup [--json] [--providers ...]`
  - `login <provider> [--json]` (or `--provider`)
  - `doctor [--json]`
- Stable envelope fields:
  - `schema_version`, `command`, `ok`, `timestamp`, `details`

Implemented in `thegent`:

- Added strict cliproxyctl envelope parsing + delegation helpers in:
  - `thegent/src/thegent/cli/commands/model_cmds.py`
- Delegated setup/login paths to `cliproxyctl --json` with loud failures on:
  - missing binary,
  - invalid JSON,
  - schema mismatch,
  - command mismatch,
  - nonzero exit / `ok=false` envelope.
- Added focused tests:
  - `thegent/tests/commands/test_model_cmds_cliproxyctl_delegation.py`

Validation evidence:

- `cd cliproxyapi-plusplus && go test ./cmd/cliproxyctl`
  - result: `ok   github.com/router-for-me/CLIProxyAPI/v6/cmd/cliproxyctl`
- `cd thegent && uv run python -m pytest tests/commands/test_model_cmds_cliproxyctl_delegation.py -q`
  - result: `6 passed`

Notes:

- This is Wave 1 contract/delegation groundwork; provider registry convergence and full TUI step engine remain in subsequent waves.

## 15) Execution Update: Wave 2 Provider Expansion + Build Blockers

Completed implementation work:

- Added promoted provider API-key login handlers in cliproxy cmd layer:
  - `pkg/llmproxy/cmd/generic_apikey_login.go`
    - `DoClineLogin`
    - `DoAmpLogin`
    - `DoFactoryAPILogin`
    - shared helper for OpenAI-compat provider config insertion.
- Added promoted providers to setup wizard options:
  - `pkg/llmproxy/cmd/setup.go`
- Resolved duplicate symbol collision in native login layer:
  - `pkg/llmproxy/cmd/native_cli.go` (duplicate `ThegentSpec` removal)
- Resolved OIDC region validation symbol mismatch:
  - `pkg/llmproxy/auth/kiro/sso_oidc.go` (`oidcRegionPattern` -> `awsRegionPattern`)

Current blocker in primary cliproxy checkout:

- Focused test command still fails due unrelated pre-existing syntax errors in executor package:
  - `pkg/llmproxy/executor/kiro_executor.go:1685` and `:1701`
- This prevents `go test ./cmd/cliproxyctl` from completing in this checkout even though cliproxyctl-local changes compile in isolated worktree context.

Thegent lane status:

- Delegation tests continue passing:
  - `uv run python -m pytest tests/commands/test_model_cmds_cliproxyctl_delegation.py -q`

## 16) Build Unblock Loop (additional findings)

Additional compile breakpoints discovered while validating cliproxyctl in primary checkout:

- `pkg/llmproxy/executor/github_copilot_executor.go`: duplicate `CloseExecutionSession` declarations.
- `pkg/llmproxy/executor/codex_websockets_executor.go`:
  - unused imports (`crypto/sha256`, `encoding/hex`),
  - undefined identifiers (`authID`, `wsURL`).

Status implication:

- `go test ./cmd/cliproxyctl` cannot pass in this checkout until these unrelated executor failures are resolved.
- `thegent` delegation lane remains validated by focused tests.

## 17) Build Validation State (latest)

Resolved compile blockers in primary cliproxy checkout:

- `pkg/llmproxy/executor/kiro_executor.go` syntax error in model mapping branch.
- `pkg/llmproxy/executor/github_copilot_executor.go` duplicate `CloseExecutionSession` method.
- `pkg/llmproxy/executor/codex_websockets_executor.go` undefined identifiers and unused imports in websocket disconnect logging.
- `pkg/llmproxy/cmd/native_cli.go` duplicate `ThegentSpec` declaration.
- `pkg/llmproxy/auth/kiro/sso_oidc.go` invalid region regex symbol reference.

Current infra blocker:

- `go test ./cmd/cliproxyctl` now fails at link step due environment disk exhaustion:
  - `link: mapping output file failed: no space left on device`

Thegent validation remains green:

- `uv run python -m pytest tests/commands/test_model_cmds_cliproxyctl_delegation.py -q` -> passed.

## 18) Runtime Path Fix for User Shell

Observed shell/runtime mismatch:

- User shell was invoking `thegent` from the mise path (`.../python/3.12.12/bin/thegent`) rather than the known-good miniforge binary path.

Action taken:

- Replaced mise `thegent` executable with a deterministic wrapper:
  - `~/.local/share/mise/installs/python/3.12.12/bin/thegent`
  - now executes `/opt/homebrew/Caskroom/miniforge/base/bin/thegent` directly.

Verification:

- `THGENT_SETUP_USE_CLIPROXY=1 .../mise/.../thegent setup --no-links --no-wizard` completes successfully.
