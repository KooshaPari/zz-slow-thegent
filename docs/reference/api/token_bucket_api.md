# token_bucket API Reference

> **Source**: `src/thegent/orchestration/resource/token_bucket.py`

Token bucket rate limiting for swarm API call layer (swarm-token-bucket).

Provides a thread-safe TokenBucket for controlling API call throughput and a
RateLimitedSwarmRunner that wraps any callable with token-bucket-based gating.

Environment variables:
THGENT_RATE_TOKENS_PER_SEC -- refill rate (tokens/second); default 10.0
THGENT_RATE_BUCKET_SIZE -- bucket capacity; default 20.0

---

## RateLimitedSwarmRunner

Wraps a callable with token-bucket rate limiting for swarm API calls.

Each call to `run()` acquires a token from the configured bucket before
invoking the wrapped function. If insufficient tokens are available, the
call blocks until a token is obtained (subject to an optional timeout).

Configuration can be injected directly or loaded from environment variables
via `configure_from_env()`.

### Methods

#### RateLimitedSwarmRunner.**init**

```python
__init__(self: Any, bucket: Any, default_timeout_s: Any)
```

Initialise with an optional pre-configured bucket.

**Parameters**:

- `bucket`: A pre-built :class:`TokenBucket`. When None, you
  must call :meth:`configure_from_env` before `run`.
- `default_timeout_s`: Default per-call wait timeout passed to
  `consume_blocking`. None means no timeout.

---

#### RateLimitedSwarmRunner.configure_from_env

```python
configure_from_env(self: Any)
```

Read bucket config from environment variables and configure bucket.

Variables:
THGENT_RATE_TOKENS_PER_SEC -- refill rate (default 10.0)
THGENT_RATE_BUCKET_SIZE -- capacity (default 20.0)

**Returns**: self (for chaining).

---

#### RateLimitedSwarmRunner.run

Acquire a token, then call _fn_ with the given arguments.

**Parameters**:

- `fn`: Callable to invoke.
- `*args`: Positional arguments forwarded to _fn_.
- `timeout_s`: Override the default per-call timeout (seconds).
  Pass `None` explicitly for no timeout.
- `**kwargs`: Keyword arguments forwarded to _fn_.

**Returns**: The return value of _fn_.

---

---

## TokenBucket

Thread-safe token bucket for rate limiting.

Tokens are refilled continuously based on elapsed wall-clock time using
`time.monotonic()`. All public methods acquire an internal `threading.Lock`
so the bucket is safe to share across threads.

Example::

    cfg = TokenBucketConfig(capacity=10.0, refill_rate=2.0)
    bucket = TokenBucket(cfg)
    if bucket.consume():
        make_api_call()

### Methods

#### TokenBucket.**init**

```python
__init__(self: Any, config: TokenBucketConfig)
```

---

#### TokenBucket.available

```python
available(self: Any)
```

Return the current number of available tokens (after refill).

---

#### TokenBucket.consume

```python
consume(self: Any, tokens: float)
```

Attempt to consume _tokens_ without blocking.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).

**Returns**: True if tokens were consumed; False if insufficient tokens available.

---

#### TokenBucket.consume_blocking

```python
consume_blocking(self: Any, tokens: float, timeout_s: Any)
```

Block until enough tokens are available, then consume them.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).
- `timeout_s`: Maximum seconds to wait; None means wait indefinitely.

**Returns**: True if tokens were consumed within the timeout; False otherwise.

---

#### TokenBucket.refill

```python
refill(self: Any, tokens: Any)
```

Manually add tokens to the bucket (or trigger time-based refill).

**Parameters**:

- `tokens`: If given, add exactly this many tokens (capped at capacity).
  If None, perform a standard time-based refill.

---

#### TokenBucket.try_consume

```python
try_consume(self: Any, tokens: float)
```

Attempt to consume without blocking; return result and estimated wait.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).

**Returns**: A 2-tuple `(success, wait_time_s)` where _wait_time_s_ is 0.0 on
success and the estimated seconds until enough tokens are available
on failure (0.0 if refill_rate is 0).

---

---

## TokenBucketConfig

Configuration for a token bucket rate limiter.

### Methods

---

## available

```python
available(self: Any)
```

Return the current number of available tokens (after refill).

---

## configure_from_env

```python
configure_from_env(self: Any)
```

Read bucket config from environment variables and configure bucket.

Variables:
THGENT_RATE_TOKENS_PER_SEC -- refill rate (default 10.0)
THGENT_RATE_BUCKET_SIZE -- capacity (default 20.0)

**Returns**: self (for chaining).

---

## consume

```python
consume(self: Any, tokens: float)
```

Attempt to consume _tokens_ without blocking.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).

**Returns**: True if tokens were consumed; False if insufficient tokens available.

---

## consume_blocking

```python
consume_blocking(self: Any, tokens: float, timeout_s: Any)
```

Block until enough tokens are available, then consume them.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).
- `timeout_s`: Maximum seconds to wait; None means wait indefinitely.

**Returns**: True if tokens were consumed within the timeout; False otherwise.

---

## refill

```python
refill(self: Any, tokens: Any)
```

Manually add tokens to the bucket (or trigger time-based refill).

**Parameters**:

- `tokens`: If given, add exactly this many tokens (capped at capacity).
  If None, perform a standard time-based refill.

---

## run

Acquire a token, then call _fn_ with the given arguments.

**Parameters**:

- `fn`: Callable to invoke.
- `*args`: Positional arguments forwarded to _fn_.
- `timeout_s`: Override the default per-call timeout (seconds).
  Pass `None` explicitly for no timeout.
- `**kwargs`: Keyword arguments forwarded to _fn_.

**Returns**: The return value of _fn_.

**Raises**:

- `RuntimeError`: If no bucket has been configured.
- `TimeoutError`: If a token could not be acquired within _timeout_s_.

---

## try_consume

```python
try_consume(self: Any, tokens: float)
```

Attempt to consume without blocking; return result and estimated wait.

**Parameters**:

- `tokens`: Number of tokens to consume (default 1.0).

**Returns**: A 2-tuple `(success, wait_time_s)` where _wait_time_s_ is 0.0 on
success and the estimated seconds until enough tokens are available
on failure (0.0 if refill_rate is 0).

---
