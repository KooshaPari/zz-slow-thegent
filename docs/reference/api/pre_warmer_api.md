# pre_warmer API Reference

> **Source**: `src/thegent/cache/pre_warmer.py`

Predictive cache pre-warmer: proactively loads likely-needed data.

Usage pattern::

    cache = MultiLevelCache(l1_maxsize=500, l1_ttl=120)
    warmer = CachePreWarmer(cache)

    warmer.register_strategy(
        WarmingStrategy(
            name="my_strategy",
            predict_fn=lambda: ["key1", "key2", "key3"],
            load_fn=lambda key: fetch_expensive(key),
            schedule_seconds=300,
        )
    )

    # One-shot warm run
    results = warmer.warm_all()

    # Continuous background daemon
    warmer.start_background()
    ...
    warmer.stop_background()

FR traceability: FR-CACHE-003 (predictive pre-warming based on usage patterns)

---

## CachePreWarmer

Predictive pre-warmer that proactively loads likely-needed data into cache.

Supports multiple :class:`WarmingStrategy` instances, each providing:

- A _predict_fn_ that returns a list of keys expected to be needed soon.
- A _load_fn_ that fetches the data for a given key.

Warming can be triggered manually (:meth:`warm_all`) or automatically via
a background daemon thread (:meth:`start_background` / :meth:`stop_background`).

### Methods

#### CachePreWarmer.**init**

```python
__init__(self: Any, cache: MultiLevelCache)
```

---

#### CachePreWarmer.get_stats

```python
get_stats(self: Any)
```

Return a snapshot of pre-warmer statistics.

**Returns**: Dict with keys:

- `strategies`: number of registered strategies
- `warm_count`: total successful warm operations across all strategies
- `last_run`: datetime of the last :meth:`warm_all` call, or None
- `background_running`: bool — whether the daemon is active
- `strategy_stats`: list of per-strategy dicts

---

#### CachePreWarmer.is_running

```python
is_running(self: Any)
```

Return True if the background daemon thread is currently alive.

---

#### CachePreWarmer.register_strategy

```python
register_strategy(self: Any, strategy: WarmingStrategy)
```

Register a :class:`WarmingStrategy` with the pre-warmer.

Re-registering a strategy with the same name replaces the existing one.

**Parameters**:

- `strategy`: The strategy to register.

---

#### CachePreWarmer.start_background

```python
start_background(self: Any)
```

Start a daemon thread that periodically warms the cache.

The daemon respects each strategy's _schedule_seconds_: a strategy is
only warmed when at least _schedule_seconds_ have elapsed since its
last run. The thread polls every second for fine-grained scheduling.

Calling this method when a daemon is already running has no effect.

---

#### CachePreWarmer.stop_background

```python
stop_background(self: Any, timeout: float)
```

Signal the background daemon to stop and wait for it to exit.

**Parameters**:

- `timeout`: Maximum seconds to wait for the daemon thread to exit.

**Returns**: True if the thread stopped within _timeout_, False if it timed out.

---

#### CachePreWarmer.unregister_strategy

```python
unregister_strategy(self: Any, name: str)
```

Remove a previously registered strategy by name.

**Parameters**:

- `name`: Strategy name to remove.

**Returns**: True if a strategy was removed, False if it was not found.

---

#### CachePreWarmer.warm_all

```python
warm_all(self: Any)
```

Run all registered strategies and warm every predicted key.

Each strategy's _predict_fn_ is called to obtain keys; then
_load_fn_ is called for each key. Errors in individual keys are
caught and recorded without aborting remaining keys.

**Returns**: Mapping of `key -&gt; bool` indicating whether each key was
successfully warmed. The dict preserves insertion order
(strategies run in registration order).

---

#### CachePreWarmer.warm_key

```python
warm_key(self: Any, key: str, load_fn: Callable[(Any, Any)])
```

Warm a single key by calling _load_fn_ and storing the result in cache.

**Parameters**:

- `key`: Cache key to warm.
- `load_fn`: Zero-argument callable that returns the value for _key_.
  Must not raise; exceptions are caught and logged.

**Returns**: True if the key was successfully warmed (value fetched and stored),
False if _load_fn_ raised or returned None.

---

---

## WarmingStrategy

Configuration for a single pre-warming strategy.

### Methods

---

## \_StrategyState

Runtime state tracked per strategy by the pre-warmer.

---

## get_stats

```python
get_stats(self: Any)
```

Return a snapshot of pre-warmer statistics.

**Returns**: Dict with keys:

- `strategies`: number of registered strategies
- `warm_count`: total successful warm operations across all strategies
- `last_run`: datetime of the last :meth:`warm_all` call, or None
- `background_running`: bool — whether the daemon is active
- `strategy_stats`: list of per-strategy dicts

---

## is_running

```python
is_running(self: Any)
```

Return True if the background daemon thread is currently alive.

---

## model_list_strategy

```python
model_list_strategy(load_fn: Callable[(Any, Any)], model_keys: Any, schedule_seconds: float)
```

Return a strategy that pre-warms cached model-list metadata.

**Parameters**:

- `load_fn`: Function to load the value for a given model key.
- `model_keys`: Explicit list of model cache keys to pre-warm.
  Defaults to a standard set of common model identifiers.
- `schedule_seconds`: Warming interval in seconds (default: 300).

**Returns**: A configured :class:`WarmingStrategy` named `"model_list"`.

---

## register_strategy

```python
register_strategy(self: Any, strategy: WarmingStrategy)
```

Register a :class:`WarmingStrategy` with the pre-warmer.

Re-registering a strategy with the same name replaces the existing one.

**Parameters**:

- `strategy`: The strategy to register.

---

## session_list_strategy

```python
session_list_strategy(load_fn: Callable[(Any, Any)], session_keys: Any, schedule_seconds: float)
```

Return a strategy that pre-warms cached session-list metadata.

**Parameters**:

- `load_fn`: Function to load the value for a given session key.
- `session_keys`: Explicit list of session cache keys to pre-warm.
  Defaults to a standard set of common session identifiers.
- `schedule_seconds`: Warming interval in seconds (default: 300).

**Returns**: A configured :class:`WarmingStrategy` named `"session_list"`.

---

## start_background

```python
start_background(self: Any)
```

Start a daemon thread that periodically warms the cache.

The daemon respects each strategy's _schedule_seconds_: a strategy is
only warmed when at least _schedule_seconds_ have elapsed since its
last run. The thread polls every second for fine-grained scheduling.

Calling this method when a daemon is already running has no effect.

---

## stop_background

```python
stop_background(self: Any, timeout: float)
```

Signal the background daemon to stop and wait for it to exit.

**Parameters**:

- `timeout`: Maximum seconds to wait for the daemon thread to exit.

**Returns**: True if the thread stopped within _timeout_, False if it timed out.

---

## unregister_strategy

```python
unregister_strategy(self: Any, name: str)
```

Remove a previously registered strategy by name.

**Parameters**:

- `name`: Strategy name to remove.

**Returns**: True if a strategy was removed, False if it was not found.

---

## warm_all

```python
warm_all(self: Any)
```

Run all registered strategies and warm every predicted key.

Each strategy's _predict_fn_ is called to obtain keys; then
_load_fn_ is called for each key. Errors in individual keys are
caught and recorded without aborting remaining keys.

**Returns**: Mapping of `key -&gt; bool` indicating whether each key was
successfully warmed. The dict preserves insertion order
(strategies run in registration order).

---

## warm_key

```python
warm_key(self: Any, key: str, load_fn: Callable[(Any, Any)])
```

Warm a single key by calling _load_fn_ and storing the result in cache.

**Parameters**:

- `key`: Cache key to warm.
- `load_fn`: Zero-argument callable that returns the value for _key_.
  Must not raise; exceptions are caught and logged.

**Returns**: True if the key was successfully warmed (value fetched and stored),
False if _load_fn_ raised or returned None.

---
