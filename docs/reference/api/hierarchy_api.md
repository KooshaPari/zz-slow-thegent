# hierarchy API Reference

> **Source**: `src/thegent/agents/smolgents/hierarchy.py`

AgentTree — parent/child tracking for SmolGents hierarchies.

---

## AgentTree

Flat registry that tracks parent/child relationships between SmolAgents.

The tree does **not** own the agents — callers are responsible for keeping
references. The tree only maintains a mapping of `name -&gt; agent` and the
directed parent/child edges so that traversal and lookup remain O(1).

Usage::

    tree = AgentTree()
    parent = SmolAgent("orchestrator", tools=[...])
    child  = SmolAgent("specialist",   tools=[...])

    tree.register(parent)
    tree.register(child, parent_name="orchestrator")

    assert tree.get("specialist") is child
    assert tree.get_children("orchestrator") == [child]
    assert tree.get_parent("specialist") is parent

### Methods

#### AgentTree.**init**

```python
__init__(self: Any)
```

---

#### AgentTree.get

```python
get(self: Any, name: str)
```

Return the agent registered under _name_, or _None_.

---

#### AgentTree.get_ancestors

```python
get_ancestors(self: Any, name: str)
```

Return ancestors from direct parent up to the root (inclusive).

---

#### AgentTree.get_children

```python
get_children(self: Any, name: str)
```

Return direct children of the agent named _name_.

---

#### AgentTree.get_descendants

```python
get_descendants(self: Any, name: str)
```

Return all descendants (recursive) of the named agent.

---

#### AgentTree.get_parent

```python
get_parent(self: Any, name: str)
```

Return the direct parent of the agent named _name_, or _None_.

---

#### AgentTree.list_agents

```python
list_agents(self: Any)
```

Return all registered agents in insertion order.

---

#### AgentTree.register

```python
register(self: Any, agent: SmolAgent)
```

Register an agent, optionally linking it to a parent.

**Parameters**:

- `agent`: The :class:`SmolAgent` to register.
- `parent_name`: Name of the parent agent already registered in this
  tree. Pass _None_ for the root / orphan nodes.

---

#### AgentTree.to_dict

```python
to_dict(self: Any)
```

Return a serialisable representation of the tree.

---

---

## get

```python
get(self: Any, name: str)
```

Return the agent registered under _name_, or _None_.

---

## get_ancestors

```python
get_ancestors(self: Any, name: str)
```

Return ancestors from direct parent up to the root (inclusive).

---

## get_children

```python
get_children(self: Any, name: str)
```

Return direct children of the agent named _name_.

---

## get_descendants

```python
get_descendants(self: Any, name: str)
```

Return all descendants (recursive) of the named agent.

---

## get_parent

```python
get_parent(self: Any, name: str)
```

Return the direct parent of the agent named _name_, or _None_.

---

## list_agents

```python
list_agents(self: Any)
```

Return all registered agents in insertion order.

---

## register

```python
register(self: Any, agent: SmolAgent)
```

Register an agent, optionally linking it to a parent.

**Parameters**:

- `agent`: The :class:`SmolAgent` to register.
- `parent_name`: Name of the parent agent already registered in this
  tree. Pass _None_ for the root / orphan nodes.

**Raises**:

- `ValueError`: If `parent_name` is specified but not yet registered.

---

## to_dict

```python
to_dict(self: Any)
```

Return a serialisable representation of the tree.

---
