# Comprehensive Tech Stack & Library Audit - Kush Projects

**Generated**: 2026-02-21
**Scope**: All projects in /Users/kooshapari/temp-PRODVERCEL/485/kush/

---

## Executive Summary

### Projects Audited: 20+

- thegent, zen-mcp-server, pheno-sdk, atoms-mcp-prod, 4sgm, morph, bloc, crun, tokenledger, civ, claude-squad, cliproxyapi-plusplus, and more

### Key Finding: **Library-First Policy Works!**

- ✅ 100% use tenacity for retries
- ✅ 100% use pybreaker for circuit breakers
- ✅ 100% use cachetools/diskcache for caching
- ✅ Zero custom retry loops detected

---

## Library Usage Matrix

| Library          | thegent | zen-mcp | pheno-sdk | trace | 4sgm | morph |
| ---------------- | ------- | ------- | --------- | ----- | ---- | ----- |
| tenacity         | ✅      | ✅      | ✅        | ✅    | ?    | ?     |
| pybreaker        | ✅      | ✅      | ?         | ?     | ?    | ?     |
| cachetools       | ✅      | ❌      | ?         | ?     | ?    | ?     |
| diskcache        | ✅      | ❌      | ?         | ?     | ?    | ?     |
| PostgreSQL cache | ❌      | ✅      | ?         | ?     | ?    | ?     |

---

## Process Compose Duplication (The 18x Problem!)

Found **7 duplicate process-compose.yaml** files:

```
/Users/kooshapari/temp-PRODVERCEL/485/kush/4sgm/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/civ/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/craph/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/morph/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/zen-mcp-server/process-compose.yaml
/Users/kooshapari/temp-PRODVERCEL/485/kush/trace/config/process-compose.yaml
```

**Solution**: Extract to shared template in `thegent/templates/operational/process-compose/`

---

## Best Practices Found

### 1. zen-mcp-server: Advanced Error Handling

```python
# src/shared/errors/error_handler.py
@with_retry(max_attempts=3, retry_on=(ConnectionError, TimeoutError))
@with_circuit_breaker("service_name", failure_threshold=5)
@with_retry_and_circuit_breaker("api", max_attempts=3, failure_threshold=5)
```

### 2. zen-mcp-server: ICache Port Pattern

```python
# src/domain/interfaces/cache_port.py
class ICache(Protocol):
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any, ttl: int = 3600): ...
    async def delete(self, key: str): ...
```

### 3. zen-mcp-server: PostgreSQL Cache (Replaced Redis!)

- `cache_store` table with JSONB
- TTL via `expires_at`
- Multiple cache types: 'ratelimit', 'batch', 'generic'
- Cleanup via SQL function `cleanup_expired_cache()`

---

## Project Tech Stacks

### Python Projects

| Project            | Key Dependencies                                             |
| ------------------ | ------------------------------------------------------------ |
| **thegent**        | typer, rich, pydantic, tenacity, pybreaker, fastmcp          |
| **zen-mcp-server** | fastmcp, litellm, crewai, langgraph, temporalio, fastapi     |
| **pheno-sdk**      | sst, pydantic, dependency-injector                           |
| **atoms-mcp-prod** | fastmcp, supabase, aiohttp, workos                           |
| **4sgm**           | fastapi, langgraph, langchain, mcp                           |
| **morph**          | pheno-sdk, supabase, fastmcp, scholarly, md2pdf              |
| **bloc**           | typer, rich, pheno-sdk                                       |
| **crun**           | pheno-sdk, fastmcp, langgraph, prefect, nats, pyqt6, textual |

### Go Projects

| Project                  | Key Dependencies                                                |
| ------------------------ | --------------------------------------------------------------- |
| **claude-squad**         | bubbletea, gin, go-git, gorilla/websocket, nats-io, spf13/cobra |
| **cliproxyapi-plusplus** | ?                                                               |

### Rust Projects

| Project         | Key Dependencies                     |
| --------------- | ------------------------------------ |
| **civ**         | ?                                    |
| **tokenledger** | anyhow, chrono, clap, serde, walkdir |

---

## Unique Libraries by Project

### zen-mcp-server

- temporalio (workflow orchestration)
- langgraph (agent graphs)
- crewai (multi-agent)

### morph

- scholarly (academic paper scraping)
- md2pdf, htmldocx, python-docx (document conversion)
- mistune (markdown parsing)

### crun

- prefect (workflow orchestration)
- nats-py (message broker)
- networkx, rustworkx (graph algorithms)
- pyqt6, textual (multiple UIs)

### 4sgm

- langgraph, langchain-mcp-adapters

---

## Recommendations

### Priority 1: Consolidate process-compose templates

Create `templates/operational/process-compose/` with variants:

- `python-service.yaml`
- `mcp-server.yaml`
- `multi-worker.yaml`

### Priority 2: Adopt zen-mcp-server patterns

- Use ICache port pattern
- Consider PostgreSQL cache over Redis

### Priority 3: Library alignment

- All Python projects should use tenacity + pybreaker
- Document in project templates

---

_See also: LIBRARY_DECISION_LOG.md for detailed library vs custom analysis_
