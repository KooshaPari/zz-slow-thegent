# pareto_router API Reference

> **Source**: `src/thegent/routing/pareto_router.py`

Pareto-first router: hard constraints → Pareto frontier → lexicographic selection.

Implements the ChatGPT Pareto research design:

- Offer = provider + model + cost_weight + quality proxy
- Hard constraints filter first (capability, cost cap, quality floor)
- Pareto frontier = non-dominated offers on (speed, cost, quality)
- Lexicographic tie-break: quality → cost → speed (role-specific soft_order)
- Shadow pricing when budget pressure (Phase 1)
- Degraded mode at 85% budget burn (cheap offers only)
- Route trace output (Phase 0)

---

## Offer

Routable offer: provider + model + indices.

---

## RoleConfig

Role definition from roles.schema.yaml (Helios spec).

---

## RouteTrace

Route trace output per Helios spec (why offer won).

---

## key

```python
key(o: Offer) -> tuple[(float, float, float)]
```

---

## select_offer

```python
select_offer(complexity_tier: str, min_quality: float, max_cost_weight: float, opt_order: tuple[(str, Ellipsis)], role: Any)
```

Select (provider, model_alias) via Pareto + lexicographic.

**Parameters**:

- `complexity_tier`: simple | moderate | complex (adjusts min_quality)
- `min_quality`: Minimum quality floor (0-1)
- `max_cost_weight`: Maximum cost weight
- `opt_order`: Lexicographic order (overridden by role if set)
- `role`: Role name (fast_chat, doc_writer, code_complex, high_accuracy) for role-specific params

**Returns**: (provider, model_alias) or None

---

## select_offer_with_fallbacks

```python
select_offer_with_fallbacks(complexity_tier: str, min_quality: float, max_cost_weight: float, k: int, role: Any)
```

Select primary + fallback chain (top k from Pareto frontier by lexicographic).

Uses role from roles.schema.yaml when provided.

**Returns**: [(provider, model_alias), ...] primary first

---

## select_offer_with_trace

```python
select_offer_with_trace(complexity_tier: str, min_quality: float, max_cost_weight: float, opt_order: tuple[(str, Ellipsis)], role: Any)
```

Select offer with full route trace (why offer won). Per Helios spec.

Uses role from roles.schema.yaml when provided (min_quality, soft_order, output_tokens_multiplier).

---
