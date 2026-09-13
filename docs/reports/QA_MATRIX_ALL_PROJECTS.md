# QA Matrix - All Projects

## Summary Matrix

| Project           | Type         | LOC   | Files | Language   | Health | Notes              |
| ----------------- | ------------ | ----- | ----- | ---------- | ------ | ------------------ |
| **thegent**       | CLI/Agent    | 258k  | 1,454 | Python     | 🟡 60% | Needs refactor     |
| **cliproxyapi++** | Gateway      | 295k  | 1,130 | Go         | 🟢 90% | Production ready   |
| **pheno-sdk**     | SDK          | 302k  | 1,688 | Python     | 🟡 65% | Extensive patterns |
| **civ**           | Simulation   | 21k   | 9     | Rust       | 🟢 95% | Clean              |
| **parpour**       | Event System | ~200k | 667   | TypeScript | 🟢 85% | Well-structured    |
| **heliosHarness** | Testing      | 3k    | 126   | Python     | 🟢 95% | 19/19 tests        |
| **agentapi++**    | Agent API    | 5k    | 28    | Go         | 🟢 95% | Minimal            |

---

## thegent Detailed Analysis

### Code Quality Score: 60/100

#### Strengths

- ✅ Good modular structure (doctor, contracts, mcp packages)
- ✅ Adapter port pattern implemented
- ✅ Type hints throughout
- ✅ Tests exist (26 passing in contracts)

#### Issues

- ❌ 258k LOC Python (too large)
- ❌ Duplicate adapters (autosync/ + integrations/)
- ❌ 40+ archived files in integrations/archive/
- ❌ Largest file (install.py) is 1,773 LOC
- ❌ Test coverage ~45%
- ❌ No Rust/Zig for performance-critical code

#### Refactor Priority

1. **HIGH**: Delete integrations/archive/
2. **HIGH**: Merge autosync/ and integrations/ adapters
3. **MEDIUM**: Split install.py, sync.py
4. **MEDIUM**: Move proxy logic to cliproxyapi++
5. **LOW**: Add Rust modules for hot paths

---

## cliproxyapi++ Detailed Analysis

### Code Quality Score: 90/100

#### Strengths

- ✅ Clean Go codebase
- ✅ Production stable
- ✅ Good test coverage
- ✅ Proper error handling

#### Issues

- ⚠️ Some legacy code paths
- ⚠️ Could benefit from more interface-based design

#### Recommendations

- Keep as-is for proxy functionality
- thegent should delegate HTTP proxy to this

---

## civ Detailed Analysis

### Code Quality Score: 95/100

#### Strengths

- ✅ Clean Rust codebase
- ✅ Proper crate organization
- ✅ Fixed-point arithmetic for determinism
- ✅ ECS framework

#### Structure

```
crates/
├── engine/     # Core simulation
├── io/          # Input/output
├── metrics/     # Statistics
├── policy/      # Game rules
└── server/      # API
```

#### Recommendations

- ✅ Keep as-is
- Could add WASM compilation for web

---

## parpour Detailed Analysis

### Code Quality Score: 85/100

#### Strengths

- ✅ Well-organized DDD structure (venture/\*)
- ✅ Good TypeScript coverage
- ✅ Event-driven architecture
- ✅ Clear bounded contexts

#### Structure

```
venture/
├── api/         # FastAPI endpoints
├── eventbus/    # NATS integration
├── ledger/      # Database schema
├── compiler/    # DSL compiler
├── compliance/  # Policy engine
├── orchestrator/# Workflow
├── policy/      # Rules
├── runtime/     # Execution
├── treasury/    # Financial
└── ...
```

#### Issues

- ⚠️ Mixed Python (3 files) + TypeScript (667 files)
- ⚠️ Could consolidate to single language

#### Recommendations

- Keep TypeScript for core
- Move Python pieces to dedicated micro-service
- Consider Rust for performance-critical paths

---

## Recommendations Summary

### Immediate Actions (This Week)

1. Delete `thegent/src/thegent/integrations/archive/`
2. Merge duplicate adapter directories
3. Pin all dependencies in pyproject.toml

### Short-term (This Month)

1. Split `install.py` into modules
2. Add 50% test coverage
3. Create ADRs folder

### Long-term (This Quarter)

1. Move HTTP proxy to cliproxyapi++
2. Add Rust modules for hot paths
3. Achieve 80% test coverage
4. Target 50% LOC reduction

---

## SLA Targets

| Metric        | Current | Q1 Target | Q2 Target |
| ------------- | ------- | --------- | --------- |
| Test Coverage | 45%     | 65%       | 80%       |
| Python LOC    | 258k    | 200k      | 150k      |
| Rust/Zig %    | 0.1%    | 5%        | 15%       |
| Documentation | 30%     | 60%       | 80%       |
| Duplication   | 15%     | 8%        | 5%        |

---

_Generated: 2026-02-23_
