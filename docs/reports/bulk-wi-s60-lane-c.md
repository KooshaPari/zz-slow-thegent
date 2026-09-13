### [WL-8540]

**Title:** Preserve session startup by separating bootstrap context and command registration
**Source:** [thegent/src/thegent/session/startup.py:387]
**Acceptance checklist:**

- [ ] Separate session bootstrap context parse failures from command registration failures.
- [ ] Keep command registration fallback on context failures.
- [ ] Add tests for bootstrap and registration branches.
      **Notes:** Improves session reliability in partially stale bootstrap states.

### [WL-8541]

**Title:** Preserve artifact stream upload by separating chunk framing and multipart completion
**Source:** [thegent/src/thegent/artifacts/stream_upload.py:442]
**Acceptance checklist:**

- [ ] Separate chunk framing failures from multipart completion failures.
- [ ] Preserve upload resume behavior when completion fails.
- [ ] Add tests for framing and completion branch behavior.
      **Notes:** Reduces upload stalls on boundary conditions.

### [WL-8542]

**Title:** Preserve queue snapshotting by separating snapshot serialization and storage write
**Source:** [thegent/src/thegent/queue/snapshot.py:333]
**Acceptance checklist:**

- [ ] Separate queue snapshot serialization failures from storage write failures.
- [ ] Preserve queue operations with in-memory snapshots.
- [ ] Add tests for serialization and storage branch behavior.
      **Notes:** Improves recovery robustness under storage contention.

### [WL-8543]

**Title:** Preserve policy rule cache by separating compile step and cache invalidation
**Source:** [thegent/src/thegent/policies/cache.py:501]
**Acceptance checklist:**

- [ ] Separate policy compile failures from cache invalidation failures.
- [ ] Preserve cache entries with conservative invalidation policy.
- [ ] Add tests for compile and invalidation branches.
      **Notes:** Reduces policy performance hits when one compile branch regresses.

### [WL-8544]

**Title:** Preserve API sync by separating cursor extraction and API call batching
**Source:** [thegent/src/thegent/api/sync_client.py:598]
**Acceptance checklist:**

- [ ] Separate sync cursor extraction failures from batching failures.
- [ ] Preserve API sync progress on cursor extraction fallback.
- [ ] Add tests for cursor and batching branches.
      **Notes:** Keeps sync throughput stable despite cursor irregularities.

### [WL-8545]

**Title:** Preserve CLI output ordering by separating command sort and serialization
**Source:** [thegent/src/thegent/cli/order.py:422]
**Acceptance checklist:**

- [ ] Separate command sort failures from output serialization failures.
- [ ] Preserve command output order with fallback sorting.
- [ ] Add tests for sort and serialization branch errors.
      **Notes:** Maintains output readability under sorting anomalies.

### [WL-8546]

**Title:** Preserve health polling by separating polling schedule and result aggregation
**Source:** [thegent/src/thegent/health/poller.py:349]
**Acceptance checklist:**

- [ ] Separate polling schedule calculation failures from aggregation failures.
- [ ] Preserve aggregation on scheduling fallback.
- [ ] Add tests for schedule and aggregate branch behavior.
      **Notes:** Improves health signal consistency under scheduler jitter.

### [WL-8547]

**Title:** Preserve connector toggles by separating toggle parse and state persistence
**Source:** [thegent/src/thegent/integrations/toggles.py:447]
**Acceptance checklist:**

- [ ] Separate connector toggle parse failures from persistence failures.
- [ ] Preserve active toggle state during persistence errors.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Keeps integration controls stable during config churn.

### [WL-8548]

**Title:** Preserve task command routing by separating command schema and route table lookup
**Source:** [thegent/src/thegent/commands/routing.py:592]
**Acceptance checklist:**

- [ ] Separate command schema validation failures from route table lookup failures.
- [ ] Preserve routing fallback for valid schema cases.
- [ ] Add tests for schema and route lookup branches.
      **Notes:** Improves command reliability under schema evolution.

### [WL-8549]

**Title:** Preserve artifact versioning by separating version parse and migration mapping
**Source:** [thegent/src/thegent/artifacts/versioning.py:478]
**Acceptance checklist:**

- [ ] Separate artifact version parse failures from migration mapping failures.
- [ ] Keep migration mapping fallback for recognized versions.
- [ ] Add tests for version and mapping branches.
      **Notes:** Reduces rollout risk when artifact versions are mixed.
