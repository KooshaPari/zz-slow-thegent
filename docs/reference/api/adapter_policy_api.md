# adapter_policy API Reference

> **Source**: `src/thegent/governance/adapter_policy.py`

WP-10004: Adapter admission and trust policy.

Enforces trust-based admission rules for provider adapters.

OPT-008: LRU cache for policy evaluation results (with TTL) - `<50ms` repeated evaluations.

---

## AdapterAdmissionPolicy

Policy engine for adapter admission control with caching.

OPT-008: Uses LRU cache with TTL for repeated policy evaluations.

### Methods

#### AdapterAdmissionPolicy.**init**

```python
__init__(self: Any, registry: CapabilityRegistry, cache_ttl_sec: int)
```

Initialize policy engine.

**Parameters**:

- `registry`: Capability registry
- `cache_ttl_sec`: Cache TTL in seconds (default: 5 minutes)

---

#### AdapterAdmissionPolicy.evaluate_admission

```python
evaluate_admission(self: Any, adapter_id: str, lane: str)
```

Evaluate if an adapter can be admitted to a specific lane.

OPT-008: Caches results for repeated evaluations (`<50ms` for cached lookups).

**Parameters**:

- `adapter_id`: Adapter identifier
- `lane`: Lane name (e.g., "critical", "default")

**Returns**: Evaluation result dict with "allowed" and optional "reason"/"trust_level"

---

---

## evaluate_admission

```python
evaluate_admission(self: Any, adapter_id: str, lane: str)
```

Evaluate if an adapter can be admitted to a specific lane.

OPT-008: Caches results for repeated evaluations (`<50ms` for cached lookups).

**Parameters**:

- `adapter_id`: Adapter identifier
- `lane`: Lane name (e.g., "critical", "default")

**Returns**: Evaluation result dict with "allowed" and optional "reason"/"trust_level"

---
