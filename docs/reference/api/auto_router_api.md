# auto_router API Reference

> **Source**: `src/thegent/routing/auto_router.py`

Auto router: uses headless Gemini Flash to classify task complexity, then Pareto routing.

Flow:

1. Classify prompt via Gemini Flash (simple | moderate | complex)
2. Select (provider, model) from Pareto frontier based on complexity
3. Return resolved agent + model for run_impl

---

## AutoRouteResult

Result from auto router.

---

## auto_route

```python
auto_route(prompt: str, classifier_model: str, use_classifier: bool, min_quality: float, max_cost_weight: float, role: Any)
```

Auto-route: classify prompt, then Pareto select (agent, model).

**Parameters**:

- `prompt`: User prompt (preview used for classification)
- `classifier_model`: Model for classification (headless)
- `use_classifier`: If False, assume "moderate" complexity
- `min_quality`: Minimum quality floor
- `max_cost_weight`: Max cost weight
- `role`: Override role (fast_chat, doc_writer, code_complex, high_accuracy). If None, inferred from complexity.

**Returns**: AutoRouteResult or None if routing fails

---
