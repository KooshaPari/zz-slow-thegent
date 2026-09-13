# fast_http_client API Reference

> **Source**: `src/thegent/infra/fast_http_client.py`

Fast HTTP client with optimized backends.

This module provides a high-performance abstraction layer for HTTP requests
that automatically selects the fastest available backend:

- curl_cffi: 2-3x faster, libcurl-based, browser fingerprinting
- httpx: Modern, well-maintained, good async/sync support
- requests: Legacy fallback

Performance improvements:

- curl_cffi uses libcurl (2-3x faster than httpx)
- Better connection pooling
- Browser fingerprinting support
- Automatic backend selection

---

## FastHTTPClient

High-performance HTTP client with automatic backend selection and connection pooling.

OPT-004: Connection pooling for provider HTTP clients (40% connection overhead reduction).

Backend priority (fastest first):

1. curl_cffi (if installed) - 2-3x faster, libcurl-based
2. httpx (modern, well-maintained) - good balance, supports connection pooling
3. requests (legacy fallback) - baseline, supports Session pooling

Connection pooling:

- httpx: Uses persistent Client with connection pool
- requests: Uses Session with connection pool
- curl_cffi: Uses persistent session (implicit pooling)

### Methods

#### FastHTTPClient.**init**

```python
__init__(self: Any, impersonate: Any)
```

Initialize HTTP client with connection pooling.

**Parameters**:

- `impersonate`: Browser to impersonate (curl_cffi only, e.g., "chrome", "safari")

---

#### FastHTTPClient.backend

```python
backend(self: Any)
```

Get current backend name.

---

#### FastHTTPClient.close

```python
close(self: Any)
```

Close connection pool.

---

#### FastHTTPClient.get

```python
get(self: Any, url: str)
```

Perform GET request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---

#### FastHTTPClient.post

```python
post(self: Any, url: str)
```

Perform POST request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---

#### FastHTTPClient.request

```python
request(self: Any, method: str, url: str)
```

Perform HTTP request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `method`: HTTP method (GET, POST, etc.)
- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---

---

## backend

```python
backend(self: Any)
```

Get current backend name.

---

## close

```python
close(self: Any)
```

Close connection pool.

---

## get

```python
get(self: Any, url: str)
```

Perform GET request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---

## get_http_client

```python
get_http_client(impersonate: Any)
```

Get global fast HTTP client instance.

**Parameters**:

- `impersonate`: Browser to impersonate (curl_cffi only)

**Returns**: FastHTTPClient instance

---

## http_get

```python
http_get(url: str)
```

Perform GET request using fastest available backend.

---

## http_post

```python
http_post(url: str)
```

Perform POST request using fastest available backend.

---

## http_request

```python
http_request(method: str, url: str)
```

Perform HTTP request using fastest available backend.

---

## post

```python
post(self: Any, url: str)
```

Perform POST request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---

## request

```python
request(self: Any, method: str, url: str)
```

Perform HTTP request using connection pool.

OPT-004: Uses persistent client for connection reuse.

**Parameters**:

- `method`: HTTP method (GET, POST, etc.)
- `url`: URL to request
- `**kwargs`: Additional request options

**Returns**: Response object

---
