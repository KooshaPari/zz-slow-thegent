# Feature Atlas - Enabled Features Matrix

**Date:** February 23, 2026

---

## Core Features (Always Enabled)

| Feature      | Module           | Status |
| ------------ | ---------------- | ------ |
| CLI Commands | `thegent-cli`    | ✅     |
| Agent System | `thegent-agents` | ✅     |
| MCP Server   | `thegent-mcp`    | ✅     |
| SDK          | `thegent-sdk`    | ✅     |

---

## Feature Gates (Environment-Controlled)

| Feature                | Env Variable                                  | Default | Status |
| ---------------------- | --------------------------------------------- | ------- | ------ |
| Parser Quality Routing | `THGENT_ROUTING_PARSER_QUALITY_ENABLED`       | false   | Off    |
| Cost Tracking          | `THGENT_COST_TRACKING_ENABLED`                | false   | Off    |
| Terminal Management    | `THGENT_TERMINAL_MANAGEMENT_ENABLED`          | false   | Off    |
| Input Guardrails       | `THGENT_INPUT_GUARDRAILS_ENABLED`             | false   | Off    |
| Ghostty Integration    | `THGENT_GHOSTTY_ENABLED`                      | false   | Off    |
| IDE Integration        | `THGENT_IDE_INTEGRATION_ENABLED`              | false   | Off    |
| MAIF Runner            | `THGENT_MAIF_ENABLED`                         | false   | Off    |
| HeliosShield           | `THGENT_HELIOS_SHIELD_ENABLED`                | false   | Off    |
| Circuit Breaker        | `THGENT_CIRCUIT_BREAKER_ENABLED`              | false   | Off    |
| AgilePlus Governance   | `THGENT_AGILEPLUS_ENABLED`                    | false   | Off    |
| LiteLLM Fallback       | `THGENT_LITELLM_FALLBACK_ENABLED`             | false   | Off    |
| Research Protocol      | `THGENT_RESEARCH_PROTOCOL_ENABLED`            | false   | Off    |
| GitHub Project Sync    | `THGENT_GH_PROJECT_SYNC_ENABLED`              | false   | Off    |
| Workstream Autosync    | `THGENT_WORKSTREAM_AUTOSYNC_ENABLED`          | false   | Off    |
| Linear Sync            | `THGENT_LINEAR_SYNC_ENABLED`                  | false   | Off    |
| Adaptive Interval      | `THGENT_WORKSTREAM_ADAPTIVE_INTERVAL_ENABLED` | false   | Off    |
| Tailscale Offload      | `THGENT_TAILSCALE_ENABLED`                    | false   | Off    |

---

## Integrations (Feature-Flagged)

| Integration       | Env Variable                   | Module                        | Status   |
| ----------------- | ------------------------------ | ----------------------------- | -------- |
| Vale (prose lint) | `VALE_ENABLED`                 | `integrations/vale`           | ✅ Ready |
| Context7          | `CONTEXT7_BASE_URL`            | `integrations/context7`       | ✅ Ready |
| Beads             | `BEADS_BASE_URL`               | `integrations/beads`          | ✅ Ready |
| Graphiti          | `THEGENT_ENABLE_GRAPHITI`      | `integrations/graphiti`       | ✅ Ready |
| NATS Event Bus    | `THEGENT_EVENT_BUS=nats`       | `integrations/nats_event_bus` | ✅ Ready |
| LMCache           | `LMCACHE_ENABLED`              | `integrations/lmcache`        | ✅ Ready |
| Kratos Auth       | `THEGENT_AUTH_PROVIDER=kratos` | `integrations/kratos`         | ✅ Ready |
| PocketBase        | `THEGENT_ENABLE_POCKETBASE`    | `integrations/pocketbase`     | ✅ Ready |
| Browser-Use       | `THEGENT_BROWSER_USE_ENABLED`  | `integrations/browser_use`    | ✅ Ready |
| SearXNG           | `THEGENT_ENABLE_SEARXNG`       | `integrations/searxng`        | ✅ Ready |
| Doorstop          | `THEGENT_ENABLE_DOORSTOP`      | `integrations/doorstop`       | ✅ Ready |
| HumanLayer        | `THEGENT_ENABLE_HUMANLAYER`    | `integrations/humanlayer`     | ✅ Ready |
| Cognee            | `THEGENT_ENABLE_COGNEE`        | `integrations/cognee`         | ✅ Ready |
| ChunkHound        | `THEGENT_ENABLE_CHUNKHOUND`    | `integrations/chunkhound`     | ✅ Ready |
| OpenCode          | `THEGENT_ENABLE_OPENCODE`      | `integrations/opencode`       | ✅ Ready |
| Bifrost           | `THEGENT_ENABLE_BIFROST`       | `integrations/bifrost`        | ✅ Ready |
| Mem0              | `THEGENT_ENABLE_MEM0`          | `integrations/mem0`           | ✅ Ready |
| Portkey           | `THEGENT_ENABLE_PORTKEY`       | `integrations/portkey`        | ✅ Ready |
| FastAgent         | `THEGENT_ENABLE_FASTAGENT`     | `integrations/fastagent`      | ✅ Ready |
| Zed               | `THEGENT_ENABLE_ZED`           | `integrations/zed`            | ✅ Ready |
| Nordlys           | `THEGENT_ENABLE_NORDLYS`       | `integrations/nordlys`        | ✅ Ready |
| Humanify          | `THEGENT_ENABLE_HUMANIFY`      | `integrations/humanify`       | ✅ Ready |
| MAGG              | `THEGENT_ENABLE_MAGG`          | `integrations/magg`           | ✅ Ready |
| AgilePlus         | `THGENT_AGILEPLUS_ENABLED`     | `integrations/agileplus`      | ✅ Ready |

---

## Pre-commit Hooks (Always Available)

| Hook          | Purpose         | Status |
| ------------- | --------------- | ------ |
| Ruff (Python) | Lint/format     | ✅     |
| MyPy          | Type checking   | ✅     |
| ESLint        | JS/TS           | ✅     |
| Prettier      | Formatting      | ✅     |
| ShellCheck    | Shell scripts   | ✅     |
| GitLeaks      | Secret scanning | ✅     |
| Commitlint    | Commit messages | ✅     |

---

## Agent Skills (Factory/Droid)

Total: 40+ droids defined in `.factory/droids/`

| Category      | Count |
| ------------- | ----- |
| Code Review   | 8     |
| Security      | 6     |
| Testing       | 5     |
| DevOps        | 4     |
| Documentation | 4     |
| Research      | 5     |
| General       | 8     |

---

## MCP Servers

| Server      | Config             | Status |
| ----------- | ------------------ | ------ |
| thegent-mcp | `mcp_servers.json` | ✅     |
| Custom MCPs | Per-project        | ✅     |

---

## Infrastructure

| Component          | Technology        | Status |
| ------------------ | ----------------- | ------ |
| Process Management | `process-compose` | ✅     |
| Container Runtime  | Docker            | ✅     |
| Local Dev          | `.devcontainer/`  | ✅     |
| Shell              | Zsh + Oh-My-Zsh   | ✅     |
| Package Manager    | uv                | ✅     |

---

## Quick Enable Commands

```bash
# Enable routing
export THGENT_ROUTING_ENABLED=1

# Enable autosync
export THGENT_WORKSTREAM_AUTOSYNC_ENABLED=1

# Enable specific integration
export THEGENT_ENABLE_GRAPHITI=1
```
