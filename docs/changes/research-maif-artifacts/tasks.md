---
task_id: research-maif-artifacts
status: in_progress
---

# Research: MAIF Action Artifacts — Implementation Tasks

**Status**: Ready for Implementation | **Effort**: 8-12 tool calls | **Timeline**: 2-3 weeks

---

## Task Breakdown

### Phase 1: Foundation (Tool Calls: 1-3)

#### Task 1.1: Core Data Model

**Goal**: Define and implement MAIF artifact structures
**Effort**: 1-2 tool calls

**Subtasks**:

- [ ] Create `thegent/src/thegent/maif/models.py` with Pydantic models:
  - `ActionType` enum
  - `MAIFArtifact` dataclass
  - Validation rules
- [ ] Define serialization format (deterministic JSON)
- [ ] Add unit tests for model validation

**Acceptance**: `pytest tests/maif/test_models.py` passes with 100% coverage

**Dependencies**: None

---

#### Task 1.2: Cryptographic Foundation

**Goal**: Set up signing and hashing infrastructure
**Effort**: 1-2 tool calls

**Subtasks**:

- [ ] Generate RSA-2048 key pair (or use existing)
- [ ] Create `thegent/src/thegent/maif/crypto.py`:
  - `SigningKey` class (RSA-2048 signing)
  - `VerifyingKey` class (signature verification)
  - Deterministic hash function (SHA-256)
- [ ] Add tests for sign/verify round-trip
- [ ] Set up key storage in secrets manager

**Acceptance**: `pytest tests/maif/test_crypto.py` passes; sign→verify succeeds

**Dependencies**: None

---

### Phase 2: Artifact Generation & Storage (Tool Calls: 4-7)

#### Task 2.1: Artifact Generator

**Goal**: Create MAIF artifacts from actions
**Effort**: 2 tool calls

**Subtasks**:

- [ ] Implement `MAIFArtifactGenerator` class (design § 2.1):
  - `create_artifact()` method
  - Hash chain tracking per session
  - Signature generation
- [ ] Add unit tests:
  - Artifact creation
  - Hash chain correctness
  - Signature verification
- [ ] Performance test: artifact creation <1ms

**Acceptance**: `pytest tests/maif/test_artifact_generator.py` passes; latency <1ms

**Dependencies**: Task 1.1, 1.2

---

#### Task 2.2: Hash Chain Validator

**Goal**: Verify artifact integrity and detect tampering
**Effort**: 1-2 tool calls

**Subtasks**:

- [ ] Implement `HashChainValidator` class (design § 2.2):
  - `verify_chain()` method
  - Signature verification per artifact
  - Chain continuity checking
- [ ] Add unit tests:
  - Valid chain (should pass)
  - Tampered artifacts (should fail)
  - Broken chains (should fail)
  - Signature verification failures
- [ ] Performance test: verify 1000 artifacts <100ms

**Acceptance**: `pytest tests/maif/test_hash_chain.py` passes; latency <100ms

**Dependencies**: Task 1.1, 1.2, 2.1

---

#### Task 2.3: L4 Storage Integration

**Goal**: Persist artifacts to Supermemory Documents API
**Effort**: 2 tool calls

**Subtasks**:

- [ ] Implement `MAIFStorage` class (design § 2.3):
  - `store()` method (L4 with fallback to L2)
  - `retrieve()` method (L4 with fallback)
  - `retrieve_by_session()` method
  - `retrieve_by_query()` method
- [ ] Implement fallback logic:
  - Local in-memory cache (L1)
  - Local disk cache (L2)
  - Circuit breaker (fail after 3 consecutive failures)
- [ ] Add integration tests with Supermemory mock
- [ ] Performance test: store <200ms, retrieve <100ms

**Acceptance**: Integration tests pass; fallback works; latency met

**Dependencies**: Task 2.1, 2.2; Supermemory client available

---

### Phase 3: Hook Integration (Tool Calls: 8-9)

#### Task 3.1: Action Hooks

**Goal**: Intercept actions and create artifacts
**Effort**: 1-2 tool calls

**Subtasks**:

- [ ] Create `hooks/maif-artifact-hooks.sh` (design § 2.4):
  - PostToolUse hook for Write/Edit/Delete
  - Conditional creation for Bash (significant calls only)
  - Filter trivial operations (ls, pwd, echo)
- [ ] Add `thegent_maif_gen` CLI entrypoint
- [ ] Add logging and error handling
- [ ] Test hook integration:
  - Create artifact on Write → verify artifact exists
  - Filter trivial Bash calls → verify no artifacts
  - Supermemory unavailable → verify fallback to L2

**Acceptance**: Hooks fire correctly; artifacts created for all significant actions

**Dependencies**: Task 2.1, 2.2, 2.3

---

### Phase 4: APIs & Queries (Tool Calls: 10-11)

#### Task 4.1: Public APIs

**Goal**: Expose artifact creation and verification APIs
**Effort**: 1-2 tool calls

**Subtasks**:

- [ ] Create `thegent/src/thegent/maif/api.py`:
  - `create_artifact()` function (design § 4.1)
  - `verify_artifact_chain()` function (design § 4.2)
  - `query_artifacts()` function (design § 4.3)
- [ ] Add FastAPI endpoints (if MCP integration required):
  - `POST /maif/artifacts` — Create artifact
  - `GET /maif/artifacts/{id}` — Retrieve artifact
  - `GET /maif/artifacts?session_id=X` — Query by session
  - `POST /maif/verify?session_id=X` — Verify chain
- [ ] Add async/await support throughout
- [ ] Add comprehensive docstrings with examples

**Acceptance**: All endpoints functional; tests pass; 95%+ coverage

**Dependencies**: All Phase 1-3 tasks

---

### Phase 5: Testing & Validation (Tool Calls: 12)

#### Task 5.1: Integration Tests

**Goal**: Validate end-to-end workflow
**Effort**: 1 tool call

**Subtasks**:

- [ ] Create `tests/maif/test_integration.py`:
  - End-to-end: action → artifact creation → storage → retrieval → verification
  - Concurrent artifacts (multiple sessions)
  - Failure scenarios (L4 unavailable, corrupted artifacts)
  - Performance benchmarks (10k artifacts)
- [ ] Create `tests/maif/test_e2e_hooks.py`:
  - Hook integration (Write → artifact)
  - Hook filtering (trivial Bash calls)
  - Error handling (hook failures non-fatal)
- [ ] Load test: 1000 artifacts/second creation rate
- [ ] Verify >90% code coverage

**Acceptance**: All integration tests pass; coverage >90%; load test meets targets

**Dependencies**: All Phase 1-4 tasks

---

## Detailed Subtasks by Component

### Component: `MAIFArtifactGenerator`

| Subtask                        | Effort    | Blocker?     |
| ------------------------------ | --------- | ------------ |
| Create class skeleton          | 0.5 calls | No           |
| Implement `create_artifact()`  | 1 call    | No           |
| Implement hash chain tracking  | 0.5 calls | No           |
| Implement signature generation | 1 call    | Yes (crypto) |
| Add unit tests                 | 1 call    | No           |
| Performance benchmarking       | 0.5 calls | No           |

**Total**: 4.5 calls

---

### Component: `HashChainValidator`

| Subtask                          | Effort    | Blocker?     |
| -------------------------------- | --------- | ------------ |
| Create class skeleton            | 0.5 calls | No           |
| Implement `verify_chain()`       | 1 call    | No           |
| Implement signature verification | 1 call    | Yes (crypto) |
| Add unit tests (happy path)      | 1 call    | No           |
| Add unit tests (failure cases)   | 1 call    | No           |
| Performance benchmarking         | 0.5 calls | No           |

**Total**: 5 calls

---

### Component: `MAIFStorage`

| Subtask                     | Effort    | Blocker?               |
| --------------------------- | --------- | ---------------------- |
| Create class skeleton       | 0.5 calls | No                     |
| Implement L4 store          | 1 call    | Yes (Supermemory)      |
| Implement L4/L2 fallback    | 1 call    | No                     |
| Implement retrieval methods | 1.5 calls | No                     |
| Add integration tests       | 1 call    | Yes (Supermemory mock) |
| Performance benchmarking    | 0.5 calls | No                     |

**Total**: 5.5 calls

---

### Component: Hooks & CLI

| Subtask                         | Effort    | Blocker? |
| ------------------------------- | --------- | -------- |
| Create `maif-artifact-hooks.sh` | 1 call    | No       |
| Create `thegent_maif_gen` CLI   | 1 call    | No       |
| Test hook integration           | 1 call    | No       |
| Add filtering logic             | 0.5 calls | No       |
| Add error handling              | 0.5 calls | No       |

**Total**: 4 calls

---

### Component: APIs & Documentation

| Subtask                          | Effort    | Blocker? |
| -------------------------------- | --------- | -------- |
| Create public API functions      | 1 call    | No       |
| Add FastAPI endpoints (optional) | 1 call    | No       |
| Add docstrings & examples        | 0.5 calls | No       |
| Integration tests                | 1 call    | No       |

**Total**: 3.5 calls

---

## Verification Checklist

Before marking WP-3002 complete, verify:

### Code Quality

- [ ] All code passes linters (ruff, type checker)
- [ ] Coverage >90% for core modules
- [ ] No security vulnerabilities (bandit, semgrep)
- [ ] Performance benchmarks meet targets
- [ ] Documentation complete (docstrings, API docs)

### Functional

- [ ] Artifact creation with signature works
- [ ] Hash chain verification works
- [ ] Supermemory L4 storage works
- [ ] Fallback to local cache works
- [ ] All hooks fire correctly
- [ ] APIs functional and well-tested

### Integration

- [ ] Works with Supermemory L3/L4
- [ ] Integration with Action Dispatcher
- [ ] Integration with Lifecycle loop
- [ ] No regressions in existing systems

### Performance

- [ ] Artifact creation <1ms
- [ ] Hash chain verification (1000 artifacts) <100ms
- [ ] Storage latency <200ms
- [ ] Query latency <500ms (10k artifacts)
- [ ] Load test: 1000 artifacts/second sustainable

### Security

- [ ] RSA-2048 keys securely stored
- [ ] Signatures verified correctly
- [ ] No key leakage in logs
- [ ] Tamper detection working
- [ ] No PII in unencrypted metadata

### Operational

- [ ] Monitoring/logging in place
- [ ] Error alerts configured
- [ ] Fallback mechanisms tested
- [ ] Circuit breaker working
- [ ] Runbook created

---

## Related Work Items

**Depends On**:

- WP-5001-SM: Supermemory client library
- WP-5001: Lifecycle loop architecture

**Enables**:

- WP-4007: Simulation & replay engine
- WP-AUDIT: Audit system
- WP-COMPLIANCE: Regulatory compliance

**Preconditions**:

- Supermemory L4 API available
- RSA key pair generated
- CI/CD pipeline functional

---

## Success Metrics

| Metric                          | Target                           | Pass/Fail |
| ------------------------------- | -------------------------------- | --------- |
| Code coverage                   | >90%                             | ☐         |
| Test pass rate                  | 100%                             | ☐         |
| Artifact creation latency       | <1ms                             | ☐         |
| Hash chain verification latency | <100ms (1k artifacts)            | ☐         |
| Supermemory integration         | Functional                       | ☐         |
| Hook integration                | All significant actions captured | ☐         |
| Fallback mechanisms             | Working                          | ☐         |
| Security review                 | Zero critical findings           | ☐         |
| Documentation                   | Complete                         | ☐         |

---

## Estimated Effort

**Total Tool Calls**: 8-12 (breakdown above by phase)
**Estimated Timeline**: 2-3 weeks (parallel work possible)
**Blocking Dependencies**: Supermemory L4 API, RSA key setup

---

## Implementation Notes

1. **Start with Phase 1**: Get data model and crypto working first
2. **Test as you go**: Write tests for each component before moving to next
3. **Performance benchmarks**: Run latency tests at end of each phase
4. **Integration testing**: Leave comprehensive integration tests for Phase 5
5. **Documentation**: Add docstrings as you implement; don't defer
6. **Security review**: Get security team review before deployment

---

## References

- [proposal.md](proposal.md) — Requirements and scope
- [design.md](design.md) — Technical architecture
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md § 4](../SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#4-maif-action-artifacts) — Research foundation
- Design section § 2 for detailed component specs
- Design section § 4 for API contracts
