# cost_routing API Reference

> **Source**: `src/thegent/research/cost_routing.py`

Advanced cost routing research and implementation.

---

## CostRoutingResearch

Research framework for advanced cost routing.

### Methods

#### CostRoutingResearch.**init**

```python
__init__(self: Any)
```

Initialize cost routing research.

---

#### CostRoutingResearch.compare_strategies

```python
compare_strategies(self: Any, requests: list[dict[(str, Any)]])
```

Compare multiple routing strategies.

**Parameters**:

- `requests`: List of requests to test

**Returns**: Comparison results

---

#### CostRoutingResearch.register_strategy

```python
register_strategy(self: Any, name: str, strategy: dict[(str, Any)])
```

Register a routing strategy.

**Parameters**:

- `name`: Strategy name
- `strategy`: Strategy configuration

---

#### CostRoutingResearch.simulate_routing

```python
simulate_routing(self: Any, requests: list[dict[(str, Any)]], strategy: str)
```

Simulate routing for a set of requests.

**Parameters**:

- `requests`: List of request dictionaries
- `strategy`: Routing strategy to use

**Returns**: Simulation results

---

---

## compare_strategies

```python
compare_strategies(self: Any, requests: list[dict[(str, Any)]])
```

Compare multiple routing strategies.

**Parameters**:

- `requests`: List of requests to test

**Returns**: Comparison results

---

## register_strategy

```python
register_strategy(self: Any, name: str, strategy: dict[(str, Any)])
```

Register a routing strategy.

**Parameters**:

- `name`: Strategy name
- `strategy`: Strategy configuration

---

## simulate_routing

```python
simulate_routing(self: Any, requests: list[dict[(str, Any)]], strategy: str)
```

Simulate routing for a set of requests.

**Parameters**:

- `requests`: List of request dictionaries
- `strategy`: Routing strategy to use

**Returns**: Simulation results

---
