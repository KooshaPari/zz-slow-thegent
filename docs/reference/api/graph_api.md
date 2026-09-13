# graph API Reference

> **Source**: `src/thegent/orchestration/graph.py`

WP-5001-SM-Graph: Supermemory Knowledge Graph integration.

---

## KnowledgeGraph

Interface to Supermemory.ai knowledge graph.

### Methods

#### KnowledgeGraph.**init**

```python
__init__(self: Any, api_token: str)
```

---

#### KnowledgeGraph.add_relation

```python
add_relation(self: Any, source: str, relation: str, target: str)
```

Add a new relation to the knowledge graph.

---

#### KnowledgeGraph.query

```python
query(self: Any, query_text: str)
```

Query the knowledge graph for relevant entities and relations.

---

---

## add_relation

```python
add_relation(self: Any, source: str, relation: str, target: str)
```

Add a new relation to the knowledge graph.

---

## query

```python
query(self: Any, query_text: str)
```

Query the knowledge graph for relevant entities and relations.

---
