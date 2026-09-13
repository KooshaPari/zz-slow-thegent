# phenoSDK `src/pheno/ports` inventory (Wave A kickoff)

**Tree:** `repos/worktrees/phenoSDK/main/src/pheno/ports`  
**AgilePlus:** `phenosdk-wave-a-contracts`

## Top-level modules (Python)

| Module / package             | Role (from naming)                                                                                    |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| `__init__.py`                | Package exports                                                                                       |
| `authentication.py`          | Auth port                                                                                             |
| `auth/`                      | Auth sub-ports (`providers.py`)                                                                       |
| `database.py`                | Persistence port                                                                                      |
| `inference.py`               | LLM / model inference port                                                                            |
| `messaging.py`               | Message bus / queue port                                                                              |
| `observability.py`           | Metrics/tracing port                                                                                  |
| `registry.py`                | Service or plugin registry                                                                            |
| `stream.py`                  | Streaming I/O                                                                                         |
| `tunnels.py`, `tunneling.py` | Network tunnel abstractions                                                                           |
| `port_allocation.py`         | Dynamic port allocation                                                                               |
| `mcp/`                       | MCP: `provider.py`, `session_manager.py`, `tool_registry.py`, `resource_provider.py`, `monitoring.py` |

## Next steps (Wave A)

**Done (subagent):** see **`PHENOSDK_WAVE_A_RECON_2026-03-29.md`** — MCP + auth.providers + stream are the first three contract targets; many `ports/__all__` modules lack adapter imports yet.

1. Reconcile `pheno.ports.*` vs `application.ports` / `adapter_kit` before extracting database/inference/messaging schemas.
2. Export FastAPI `openapi.json` from `adapters/api/app.py` into a committed artifact when ready for SDD.
3. Extract MCP/auth/stream DTOs into a versioned package or Proto/OpenAPI under Phenotype template libs.

## Command hints

```bash
rg "class.*Port|Protocol" repos/worktrees/phenoSDK/main/src/pheno/ports --type py
rg "ports\." repos/worktrees/phenoSDK/main/src/pheno/adapters --type py | head -40
```
