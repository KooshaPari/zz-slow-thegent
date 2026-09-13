<DONE>
# Governance Override Expired Event - Implementation Status

> **WORK_STREAM ID:** gov-wp-3003-enhance
> **Priority:** P3 (Optional Enhancement)
> **Status:** ✅ Complete

## Summary

This work item implements emission of `governance.override.expired` events when cached overrides are used but the record has expired.

## Implementation Status

### ✅ Implementation Complete

The governance override expired event is implemented in:

1. **`src/thegent/governance/override_expired.py`**:
   - `OverrideExpirationHandler` class
   - `emit_expired_event()` method
   - Event structure: `{"type": "governance.override.expired", ...}`

2. **`src/thegent/governance/overrides.py`** (lines 84-90):
   - Emits `governance.override.expired` log event when override expires
   - Logs: `policy_id`, `by`, `expires_at`
   - Cleans up expired override files

### Implementation Details

```python
# src/thegent/governance/overrides.py
# WP-3003: Emit governance.override.expired when override has expired
_log.info(
    "governance.override.expired policy_id=%s by=%s expires_at=%s",
    policy_id,
    override.by,
    override.expires_at,
)
```

### Event Structure

```python
{"type": "governance.override.expired", "override_id": str, "policy": str, "expired_at": datetime.isoformat()}
```

### Configuration

Override TTL is configurable via:
- `THGENT_OVERRIDE_TTL_SECONDS` environment variable
- Default: 24 hours (86400 seconds)
- Documented in `src/thegent/config.py` (line 415)

## Usage

The expired event is automatically emitted when:
1. An override is checked via `OverrideManager.has_unexpired()`
2. The override's `expires_at` timestamp has passed
3. The override file is cleaned up

## Acceptance Criteria

- [x] `governance.override.expired` event emitted
- [x] Event includes policy_id, by, expires_at
- [x] Expired overrides cleaned up
- [x] TTL configurable via environment variable
- [x] Implementation documented

## References

- [GOVERNANCE_WP_GAPS.md](./GOVERNANCE_WP_GAPS.md) - Original gap document
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
- [WP-3003](../plans/02-UNIFIED-WBS.md#wp-3003) - Override path with TTL
