<DONE>
# Codex 0.104.0 "No Model Metadata" Fix

**Date:** 2026-02-20
**Affected component:** `src/thegent/cliproxy_adapter.py`
**Symptom:** Codex 0.104.0 reports "no model metadata" on startup and keeps "reconnecting"

---

## Root Cause

Codex 0.104.0 calls `GET /v1/models` on startup to fetch model metadata. It expects:

1. **OpenAI-standard response body:** `{"object": "list", "data": [...]}`
2. **`x-models-etag` response header:** SHA256 of sorted model IDs (used for ETag-based cache invalidation)

The `cliproxy_adapter.py` `_transform_models_response` function was converting the response from the CLIProxy backend but **writing the model list under the key `"models"`** instead of `"data"`. Codex 0.104.0 looks for `data`, not `models`, so it found no models and emitted the "no model metadata" error.

Additionally, the handler did **not** set the `x-models-etag` header, causing Codex to re-fetch and "reconnect" on every poll cycle (since it could not cache the model list).

## What Changed

### `_transform_models_response` (`cliproxy_adapter.py`, line 231)

**Before:**

```python
def _transform_models_response(content: bytes) -> bytes | None:
    # ...
    models = data.pop("data", data.get("models", []))
    data["models"] = models  # WRONG: Codex 0.104.0 needs "data" not "models"
    return json.dumps(data).encode()
```

**After:**

```python
def _transform_models_response(content: bytes) -> tuple[bytes, str] | None:
    # ...
    models = payload.get("data") or payload.get("models") or []
    result = {"object": "list", "data": models}  # CORRECT: "data" key
    body = json.dumps(result).encode()
    etag = _compute_models_etag(models)
    return body, etag  # Returns (body, etag) tuple
```

### New `_compute_models_etag` function (`cliproxy_adapter.py`, line 231)

```python
def _compute_models_etag(models: list) -> str:
    model_ids = sorted(m.get("id", "") for m in models if isinstance(m, dict))
    return hashlib.sha256(",".join(model_ids).encode()).hexdigest()
```

Produces a deterministic, order-independent SHA256 hex digest of sorted model IDs.

### `proxy_handler` models branch (`cliproxy_adapter.py`, line 331)

**Before:**

```python
transformed = _transform_models_response(resp.body)
if transformed is not None:
    return Response(content=transformed, status_code=200, headers={"Content-Type": "application/json"})
```

**After:**

```python
result = _transform_models_response(resp.body)
if result is not None:
    transformed, etag = result
    return Response(
        content=transformed,
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "x-models-etag": etag,  # ADDED: required by Codex 0.104.0
        },
    )
```

## Verification

Live proxy at `http://127.0.0.1:8317/v1/models` before the fix returned:

```json
{"object": "list", "models": [...]}  // wrong key
```

Missing headers: `x-models-etag` was absent.

After the fix, the response will be:

```json
{"object": "list", "data": [...]}  // correct key
```

With header: `x-models-etag: <sha256-hex>`

## Test Coverage

Tests at `tests/routing/test_models_endpoint.py` (27 tests, all passing):

| Class                                  | Coverage                                                         |
| -------------------------------------- | ---------------------------------------------------------------- |
| `TestComputeModelsEtag`                | ETag determinism, order-independence, change detection           |
| `TestTransformModelsResponseFormat`    | `data` key (not `models`), `object: list`, field preservation    |
| `TestTransformModelsResponseEtag`      | ETag returned, matches compute function, changes with model list |
| `TestTransformModelsResponseMetadata`  | Metadata enrichment, no-overwrite, slug assignment               |
| `TestTransformModelsResponseEdgeCases` | Malformed input, empty list, missing id, slash-id suffix lookup  |

## Codex 0.104.0 Binary Analysis Notes

From binary string extraction:

- `x-models-etag` - response header Codex checks for cache invalidation
- `models_etag` - OTEL span attribute recording the etag value
- `prefer_websockets` - config key (separate concern; no change needed)

The ETag mechanism: Codex stores the etag from the first `/v1/models` response. On subsequent polls, if the etag matches, it uses the cached list. Without the header, every poll fetches fresh and the "reconnecting" loop appears.

## Impact

- Fixes Codex 0.104.0 "no model metadata" error on startup
- Fixes Codex "reconnecting" loop (ETag caching now works)
- No change to non-Codex behavior (other clients tolerate `data` key; it is OpenAI-standard)
- No backwards compatibility concern: `data` is the OpenAI-standard key; `models` was a non-standard artifact of the previous transform
