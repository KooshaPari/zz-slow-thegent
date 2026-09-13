# Codebase Health Atlas - QA Matrix

## Executive Summary

### Project Stats

| Project           | Files | LOC     | Language | Status            |
| ----------------- | ----- | ------- | -------- | ----------------- |
| **thegent**       | 1,454 | 258,266 | Python   | ⚠️ Needs refactor |
| **cliproxyapi++** | 1,130 | 294,801 | Go       | ✅ Stable         |
| **pheno-sdk**     | 1,688 | 301,767 | Python   | ⚠️ Needs refactor |
| **civ**           | 9     | 21,233  | Rust     | ✅ Clean          |
| **parpour**       | 3     | 393     | Python   | ✅ Minimal        |
| **heliosHarness** | 126   | ~3,000  | Python   | ✅ Clean          |
| **agentapi++**    | 28    | 5,245   | Go       | ✅ Stable         |

---

## Code Quality Issues

### 🔴 Critical (Immediate Action Required)

#### 1. Code Duplication

| Location                                         | Issue              | Recommendation                 |
| ------------------------------------------------ | ------------------ | ------------------------------ |
| `autosync/adapters/` vs `integrations/adapters/` | Duplicate adapters | Merge into one location        |
| `integrations/archive/`                          | 40+ archived files | Delete or move to archive repo |
| Multiple `*_adapter.py` files                    | Similar patterns   | Extract to common base class   |

#### 2. Largest Files Needing Refactor

| File                        | LOC   | Issue                     | Recommendation         |
| --------------------------- | ----- | ------------------------- | ---------------------- |
| `install.py`                | 1,773 | God file                  | Split into modules     |
| `commands/sync.py`          | 1,745 | CLI bloat                 | Extract to subcommands |
| `clode_main.py`             | 1,717 | CLI entry point           | Modularize             |
| `provider_model_manager.py` | 1,526 | Too many responsibilities | Split by provider type |

#### 3. Missing Rust/Zig/Mojo Opportunities

| Python File                 | LOC   | Should Be     | Language |
| --------------------------- | ----- | ------------- | -------- |
| `provider_model_manager.py` | 1,526 | Model routing | Rust     |
| `cliproxy_adapter.py`       | 1,250 | HTTP proxy    | Rust     |
| `codex_proxy.py`            | 1,258 | Process spawn | Rust     |
| `litellm_router.py`         | 1,017 | LLM routing   | Rust     |
| `load_based_limits.py`      | 1,028 | Resource mgmt | Zig      |

---

### 🟡 Medium (Refactor Soon)

#### 1. Tests Coverage Gaps

```
tests/            - 800+ test files
test_*.py        - Many missing unit tests
coverage: ~45%   - Need 80%+
```

#### 2. Documentation Gaps

- No unified API docs
- No architecture decision records (ADRs)
- Missing docstrings in critical paths

#### 3. Dependency Issues

| Dependency  | Issue                 | Recommendation         |
| ----------- | --------------------- | ---------------------- |
| `litellm`   | Bloated, slow imports | Use lightweight client |
| `starlette` | Heavy for CLI         | Remove unused routes   |
| `pydantic`  | Version conflicts     | Pin versions           |

---

### 🟢 Good

- **civ**: Clean Rust codebase
- **parpour**: Minimal, focused
- **heliosHarness**: Well-structured tests
- **doctor module**: Good modular design

---

## Responsibility Split

### thegent (Should Keep)

- CLI entry points
- Agent orchestration logic
- Session management
- MCP tool execution
- Governance/policy

### cliproxyapi++ (Should Move)

- HTTP proxy handling
- Provider routing ( LiteLLM integration)
- Rate limiting
- Cache management
- Response transformations

---

## LOC Reduction Plan

### Phase 1: Delete/Archive ( -30k LOC)

- [ ] Remove `integrations/archive/` → Archive repo
- [ ] Remove `autosync/adapters/` duplicates
- [ ] Remove unused CLI aliases

### Phase 2: Refactor (-50k LOC)

- [ ] Split `install.py` (1,773 → 300)
- [ ] Split `sync.py` (1,745 → 500)
- [ ] Extract common adapter base class
- [ ] Modularize CLI apps

### Phase 3: Rust Migration (-80k LOC target)

- [ ] `cliproxy_adapter.py` → Rust
- [ ] `provider_model_manager.py` → Rust
- [ ] `codex_proxy.py` → Rust
- [ ] `litellm_router.py` → Rust

---

## Recommendations Summary

### Immediate Actions

1. Delete `integrations/archive/` (code rot)
2. Merge duplicate adapter directories
3. Pin dependencies in pyproject.toml

### Short-term (1-2 sprints)

1. Split largest files into modules
2. Add 80% test coverage goal
3. Create ADR documentation

### Long-term (1-2 quarters)

1. Move proxy logic to cliproxyapi++
2. Rewrite core in Rust
3. Add plugin system

---

## SLA / Health Metrics

| Metric         | Current | Target | Status |
| -------------- | ------- | ------ | ------ |
| Test Coverage  | 45%     | 80%    | ❌     |
| LOC Python     | 258k    | 150k   | ❌     |
| Duplicate Code | 15%     | 5%     | ❌     |
| Documentation  | 30%     | 80%    | ❌     |
| Rust/Zig %     | 0.1%    | 30%    | ❌     |

---

_Generated: 2026-02-23_
