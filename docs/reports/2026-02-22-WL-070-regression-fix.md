# WL-070 Regression Fix Evidence (2026-02-22)

## Scope

Fix regression in WL-070 (`get_litellm_router` cache behavior) where distinct policy keys were evicting each other due to `TTLCache(maxsize=1)`.

## Change

- File: `src/thegent/routing/litellm_router.py`
- Updated `_router_cache` from `TTLCache(maxsize=1, ttl=300)` to `TTLCache(maxsize=8, ttl=300)`.
- Rationale: cache is keyed by policy, so it must hold multiple policy variants concurrently during TTL.

## Verification

Command:

```bash
uv run python -m pytest -q tests/test_wl070_litellm_router_cache.py
```

Result:

- `7 passed in 29.75s`
- Previously failing case now passes:
  - `test_different_policies_get_separate_cache_entries`

## Outcome

WL-070 behavior is restored: one build per unique policy within TTL window, no redundant rebuilds due to single-entry eviction.
