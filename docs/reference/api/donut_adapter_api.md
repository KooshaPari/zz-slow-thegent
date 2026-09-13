# donut_adapter API Reference

> **Source**: `src/thegent/routing/donut_adapter.py`

Donut Architecture adapter for LiteLLM routing integration.

Integrates the routing layer with the Donut shared layer, enabling:

- Shared router instances across teammates
- Model preference propagation from queue
- Routing stats harvesting on session stop
- Team configuration export for multi-agent coordination

The Donut architecture provides a shared layer (queue, harvest, rules sync)
that is platform-agnostic, used by Claude Code, Codex, Cursor, Factory Droid,
and Augment Code.

---

## RoutingDonutAdapter

Adapter integrating routing with Donut shared layer.

Provides:

- Shared router instance management (singleton per policy)
- Model preference reading from prompt queue
- Routing stats harvesting on session stop
- Team router config export for multi-agent coordination

The adapter follows the Donut Architecture pattern where shared components
(queue, harvest, rules) are platform-agnostic and used across all agents.

### Methods

#### RoutingDonutAdapter.**init**

```python
__init__(self: Any, queue_path: Any, harvest_path: Any)
```

Initialize the Donut adapter.

**Parameters**:

- `queue_path`: Path to prompt queue JSONL file.
  Defaults to ~/.thegent/prompt_queue.jsonl
- `harvest_path`: Path to routing harvest JSONL file.
  Defaults to ~/.thegent/routing_harvest.jsonl

---

#### RoutingDonutAdapter.clear_stats

```python
clear_stats(self: Any)
```

Reset routing statistics.

---

#### RoutingDonutAdapter.get_router

```python
get_router(self: Any, policy: str)
```

Get or create a shared LiteLLM router for the given policy.

Routers are cached by policy, enabling reuse across teammates
and multiple calls within a session.

**Parameters**:

- `policy`: Routing policy (cheapest, fastest, round_robin)

**Returns**: Configured LiteLLM Router instance

---

#### RoutingDonutAdapter.get_stats

```python
get_stats(self: Any)
```

Get current routing statistics.

---

#### RoutingDonutAdapter.get_team_router_config

```python
get_team_router_config(self: Any)
```

Get router config dict for sharing across teammates.

Exports configuration that can be used by teammate agents
to instantiate compatible routers. This enables coordinated
routing decisions across a team of agents.

**Returns**: Dictionary containing:

- policies: List of available routing policies
- default_policy: The default routing policy
- queue_path: Path to the shared queue
- harvest_path: Path to the harvest file
- stats_summary: Current routing statistics summary

---

#### RoutingDonutAdapter.harvest_on_stop

```python
harvest_on_stop(self: Any)
```

Export routing stats for harvest on session stop.

Creates a harvest entry with routing statistics and appends it
to the routing harvest JSONL file. This is called at session end
to capture routing metrics for analysis and cost tracking.

**Returns**: The harvest entry dictionary that was written

---

#### RoutingDonutAdapter.harvest_path

```python
harvest_path(self: Any)
```

Path to the routing harvest file.

---

#### RoutingDonutAdapter.queue_path

```python
queue_path(self: Any)
```

Path to the prompt queue file.

---

#### RoutingDonutAdapter.read_model_preference_from_queue

```python
read_model_preference_from_queue(self: Any)
```

Read preferred_model from the first unclaimed queue item.

The prompt queue stores pending items that may include a preferred_model
field indicating which model should handle the task. This method reads
from the Donut shared queue to extract that preference.

Queue item format:
{"ts": "ISO8601", "prompt": "...", "preferred_model": "...",
"claimed_by": null, "lease_expires_at": null}

**Returns**: The preferred_model string if found in an unclaimed item,
otherwise None.

---

#### RoutingDonutAdapter.record_request

```python
record_request(self: Any, model: str, provider: str, category: str, tokens: int, cost_usd: float, is_fallback: bool, is_error: bool)
```

Record a routing request for stats tracking.

**Parameters**:

- `model`: The model that handled the request
- `provider`: The provider used
- `category`: Task category (fast, normal, complex, high_complex)
- `tokens`: Total tokens used
- `cost_usd`: Cost in USD
- `is_fallback`: Whether this was a fallback routing
- `is_error`: Whether the request resulted in an error

---

---

## RoutingStats

Routing statistics for harvest export.

---

## clear_stats

```python
clear_stats(self: Any)
```

Reset routing statistics.

---

## get_donut_adapter

Get global Donut adapter instance.

---

## get_router

```python
get_router(self: Any, policy: str)
```

Get or create a shared LiteLLM router for the given policy.

Routers are cached by policy, enabling reuse across teammates
and multiple calls within a session.

**Parameters**:

- `policy`: Routing policy (cheapest, fastest, round_robin)

**Returns**: Configured LiteLLM Router instance

---

## get_stats

```python
get_stats(self: Any)
```

Get current routing statistics.

---

## get_team_router_config

```python
get_team_router_config(self: Any)
```

Get router config dict for sharing across teammates.

Exports configuration that can be used by teammate agents
to instantiate compatible routers. This enables coordinated
routing decisions across a team of agents.

**Returns**: Dictionary containing:

- policies: List of available routing policies
- default_policy: The default routing policy
- queue_path: Path to the shared queue
- harvest_path: Path to the harvest file
- stats_summary: Current routing statistics summary

---

## harvest_on_stop

```python
harvest_on_stop(self: Any)
```

Export routing stats for harvest on session stop.

Creates a harvest entry with routing statistics and appends it
to the routing harvest JSONL file. This is called at session end
to capture routing metrics for analysis and cost tracking.

**Returns**: The harvest entry dictionary that was written

---

## harvest_path

```python
harvest_path(self: Any)
```

Path to the routing harvest file.

---

## queue_path

```python
queue_path(self: Any)
```

Path to the prompt queue file.

---

## read_model_preference_from_queue

```python
read_model_preference_from_queue(self: Any)
```

Read preferred_model from the first unclaimed queue item.

The prompt queue stores pending items that may include a preferred_model
field indicating which model should handle the task. This method reads
from the Donut shared queue to extract that preference.

Queue item format:
{"ts": "ISO8601", "prompt": "...", "preferred_model": "...",
"claimed_by": null, "lease_expires_at": null}

**Returns**: The preferred_model string if found in an unclaimed item,
otherwise None.

---

## record_request

```python
record_request(self: Any, model: str, provider: str, category: str, tokens: int, cost_usd: float, is_fallback: bool, is_error: bool)
```

Record a routing request for stats tracking.

**Parameters**:

- `model`: The model that handled the request
- `provider`: The provider used
- `category`: Task category (fast, normal, complex, high_complex)
- `tokens`: Total tokens used
- `cost_usd`: Cost in USD
- `is_fallback`: Whether this was a fallback routing
- `is_error`: Whether the request resulted in an error

---
