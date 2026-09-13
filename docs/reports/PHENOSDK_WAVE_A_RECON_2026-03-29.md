# phenoSDK Wave A — ports & contracts reconnaissance (2026-03-29)

**Source:** subagent scan of `repos/worktrees/phenoSDK/main` (read-only).  
**AgilePlus:** `phenosdk-wave-a-contracts`

## `src/pheno/ports/` — 19 Python files

Full inventory: `__init__.py`, `authentication.py`, `database.py`, `inference.py`, `messaging.py`, `observability.py`, `port_allocation.py`, `registry.py`, `stream.py`, `tunneling.py`, `tunnels.py`, `auth/__init__.py`, `auth/providers.py`, `mcp/__init__.py`, `mcp/monitoring.py`, `mcp/provider.py`, `mcp/resource_provider.py`, `mcp/session_manager.py`, `mcp/tool_registry.py`.

**Note:** `ports/__init__.py` `__all__` omits **`mcp`** though `ports/mcp/` exists as a real package.

## Imports of `pheno.ports` in adapters / infra

| Area                        | Finding                                                                                                                                                             |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/pheno/adapters/`       | **`pheno.ports.auth.providers`** only — `AuthProvider`, `MFAAdapter` in `adapters/auth/**`.                                                                         |
| `src/pheno/infra/`          | No direct `pheno.ports` imports found.                                                                                                                              |
| `src/pheno/infrastructure/` | No direct `pheno.ports` imports found.                                                                                                                              |
| **Outside those paths**     | **`pheno.ports.mcp`** implemented under **`src/pheno/mcp/adapters/`** (not under `adapters/`). **`pheno.ports.stream`** used from `stream.py`, dev utils, examples. |

**Comment drift:** `adapters/llm/__init__.py` mentions `pheno.ports.llm` (no such package); `adapters/events/__init__.py` mentions `pheno.ports.events` (missing).

## Port ↔ adapter clarity

| Port area                                                                           | Clarity                                                                                                        |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `ports.mcp`                                                                         | **Clear** — `mcp/adapters/*`, schemes, manager, tests.                                                         |
| `ports.auth.providers`                                                              | **Clear** — `adapters/auth/**`, `application/auth/manager.py`.                                                 |
| `ports.stream`                                                                      | **Mixed** — embedded in feature code, no `adapters/stream/`.                                                   |
| `database`, `inference`, `messaging`, `observability`, `registry`, `authentication` | **Unclear** — little/no `from pheno.ports.<x>` usage; persistence/LLM use `application.ports` / `adapter_kit`. |
| `port_allocation`, `tunneling`, `tunnels`                                           | **Unclear** — weak coupling to port protocols.                                                                 |

## Existing contract artifacts

- **No** `contracts/` at repo root.
- **No** committed OpenAPI/Proto under `docs/` (JSON there is Atlas health/test data).
- **Elsewhere:** `examples/grpc_proto/echo.proto`; `schemas/` with JSON; FastAPI `openapi_url` in `adapters/api/app.py` (runtime); human doc `docs/PORT_DEFINITIONS.md`.

## Recommended first three extractions (Wave A)

1. **`pheno.ports.mcp`** — Stable protocol bundle, dedicated adapters, high fan-in.
2. **`pheno.ports.auth.providers`** — Security boundary; only port family heavily imported from `adapters/`.
3. **`pheno.ports.stream`** — Shared DTOs for streaming; smaller surface before more adapters.

## Gap

Reconciling **`pheno.ports.*`** with **`pheno.application.ports`** / **`adapter_kit`** before extracting schemas for database, inference, messaging, etc.
