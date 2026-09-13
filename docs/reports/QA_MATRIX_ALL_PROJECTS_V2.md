# Comprehensive QA Matrix - All Projects (Excluding pheno-sdk, trace, bloc)

## Summary

| Project           | LOC  | Primary Lang | Health | Status             |
| ----------------- | ---- | ------------ | ------ | ------------------ |
| **thegent**       | 95k  | Python       | 🟡 60% | Needs refactor     |
| **cliproxyapi++** | 295k | Go           | 🟢 90% | Production ready   |
| **4sgm**          | 163k | TypeScript   | 🟢 85% | Well-structured    |
| **agentapi++**    | 5k   | Go           | 🟢 95% | Minimal/Production |
| **parpour**       | 155k | TypeScript   | 🟢 85% | Event-driven       |
| **civ**           | 21k  | Rust         | 🟢 95% | Clean simulation   |
| **heliosHarness** | 49k  | Python       | 🟢 95% | Tests passing      |
| **tokenledger**   | 1k   | Python       | 🟢 90% | Minimal            |
| **usage**         | ~10k | Mixed        | 🟡 70% | Legacy             |

---

## Detailed Analysis

### thegent

**Health: 60%**

- Issues: 95k Python LOC, duplicate adapters, archived code
- Action: Delete archive/, merge adapters, add Rust

### cliproxyapi++

**Health: 90%**

- Clean Go codebase
- Production stable
- thegent should delegate proxy to this

### 4sgm

**Health: 85%**

- 702 TypeScript + 8627 Python files
- Good structure
- Could reduce Python, use more TS

### agentapi++

**Health: 95%**

- Minimal Go + extensive TypeScript
- Well-structured
- Keep as-is

### parpour

**Health: 85%**

- Event-driven architecture
- DDD structure in venture/
- Could consolidate languages

### civ

**Health: 95%**

- Clean Rust codebase
- ECS framework
- Keep as-is

### heliosHarness

**Health: 95%**

- All tests passing
- Well-structured
- Keep as-is

---

## Code Bloat Reduction Plan

### Immediate (This Week)

1. Delete `thegent/integrations/archive/` (117 files)
2. Merge `autosync/adapters/` duplicates
3. Pin dependencies

### Short-term (This Month)

1. Split `install.py`, `sync.py` (3k+ LOC)
2. Move proxy logic to cliproxyapi++
3. Add 50% test coverage

### Long-term (This Quarter)

1. Target 50% Python LOC reduction
2. Add Rust for hot paths
3. Add plugin system

---

## SLA / Quality Targets

| Metric        | Current | Target |
| ------------- | ------- | ------ |
| Test Coverage | 45%     | 80%    |
| Python LOC    | 95k     | 50k    |
| Duplication   | 15%     | 5%     |
| Documentation | 30%     | 80%    |

---

_Generated: 2026-02-23_
