# api_evolution API Reference

> **Source**: `src/thegent/tools/api_evolution.py`

WP-10009: Backward-compatible API evolution controls.

Manages version negotiation and compatibility flags for API changes.

---

## APIEvolutionManager

Manages compatibility between different API versions.

### Methods

#### APIEvolutionManager.**init**

```python
__init__(self: Any, current_version: str)
```

---

#### APIEvolutionManager.is_feature_enabled

```python
is_feature_enabled(self: Any, flag: str)
```

Check if a specific compatibility flag is enabled.

---

#### APIEvolutionManager.negotiate_version

```python
negotiate_version(self: Any, client_version: str)
```

Negotiate the best API version for the client.

---

---

## is_feature_enabled

```python
is_feature_enabled(self: Any, flag: str)
```

Check if a specific compatibility flag is enabled.

---

## negotiate_version

```python
negotiate_version(self: Any, client_version: str)
```

Negotiate the best API version for the client.

---
