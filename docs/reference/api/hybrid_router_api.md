# hybrid_router API Reference

> **Source**: `src/thegent/models/hybrid_router.py`

WP-20002: Neural-Symbolic Hybrid Router.

Combines symbolic risk assessment with neural model capabilities for safety-first routing.

---

## HybridRouter

Combines LLM (Neural) and Symbolic (Formal) methods for model routing.

### Methods

#### HybridRouter.**init**

```python
__init__(self: Any, dag: Any)
```

---

#### HybridRouter.route_safely

```python
route_safely(self: Any, task_type: str, prompt: str, start_node: str)
```

Route to a model based on both neural capability and symbolic safety.

---

---

## route_safely

```python
route_safely(self: Any, task_type: str, prompt: str, start_node: str)
```

Route to a model based on both neural capability and symbolic safety.

---
