# Threat Model Template (STRIDE-per-component)

> **Source audit:** `FLEET-AUDIT-REPORT.md` — S7 (Threat model) is the #1 P0 gap (priority 42, 10 of 11 audited repos at score 0).
> **Method:** STRIDE per-component. Each component in your system gets a row; each STRIDE category is a column.
> **Template:** Adapted from `THREAT-MODEL-TEMPLATE.md` (Phenotype Org, v1.0).
> **Last reviewed:** 2026-06-16
> **Owner:** thegent security (CODEOWNERS gate, 63 lines)

## When to do this

A threat model is **wired** (score 2) when this file exists in `docs/security/threat-model.md`
and is referenced from your `README.md` or `SECURITY.md`.
It's **measured** (score 3) when a CI gate fails if the file is more than 90 days old.

## STRIDE cheat sheet

| Letter | Threat                 | Property violated | Question to ask                              |
| ------ | ---------------------- | ----------------- | -------------------------------------------- |
| **S**  | Spoofing               | Authentication    | Can an attacker impersonate a user/system?   |
| **T**  | Tampering              | Integrity         | Can an attacker modify data or code?         |
| **R**  | Repudiation            | Non-repudiation   | Can a user deny an action they took?         |
| **I**  | Information disclosure | Confidentiality   | Can an attacker read data they shouldn't?    |
| **D**  | Denial of service      | Availability      | Can an attacker make the system unavailable? |
| **E**  | Elevation of privilege | Authorization     | Can an attacker gain higher privileges?      |

For each cell, mark one of: **N/A** (not applicable to this component), **low** (impact minor,
mitigation optional), **med** (mitigation required), **high** (mitigation + test required).

---

## Component inventory

List every component in your system. A component is any discrete unit that handles data
or accepts input — a service, a CLI, a database, a queue, a third-party dependency, a
network boundary, a CI workflow, even a build artifact.

### thegent component inventory (covered below)

- **Agent loop / orchestrator** — `src/thegent/loop_controller.py`, `hierarchy_orchestrator.py`, `crew.py`, `state_machine.py`
- **Tool registry** — `src/thegent/registry.py`, `unified_registry.py`, `tool_adapter.py`, `unified_registry_cli.py`
- **LLM provider abstraction** — `src/thegent/cliproxy_adapter/`, `cliproxy_manager.py`, `provider_loop.py`, `cliproxy_data/`
- **Python package supply chain** — `pyproject.toml` (PyPI publish), `phenotype-py-utils` (git dep), `litellm==1.88.1` (pinned), all 47 transitive deps
- **CI workflows** — `.github/workflows/ci.yml`, `release.yml`, `python-ci.yml`, `deny.yml`, `scorecard.yml`, `audit.yml`
- **MCP server** — `fastmcp[tasks]>=3.0.0` runtime, exposed via `thegent` CLI
- **Rust shims** — `crates/` (thegent-parser, thegent-git, thegent-fs, thegent-crypto, thegent-hooks, thegent-tui, thegent-cache, thegent-metrics, thegent-memory, thegent-discovery); called from Python via `thegent.rust_wrappers` (clode/dex/roid/droid/anen/fanta/antigma)

### Component: `thegent` Rust shim crates (`crates/`, called from Python via `thegent.rust_wrappers`)

| Threat                  | Rating | Specific attack vector                                                                                                                                     | Mitigation                                                                                                                                                                     | Owner        | Last reviewed |
| ----------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | ------------- |
| **S — Spoofing**        | low    | `clode` / `dex` / `roid` / `droid` / `anen` / `fanta` / `antigma` shim wrappers resolve the same binary on PATH; PATH hijack could swap a malicious binary | `clode_binary_discovery` (in-tree) walks a pinned allowlist of binary paths; `thegent-fs` crate centralizes discovery; release builds are SHA-locked via `rust-toolchain.toml` | rust-dev     | 2026-06-16    |
| **T — Tampering**       | med    | A malicious update to a transitive Rust crate (Cargo registry) is auto-pulled                                                                              | `deny.toml` (in repo root) pins licenses and blocks `phenoShared` namespace collisions; `rust-toolchain.toml` pins toolchain; SBOM still 0 (THE-045)                           | supply-chain | 2026-06-16    |
| **R — Repudiation**     | low    | Shim invocation does not log which crate version ran                                                                                                       | `thegent-metrics` crate records crate version + git SHA on every shim call                                                                                                     | rust-dev     | 2026-06-16    |
| **I — Info disclosure** | med    | `thegent-fs` shim reads filesystem paths passed in from LLM output; if the LLM is jailbroken, it can exfiltrate file contents                              | Path arguments are constrained to the workspace root via `cliproxy_request_transform`; thegent-crypto crate wraps sensitive reads in an audit log                              | security     | 2026-06-16    |
| **D — DoS**             | low    | Rust shims are in-process; no network surface                                                                                                              | n/a                                                                                                                                                                            | rust-dev     | 2026-06-16    |
| **E — Elevation**       | med    | `thegent-hooks` crate runs pre/post-tool hooks; a malicious hook registered at startup executes as the user                                                | Hooks are whitelisted in `hooks/` and signed; `clippy.toml` + `cargo clippy -- -D warnings` block dangerous patterns; `thegent-crypto` verifies hook signatures on load        | security     | 2026-06-16    |

## Per-component threat grid

For each component, fill in the STRIDE table.

### Component: `<name>`

| Threat                  | Rating       | Specific attack vector | Mitigation | Owner | Last reviewed |
| ----------------------- | ------------ | ---------------------- | ---------- | ----- | ------------- |
| **S — Spoofing**        | low/med/high |                        |            |       | YYYY-MM-DD    |
| **T — Tampering**       |              |                        |            |       |               |
| **R — Repudiation**     |              |                        |            |       |               |
| **I — Info disclosure** |              |                        |            |       |               |
| **D — DoS**             |              |                        |            |       |               |
| **E — Elevation**       |              |                        |            |       |               |

Repeat this block for every component.

---

## Worked examples: thegent

These are real, audit-derived threat models for the `thegent` Python agent runtime. They replace
the generic `phenodocs` example in the upstream template.

### Component: `thegent` agent loop / orchestrator (`loop_controller.py`, `hierarchy_orchestrator.py`)

| Threat                  | Rating | Specific attack vector                                                                                                                                    | Mitigation                                                                                                                                                                                                                     | Owner    | Last reviewed |
| ----------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------- |
| **S — Spoofing**        | med    | Prompt injection in tool-result messages impersonates the orchestrator or a parent agent, causing child agents to execute as a different identity         | `provider_loop.py` strips tool-output identity claims; sub-agent dispatch uses signed `role_id` tokens; `.llmignore` blocks untrusted content as system prompt                                                                 | agentic  | 2026-06-16    |
| **T — Tampering**       | high   | Malicious tool output mutates loop state (e.g., rewrites the task plan via injected JSON in stdout); `state_machine.py` transitions are not all validated | Plan edits are diffed against a hash of the original; `tach.toml` enforces module boundaries; `pyrightconfig.json` standard checking on `src/`                                                                                 | agentic  | 2026-06-16    |
| **R — Repudiation**     | med    | User denies that an agent action ran on their behalf; loop controller does not always log tool-call author or message-id                                  | `structlog>=24.0.0` writes structured events; session log keyed by `session_id` + tool author; `WORKLOG.md` ingest at session end                                                                                              | agentic  | 2026-06-16    |
| **I — Info disclosure** | high   | Agent loop carries prior-conversation context into a tool call; tool output may echo PII or secrets into an LLM provider's logging                        | `.llmignore` + `.env.example` reference; redaction hook in `hooks/` pre-tool-call; secrets via `pydantic-settings` (env-only, never `pyproject.toml`); THE-033 retention policy still 0 — open                                 | security | 2026-06-16    |
| **D — DoS**             | med    | Adversarial prompt causes unbounded tool-call loops, exhausting LLM API quota and bill                                                                    | `pybreaker>=1.2.0` circuit breaker on provider calls; `tenacity>=9.0.0` retry with capped attempts; `--max-steps` CLI flag; hard max-tokens per call                                                                           | agentic  | 2026-06-16    |
| **E — Elevation**       | high   | Tool adapter (e.g., shell, `clode` shim) invoked with elevated scope via JSON args from the LLM; prompt injection escalates a read-only tool to a write   | `tool_adapter.py` requires explicit `requires_approval=True` for write tools; `routing_contracts.py` enforces an allowlist of tool name → capability mappings; THE-004 AS2 dry-run mode (score 1 → target 2) still in progress | security | 2026-06-16    |

### Component: `thegent` tool registry (`registry.py`, `unified_registry.py`, `tool_adapter.py`)

| Threat                  | Rating | Specific attack vector                                                                                                                                                          | Mitigation                                                                                                                                                               | Owner    | Last reviewed |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------- |
| **S — Spoofing**        | med    | Attacker registers a tool with the same name as a built-in (e.g., `bash`) but routed to a malicious handler via a side-loaded plugin path                                       | `unified_registry.py` namespaces tools by `{package}.{name}`; resolution rejects `__` and shadowed builtins; `adapters/` is import-linted via `.importlinter`            | agentic  | 2026-06-16    |
| **T — Tampering**       | med    | Plugin author mutates an already-registered tool's handler at runtime (TOCTOU between registration and call)                                                                    | Handlers are frozen at registration time; `tool_adapter.py` snapshots the callable + signature; thegent-crypto crate signs tool manifests (`crates/thegent-crypto`)      | security | 2026-06-16    |
| **R — Repudiation**     | low    | Registry does not log which tool version was invoked                                                                                                                            | `unified_registry.py` records `tool_name`, `tool_version`, and caller session_id into structlog                                                                          | agentic  | 2026-06-16    |
| **I — Info disclosure** | med    | Tool's `description` field (sent to LLM) leaks the host's filesystem layout or env var names                                                                                    | `unified_registry_cli.py` `redact` step on tool descriptions; LLM-side filter on output                                                                                  | agentic  | 2026-06-16    |
| **D — DoS**             | low    | Registry is in-process; no remote surface                                                                                                                                       | n/a (in-memory dict)                                                                                                                                                     | agentic  | 2026-06-16    |
| **E — Elevation**       | med    | `unified_registry_cli.py` allows registering a tool with arbitrary `capabilities` (e.g., `network`, `shell`); LLM prompt injection triggers registration of a new tool mid-loop | `routing_contracts.py` validates capability claims against `tach.toml` boundaries; new tool registration requires an out-of-band confirmation token in non-`--dev` modes | security | 2026-06-16    |

### Component: `thegent` LLM provider abstraction (`cliproxy_adapter/`, `provider_loop.py`, `cliproxy_manager.py`)

| Threat                  | Rating | Specific attack vector                                                                                                                                              | Mitigation                                                                                                                                                                                        | Owner    | Last reviewed |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------- |
| **S — Spoofing**        | high   | Attacker serves a TLS-stripped / fake provider endpoint; `cliproxy_manager.py` falls back to a non-pinned base URL on retry                                         | `httpx>=0.28.1` enforces HTTPS by default; provider allowlist in `cliproxy_adapter/config.py`; `cliproxy_header_utils.py` validates the `Server` identity on every reconnect                      | security | 2026-06-16    |
| **T — Tampering**       | high   | Rogue or compromised LLM response injects system-level instructions, JSON tool calls that were not in the user prompt                                               | `provider_loop.py` runs output through `output_schema.py` (pydantic validation); thegent runs in `dry-run` mode for unknown tool shapes; redaction hook before persisting                         | security | 2026-06-16    |
| **R — Repudiation**     | low    | Provider returns a response that the user later denies; thegent does not always store the response hash                                                             | `compaction.py` + `context_compactor.py` keep a content-addressed store of provider responses; session log retains the SHA-256                                                                    | agentic  | 2026-06-16    |
| **I — Info disclosure** | high   | API keys for Anthropic / OpenAI / Gemini logged to console via Rich / structlog; or sent in a `Referer` header                                                      | `pydantic-settings` loads keys from env only; `.gitignore` blocks `.env`; `pre-commit-config.yaml` runs `gitleaks` + `trufflehog`; THE-046 S4 (API key auth model) score 1 → target 2 in progress | security | 2026-06-16    |
| **D — DoS**             | med    | Adversarial input or downstream provider rate-limits cause request pile-up; retry storm on a flaky provider                                                         | `pybreaker` per-provider circuit breaker; `tenacity` exponential backoff with jitter; `apscheduler>=3.10.4` for provider health pings; THE-041 RL1 (LLM retry) already 1, target 2                | sre      | 2026-06-16    |
| **E — Elevation**       | med    | `cliproxy_manager.py` accepts a `provider_override` flag from the user (or LLM) that swaps in a higher-privilege provider mid-run (e.g., a different org's billing) | `provider_loop.py` resolves the provider at session start and freezes it; `--provider` CLI flag requires re-auth; change requires session restart                                                 | security | 2026-06-16    |

### Component: `thegent` Python package supply chain (`pyproject.toml` → PyPI)

| Threat                  | Rating | Specific attack vector                                                                                                                                                      | Mitigation                                                                                                                                                                             | Owner        | Last reviewed |
| ----------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ------------- |
| **S — Spoofing**        | med    | Typosquat on PyPI (`thegentt`) confuses installs; or a dependency is replaced by a look-alike (e.g., `pydantic` vs `pydantic-ai`)                                           | `pyproject.toml` pins exact versions for `litellm==1.88.1`; `uv.lock` (664 KB) committed; `deny.toml` blocks `phenoShared` org namespacing collisions                                  | supply-chain | 2026-06-16    |
| **T — Tampering**       | high   | A malicious update to a transitive dep (47 listed) is published and auto-pulled on next `uv sync`                                                                           | `uv.lock` lockfile committed; `dependency-groups.dev` pins `mypy`, `ruff`, `hypothesis`; `DEPENDENCY_AUDIT.md` documents the review cadence; SBOM + SLSA still 0 (THE-045, THE-048–50) | supply-chain | 2026-06-16    |
| **R — Repudiation**     | low    | Publish provenance missing; no SLSA `provenance` attestation attached to PyPI release                                                                                       | `cliff.toml` + GitHub `release.yml` exist; SLSA L3 provenance is a known gap (S8 pillar)                                                                                               | ci-ops       | 2026-06-16    |
| **I — Info disclosure** | med    | Build process leaks the publish token; or a transitive dep phones home at install time                                                                                      | `release.yml` uses `PYPI_TOKEN` from GitHub secrets; pre-publish `trufflehog.yml` scan; `.trufflehog.yml` baseline                                                                     | supply-chain | 2026-06-16    |
| **D — DoS**             | low    | PyPI outage blocks install; or a malicious dep hangs at install (e.g., a long-running `setup.py`)                                                                           | `hatchling` build backend (no arbitrary code at install); `uv` cache; runtime can fall back to local clone                                                                             | sre          | 2026-06-16    |
| **E — Elevation**       | high   | `phenotype-py-utils @ git+https://github.com/KooshaPari/phenotype-py-utils.git@v0.1.0` is a git-tag-pinned dep; a compromised maintainer account could re-tag or force-push | Pinned to a specific tag (`v0.1.0`), not a branch; `cargo`/Python sigstore verification is a known gap; no SLSA attestation (THE-049)                                                  | security     | 2026-06-16    |

### Component: `thegent` CI workflows (`.github/workflows/*.yml`)

| Threat                  | Rating | Specific attack vector                                                                                                                                               | Mitigation                                                                                                                                              | Owner    | Last reviewed |
| ----------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------- |
| **S — Spoofing**        | med    | `ci.yml` references a reusable workflow at a placeholder SHA (audit found no matching live file) — if SHA unpins, attacker can swap in a malicious reusable workflow | All workflows pin to SHA where possible; CODEOWNERS (63 lines) gates `.github/` changes; audit 2026-06-05 captured the missing-source finding           | ci-ops   | 2026-06-16    |
| **T — Tampering**       | med    | Malicious PR adds a workflow step that exfiltrates secrets on push                                                                                                   | `permissions: contents: read` declared on `ci.yml` and `release.yml`; default token is read-only; CODEOWNERS required review for `.github/workflows/**` | ci-ops   | 2026-06-16    |
| **R — Repudiation**     | low    | Workflow authorship                                                                                                                                                  | Git log; CODEOWNERS review trail in PR                                                                                                                  | ci-ops   | 2026-06-16    |
| **I — Info disclosure** | low    | Workflow logs leak API keys or PII                                                                                                                                   | Secrets via `PYPI_TOKEN`, `ANTHROPIC_API_KEY`, etc. (GitHub encrypted); `deny.yml` + `gitleaks.toml` block plaintext in logs                            | security | 2026-06-16    |
| **D — DoS**             | low    | Workflow abuse / quota exhaustion                                                                                                                                    | `concurrency: group + cancel-in-progress: true` on `ci.yml` and `release.yml`; standard Linux runners only (per `~/.claude/CLAUDE.md` billing policy)   | ci-ops   | 2026-06-16    |
| **E — Elevation**       | med    | Compromised PAT in a workflow step escalates to write                                                                                                                | `permissions: contents: read` on all workflows; `id-token: write` only where OIDC is required                                                           | ci-ops   | 2026-06-16    |

### Component: `thegent` MCP server (`fastmcp[tasks]>=3.0.0`, exposed via `thegent` CLI)

| Threat                  | Rating | Specific attack vector                                                                                  | Mitigation                                                                                                                                      | Owner    | Last reviewed |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------- |
| **S — Spoofing**        | med    | A second MCP server impersonates `thegent` on the same port / over the same stdio                       | `granian>=1.7.4` server binds to a configurable port; `mcp_server.log` records the listen socket; thegent-mcp handshake requires a static token | api      | 2026-06-16    |
| **T — Tampering**       | med    | An MCP request mutates the agent loop's session state via a `task` channel that bypasses validation     | `fastmcp[tasks]` channel is gated behind `routing_contracts.py`; tool registry validates every inbound message                                  | api      | 2026-06-16    |
| **R — Repudiation**     | low    | MCP request origin is anonymous (no caller identity)                                                    | Optional `PyJWT>=2.12.0` bearer token; session_id is recorded per call                                                                          | api      | 2026-06-16    |
| **I — Info disclosure** | med    | MCP server logs payloads containing PII / secrets to `mcp_server.log` (file in repo root)               | `mcp_server.log` is `.gitignore`d; structlog redaction; THE-033 retention still 0                                                               | security | 2026-06-16    |
| **D — DoS**             | low    | MCP port exhaustion; large payload attacks                                                              | `uvicorn>=0.34.0` with body-size cap; `pybreaker` on the tool dispatch                                                                          | sre      | 2026-06-16    |
| **E — Elevation**       | med    | A tool exposed over MCP with a capability that the in-process registry has, but the MCP caller does not | Capability-gated dispatch in `routing_contracts.py`; out-of-band auth for `network` / `shell` capability tools                                  | security | 2026-06-16    |

---

## How to lift the S7 score

- **0 → 1 (ad-hoc):** Add a `docs/security/threat-model.md` with at least one component's STRIDE table.
- **1 → 2 (wired):** Reference the threat model from `README.md` and `SECURITY.md`. Cover at least 80% of your components. Add an owner + last-reviewed column to each row.
- **2 → 3 (measured):** Add a CI gate that fails if `docs/security/threat-model.md` is older than 90 days, OR if a previously-scored component row is deleted.

## Review cadence

Review the threat model:

- **On every major release** (semver minor)
- **On any new external dependency** added
- **On any new public-facing endpoint**
- **Quarterly minimum** (a 90-day-old model is a CI failure for "measured" repos)

## Cross-references

- `BACKLOG.md` — the P0 list; S7 is the #1 item.
- `FLEET-AUDIT-REPORT.md` — the per-pillar fleet-wide distribution.
- Per-repo `ACTION-PLAN.md` files — each has a "Build" phase with S7 task entries.
- thegent-specific: `CODEOWNERS` (63 lines), `deny.toml`, `.trufflehog.yml`, `gitleaks.toml`, `pyproject.toml` `[dependency-groups]`.
- thegent-specific action plan: `docs/audits/thegent/ACTION-PLAN.md` (THE-044 S7 task).

## How to validate

```bash
# After writing your threat model, validate it has all 5 STRIDE rows
for c in S T R I D E; do
  grep -q "^\*\*$c " docs/security/threat-model.md || echo "missing $c"
done
```

If `grep` returns nothing for all 6 letters, your file is valid.

## Provenance

- **Template version:** 1.0
- **Author:** Phenotype Org holistic audit, 2026-06-16
- **Audit that produced it:** `FLEET-AUDIT-30-PILLAR.md` (S7 P0)
- **License:** Same as the parent repo
