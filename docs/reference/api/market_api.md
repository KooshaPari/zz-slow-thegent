# market API Reference

> **Source**: `src/thegent/discovery/market.py`

WP-30001: Agent Service Registry (Global).

A decentralized marketplace for agent services.
Enables agents to list capabilities and for clients to discover and bind to them.

---

## AgentService

Metadata for an agent service listing.

**Inherits from**: `BaseModel`

---

## GlobalServiceRegistry

Manages global agent service listings and discovery.

### Methods

#### GlobalServiceRegistry.**init**

```python
__init__(self: Any, storage_path: Path)
```

---

#### GlobalServiceRegistry.discover_services

```python
discover_services(self: Any, capability: str)
```

Find active services for a given capability.

---

#### GlobalServiceRegistry.list_service

```python
list_service(self: Any, service: AgentService)
```

Publish a service listing to the registry.

---

#### GlobalServiceRegistry.run_auction

```python
run_auction(self: Any, task_id: str, capability: str, budget: float)
```

WP-30002: Run a reverse auction for a task requirement.

---

---

## discover_services

```python
discover_services(self: Any, capability: str)
```

Find active services for a given capability.

---

## list_service

```python
list_service(self: Any, service: AgentService)
```

Publish a service listing to the registry.

---

## run_auction

```python
run_auction(self: Any, task_id: str, capability: str, budget: float)
```

WP-30002: Run a reverse auction for a task requirement.

---
