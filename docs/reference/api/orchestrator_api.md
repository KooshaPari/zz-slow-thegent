# orchestrator API Reference

> **Source**: `src/thegent/sync/orchestrator.py`

## CatalogSyncComponent

**Inherits from**: `SyncComponent`

**Method Resolution Order**: `CatalogSyncComponent -> SyncComponent`

### Methods

#### CatalogSyncComponent.**init**

```python
__init__(self: Any)
```

---

---

## DagSyncComponent

**Inherits from**: `SyncComponent`

**Method Resolution Order**: `DagSyncComponent -> SyncComponent`

### Methods

#### DagSyncComponent.**init**

```python
__init__(self: Any)
```

---

---

## RulesSyncComponent

**Inherits from**: `SyncComponent`

**Method Resolution Order**: `RulesSyncComponent -> SyncComponent`

### Methods

#### RulesSyncComponent.**init**

```python
__init__(self: Any)
```

---

---

## SyncComponent

**Inherits from**: `ABC`

### Methods

#### SyncComponent.**init**

```python
__init__(self: Any, name: str, description: str, depends_on: Any)
```

---

---

## SyncOrchestrator

### Methods

#### SyncOrchestrator.**init**

```python
__init__(self: Any, registry: Any)
```

---

---

## SyncRegistry

### Methods

#### SyncRegistry.**init**

```python
__init__(self: Any)
```

---

#### SyncRegistry.get_all_components

```python
get_all_components(self: Any)
```

---

#### SyncRegistry.get_component

```python
get_component(self: Any, name: str)
```

---

#### SyncRegistry.register

```python
register(self: Any, component: SyncComponent)
```

---

---

## SyncResult

### Methods

#### SyncResult.to_dict

```python
to_dict(self: Any)
```

---

---

## SyncStatus

**Inherits from**: `Enum`

---

## WorkStreamSyncComponent

**Inherits from**: `SyncComponent`

**Method Resolution Order**: `WorkStreamSyncComponent -> SyncComponent`

### Methods

#### WorkStreamSyncComponent.**init**

```python
__init__(self: Any)
```

---

---

## get_all_components

```python
get_all_components(self: Any) -> list[SyncComponent]
```

---

## get_component

```python
get_component(self: Any, name: str) -> Any
```

---

## register

```python
register(self: Any, component: SyncComponent)
```

---

## resolve

```python
resolve(comp: SyncComponent)
```

---

## to_dict

```python
to_dict(self: Any) -> dict[(str, Any)]
```

---
