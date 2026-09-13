# ADR-015: Immutable Audit Ledger Design

**Status:** Accepted
**Date:** 2026-02-19
**Authors:** agent-f1
**Deciders:** thegent architecture team

---

## Context

The `thegent` platform orchestrates multiple AI agents performing autonomous actions — file writes, shell commands, API calls, planning cycles — on behalf of users. Without a tamper-evident audit trail, it is impossible to:

1. Detect post-hoc modification or deletion of agent action records.
2. Reconstruct the exact sequence of events in an AgilePlus governance cycle for forensic replay.
3. Satisfy enterprise compliance requirements that demand non-repudiation of automated actions.
4. Provide evidence to governance policy engine (`qa-policy-engine.sh`) that actions occurred as reported.

The system already logs agent activity to JSONL files under `.thegent/sessions/`. The gap is that these files are mutable plain text — any process (or adversary) with filesystem access can silently alter or truncate them without detection.

Two overlapping ledger implementations exist:

- **`EvidenceLedger`** (`src/thegent/governance/evidence_ledger.py`): Per-AgilePlus-cycle evidence events; used heavily throughout `agileplus.py`.
- **`IncidentLedger`** / **`LedgerVerifier`** (`src/thegent/governance/ledger.py`): General incident / artifact records used by governance policy enforcement.

Both independently apply SHA-256 hash chaining. This ADR documents and ratifies the shared design pattern, and designates `EvidenceLedger` as the canonical reference implementation.

---

## Decision

Audit records are stored in **append-only JSONL files with SHA-256 hash chaining**. Each entry in the ledger contains:

1. **`event_type`** — semantic label for the event (e.g., `cycle_started`, `task_dispatched`, `verification_completed`).
2. **`timestamp`** — ISO-8601 UTC timestamp.
3. **`cycle_id`** — correlation identifier for the governing AgilePlus cycle.
4. **`payload`** — event-specific structured data (dict).
5. **`prev_hash`** — SHA-256 hash of the immediately preceding record (`null` for the genesis record).
6. **`hash`** — SHA-256 hash of this record's canonical JSON representation (computed over all fields except `hash` itself, with keys sorted, no whitespace).

The first record in every new ledger file is a **schema version marker** with `event: "schema_version"` and `version: 1`, which anchors the chain.

### Hash Calculation

```
canonical_json = json.dumps({k: v for k, v in record.items() if k != "hash"},
                             sort_keys=True, separators=(",", ":"))
record["hash"] = sha256(canonical_json.encode()).hexdigest()
```

### Chain Verification

To verify integrity, iterate all records in order:

1. Recompute the expected hash from the record's fields (excluding `hash`).
2. Assert `record["hash"] == expected_hash`. Any mismatch indicates the record was altered.
3. Assert `record["prev_hash"] == hash_of_previous_record`. Any mismatch indicates a record was inserted, deleted, or reordered.

A `verify_chain()` method on `EvidenceLedger` provides this in O(n) time with O(1) memory.

### File Layout

```
.thegent/sessions/agileplus/evidence_ledger.jsonl   # EvidenceLedger
.thegent/sessions/<custom-path>/incident.jsonl       # IncidentLedger (governance / omega-safety)
```

Files are opened in append mode (`"a"`) exclusively. No record is ever overwritten or deleted by normal operation.

---

## Consequences

### Positive

- **Tamper detection**: Any modification (insert, delete, or edit) to any record in the chain is detectable by replaying `verify_chain()`.
- **Portability**: Plain JSONL files require no database, broker, or network service. They are readable with standard Unix tools (`jq`, `rg`) and trivially transferable.
- **No external dependency**: The implementation uses only Python stdlib (`hashlib`, `json`, `pathlib`) plus `pydantic` (already a core project dependency).
- **Forensic replay**: Because events contain `cycle_id` and full payloads, any AgilePlus cycle can be reconstructed entirely from the ledger without consulting live state.
- **Streaming-friendly**: Records are appended one at a time. No full-file rewrites are needed; ledgers survive incomplete writes (the corrupt tail line is detectable via `verify_chain()`).
- **Queryable**: `EvidenceLedger.query(cycle_id=..., event_type=...)` supports lightweight in-process filtering without a query engine.

### Negative / Trade-offs

- **O(n) verification cost**: Full chain verification scales linearly with ledger size. For very long-running systems accumulating millions of records, periodic archival and re-anchoring is required (not yet implemented; see Open Questions).
- **No concurrent writers**: The `open("a")` pattern is safe for a single writer per file on POSIX filesystems, but concurrent multi-process writers to the same file path require external locking. Current usage is single-writer per session directory.
- **No encryption**: Hashing provides integrity but not confidentiality. Payloads containing sensitive data (agent outputs, tool call arguments) are stored in plaintext.
- **No remote replication**: If the local filesystem is fully compromised (including the ledger), the chain cannot self-prove its own integrity without an external anchor (e.g., a periodic hash published to a remote store). This is out of scope for the current implementation.
- **Rolling hash variant divergence**: `IncidentLedger` in `ledger.py` uses a slightly different serialization strategy (string concatenation splitting on `,"rolling_hash"` vs. the `sort_keys` JSON approach in `EvidenceLedger`). Both are functionally correct but are not cross-verifiable. Future work should unify on `EvidenceLedger`'s approach.

---

## Alternatives Considered

### 1. SQLite with Write-Ahead Log (WAL)

**Rejected.** SQLite files are mutable; records can be `UPDATE`d or `DELETE`d silently. WAL provides crash recovery, not tamper evidence. Adding a separate integrity check layer would recreate the hash-chaining logic on top of SQLite anyway, with added complexity and a binary file format opaque to standard tools.

### 2. Append-only S3 / Object Storage

**Rejected for local dev.** Requiring an S3-compatible store as a runtime dependency for local development and single-user deployments is a disproportionate operational burden. S3 Object Lock provides immutability guarantees, but only for cloud-hosted deployments. The JSONL approach is portable across local and cloud; a future egress adapter could mirror to S3 without changing the core format.

### 3. OpenTelemetry Spans

**Rejected.** OTEL spans are designed for distributed tracing and observability, not tamper-evident audit. OTEL exporters (OTLP, Jaeger, Zipkin) can drop, sample, or batch records. The collector is an additional runtime service. Hash chaining is not part of the OTEL data model. OTEL remains appropriate for performance observability; it is complementary, not a replacement.

### 4. Write-once filesystem flags (e.g., `chattr +a`)

**Rejected.** Filesystem-level append-only flags require elevated privileges to set and are platform-specific (Linux `ext4`/`xfs`; not available on macOS `HFS+`/`APFS` in the same form). They also do not detect tampering of already-appended content — only prevent deletion or overwriting. Cross-platform portability is a hard requirement for `thegent`.

### 5. Signed JWT / HMAC per-record (symmetric key)

**Considered but deferred.** Per-record HMAC with a shared secret would make ledger records independently verifiable without replaying the chain. The cost is key management: the secret must be stored separately from the ledger, or the scheme is circular. SHA-256 hash chaining without a key is sufficient for the current threat model (filesystem access by unauthorized processes, not a malicious insider who also controls the verification process). HMAC signing is noted as a future enhancement.

---

## Implementation Reference

| Component                        | File                                        | Role                                                                                |
| -------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------- |
| `EvidenceLedger` (canonical)     | `src/thegent/governance/evidence_ledger.py` | AgilePlus cycle evidence; `record()`, `query()`, `verify_chain()`                   |
| `EvidenceEvent` (Pydantic model) | `src/thegent/governance/evidence_ledger.py` | Schema for each ledger entry                                                        |
| `IncidentLedger`                 | `src/thegent/governance/ledger.py`          | Governance/omega-safety incident records; `record_artifact()`, `verify_integrity()` |
| `LedgerVerifier`                 | `src/thegent/governance/ledger.py`          | Standalone chain verification for arbitrary ledger paths                            |
| `AgilePlusRunner`                | `src/thegent/governance/agileplus.py`       | Primary consumer of `EvidenceLedger`; records all cycle lifecycle events            |
| `omega_safety`                   | `src/thegent/verification/omega_safety.py`  | References `evidence_ledger` for safety gate evidence                               |
| `artifacts/api.py`               | `src/thegent/artifacts/api.py`              | Uses `verify_hash_chain()` for artifact integrity at ingest                         |

### Event Types Recorded by EvidenceLedger

| Constant                 | Value                      | When Emitted                   |
| ------------------------ | -------------------------- | ------------------------------ |
| `CYCLE_STARTED`          | `"cycle_started"`          | AgilePlus cycle begins         |
| `SCAN_COMPLETED`         | `"scan_completed"`         | Work stream scan finishes      |
| `PLAN_CREATED`           | `"plan_created"`           | Planning phase produces a plan |
| `TASK_DISPATCHED`        | `"task_dispatched"`        | Task sent to an agent          |
| `TASK_COMPLETED`         | `"task_completed"`         | Agent reports task completion  |
| `VERIFICATION_COMPLETED` | `"verification_completed"` | Verification gate passes/fails |
| `CYCLE_COMPLETED`        | `"cycle_completed"`        | Full AgilePlus cycle finishes  |

---

## Open Questions

1. **Archival and re-anchoring strategy**: For long-running deployments, the ledger will grow unbounded. A roll-over protocol is needed: close the current ledger, publish its final hash as the genesis `prev_hash` of a new ledger file, and archive the old file.
2. **Unification of `EvidenceLedger` and `IncidentLedger`**: The two implementations should be merged or made cross-verifiable. The canonical approach (`sort_keys` JSON + excluding `hash` field) from `EvidenceLedger` should be adopted in `IncidentLedger`.
3. **HMAC signing**: Future enhancement to add per-record HMAC signatures for independent record verification without full chain replay.
4. **Remote anchor**: Periodic publication of the chain head hash to a remote, append-only store (e.g., S3 with Object Lock, or a public blockchain commitment) would defeat adversaries with full local filesystem access.
5. **Concurrent writer safety**: If multiple processes must write to the same ledger (e.g., in a multi-agent swarm), a file-level lock (via `fcntl.flock` or a `LockFile` wrapper using `filelock`) must be added before `record()` calls.

---

## Cross-References

- `ADR.md` — Master ADR index
- `src/thegent/governance/evidence_ledger.py` — Canonical implementation
- `src/thegent/governance/ledger.py` — Incident ledger implementation
- `src/thegent/governance/agileplus.py` — Primary consumer
- `docs/reference/WORK_STREAM.md` — Work stream item `adr-015-immutable-ledger`
