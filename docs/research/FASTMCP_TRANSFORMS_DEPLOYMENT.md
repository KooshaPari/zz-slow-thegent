<DONE>
# FastMCP Transforms & Deployment Summary

**Source:** Extracted from FastMCP package source (gofastmcp.com docs: transforms, resources-as-tools, prompts-as-tools, deployment/http)
**Date:** 2026-02-14

---

## (a) add_transform Usage

add_transform adds a transform to a server or provider. Transforms modify components (tools, resources, prompts) and are applied after provider aggregation.

### Server-level

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import Namespace, ToolTransform

server = FastMCP("Server")
server.add_transform(Namespace("api"))  # All tools become "api_toolname"

# Tool-specific transformations (replaces deprecated add_tool_transformation)
server.add_transform(ToolTransform({"tool_name": config}))
```

### Provider-level (mounted servers)

```python
provider = FastMCPProvider(sub_server)
provider.add_transform(Namespace("sub"))
main.add_provider(provider)
```

### Built-in transforms

| Transform | Purpose |
|-----------|---------|
| Namespace("prefix") | Prefix tool names (e.g. api_toolname) |
| ToolTransform({name: config}) | Per-tool description/schema overrides |
| ResourcesAsTools(provider) | Expose resources as list_resources / read_resource tools |
| PromptsAsTools(provider) | Expose prompts as list_prompts / get_prompt tools |
| VersionFilter(...) | Filter by client version |
| Visibility | Enable/disable components by tags |

---

## (b) EventStore(storage=)

EventStore enables SSE polling and resumability for Streamable HTTP. Events are stored so clients can reconnect and resume from the last event.

### Constructor

```python
from fastmcp.server.event_store import EventStore
from key_value.aio.stores.redis import RedisStore

# Default in-memory storage
event_store = EventStore()

# Custom backend (Redis)
redis_backend = RedisStore(url="redis://localhost")
event_store = EventStore(storage=redis_backend)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| storage | AsyncKeyValue | None | MemoryStore() | Backend for event storage |
| max_events_per_stream | int | 100 | Max events retained per stream |
| ttl | int | None | 3600 | Event TTL in seconds; None = no expiration |

### Usage with HTTP app

```python
mcp = FastMCP("MyServer")
app = mcp.http_app(
    event_store=event_store,
    retry_interval=2000,  # ms before client reconnects
    transport="streamable-http",
)
```

---

## (c) close_sse_stream

ctx.close_sse_stream() gracefully closes the current HTTP response so the client reconnects. Used to avoid load balancer timeouts during long-running operations.

### When it applies

- Requires: Streamable HTTP transport AND an EventStore
- Otherwise: No-op (debug log only)

### Behavior

1. Closes the current HTTP connection
2. Client reconnects after retry_interval ms
3. Client resumes from last event via EventStore

### Example

```python
@mcp.tool
async def long_running_task(ctx: Context) -> str:
    for i in range(100):
        await ctx.report_progress(i, 100)

        # Close connection every 30 iterations to avoid LB timeouts
        if i % 30 == 0 and i > 0:
            await ctx.close_sse_stream()

        await do_work()
    return "Done"
```

---

## (d) ResourcesAsTools and PromptsAsTools

### ResourcesAsTools

Exposes resources as tools for clients that only support tools.

Generated tools:
- list_resources - Lists resources and templates (JSON)
- read_resource - Reads a resource by URI (text or base64 for binary)

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import ResourcesAsTools

mcp = FastMCP("Server")
mcp.add_transform(ResourcesAsTools(mcp))
```

### PromptsAsTools

Exposes prompts as tools for tool-only clients.

Generated tools:
- list_prompts - Lists prompts with metadata (JSON)
- get_prompt - Renders a prompt by name with optional arguments

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import PromptsAsTools

mcp = FastMCP("Server")
mcp.add_transform(PromptsAsTools(mcp))
```

### Notes

- Both take the provider (usually the FastMCP server) as the constructor argument
- Auth and visibility filtering from the provider apply to the generated tools
- read_resource accepts exact URIs or filled-in template URIs
- get_prompt accepts name and optional arguments dict

---

## HTTP Deployment (http_app)

```python
app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",  # or "http", "sse"
    event_store=event_store,
    retry_interval=2000,
    stateless_http=False,
    json_response=False,
)
```

| Parameter | Description |
|-----------|-------------|
| path | HTTP endpoint path |
| transport | "http", "streamable-http", or "sse" |
| event_store | For SSE polling/resumability (streamable-http only) |
| retry_interval | Reconnect delay in ms (requires event_store) |
| stateless_http | New transport per request for horizontal scaling |

---

## References

- FastMCP 3.0 Docs: https://gofastmcp.com
- Transforms: https://gofastmcp.com/servers/transforms/transforms
- Resources as Tools: https://gofastmcp.com/servers/transforms/resources-as-tools
- Prompts as Tools: https://gofastmcp.com/servers/transforms/prompts-as-tools
- HTTP Deployment: https://gofastmcp.com/deployment/http

---

## EXTENSION_SUMMARY

### 9. CI/CD Integration

#### 9.1 Deployment Pipeline

```yaml
# .github/workflows/deploy-mcp.yml
name: Deploy FastMCP Server

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[tasks]"

      - name: Run tests
        run: pytest tests/test_unit_mcp_tools.py -v

      - name: Lint
        run: ruff check src/thegent/mcp_tools_modes.py

      - name: Build Docker image
        run: |
          docker build -t ${{ env.REGISTRY }}/thegent-mcp:${{ github.sha }} .
          docker push ${{ env.REGISTRY }}/thegent-mcp:${{ github.sha }}

      - name: Deploy to environment
        run: |
          kubectl set image deployment/thegent-mcp \
            thegent-mcp=${{ env.REGISTRY }}/thegent-mcp:${{ github.sha }} \
            -n ${{ github.event.inputs.environment }}
```

**Cross-reference:** See `hooks/qa-preflight.sh` for pre-deployment quality checks.

#### 9.2 Health Check Integration

```python
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route


def health_check(request):
    """Health check endpoint for deployment."""
    return JSONResponse(
        {
            "status": "healthy",
            "version": "1.0.0",
            "components": {"mcp": "healthy", "cache": "healthy", "event_store": "healthy"},
        }
    )


mcp = FastMCP("ThegentServer")
mcp.router.add_route("/health", health_check)
```

### 10. Rollback Procedures

#### 10.1 Automatic Rollback on Health Failure

```bash
#!/bin/bash
# scripts/rollback-mcp.sh

DEPLOYMENT_NAME="thegent-mcp"
NAMESPACE="production"
PREVIOUS_IMAGE=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' | rev | cut -d: -f1 | rev)

# Check health
for i in {1..5}; do
    if curl -sf http://thegent.internal/health > /dev/null; then
        echo "Health check passed"
        exit 0
    fi
    echo "Health check failed, attempt $i/5"
    sleep 5
done

# Rollback
echo "Rolling back to previous image: $PREVIOUS_IMAGE"
kubectl set image deployment/$DEPLOYMENT_NAME \
    thegent-mcp=$PREVIOUS_IMAGE \
    -n $NAMESPACE

# Verify rollback
sleep 10
if curl -sf http://thegent.internal/health > /dev/null; then
    echo "Rollback successful"
else
    echo "Rollback failed, manual intervention required"
    exit 1
fi
```

#### 10.2 Blue-Green Deployment

```yaml
# k8s/blue-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thegent-mcp-blue
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: thegent-mcp
        image: thegent-mcp:v1.0.0-blue
        env:
        - name: DEPLOYMENT_COLOR
          value: "blue"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thegent-mcp-green
spec:
  replicas: 0
  template:
    spec:
      containers:
      - name: thegent-mcp
        image: thegent-mcp:v1.0.1-green
        env:
        - name: DEPLOYMENT_COLOR
          value: "green"
---
apiVersion: v1
kind: Service
metadata:
  name: thegent-mcp
spec:
  selector:
    app: thegent-mcp
    deployment_color: blue  # Switch to "green" after verification
```

**Deployment Strategy:**

| Phase | Action | Verification |
|-------|--------|--------------|
| Deploy green | Set green replicas=3, blue replicas=0 | Health check on green |
| Verify | Run smoke tests against green | Pass rate > 99% |
| Switch | Update service selector to green | Zero downtime |
| Cleanup | Delete blue deployment | Resource cleanup |

### 11. Cross-Document References

| Reference | Purpose |
|-----------|---------|
| `FASTMCP_IMPLEMENTATION_GUIDE.md` | Complete deployment configuration |
| `FASTMCP_SPEC_DEEP_DIVE.md` | Transform specifications |
| `FASTMCP_MIDDLEWARE.md` | Middleware for production |
| `FASTMCP_STORAGE_EVENTSTORE.md` | EventStore for SSE |
| `hooks/qa-preflight.sh` | Pre-deployment quality checks |
| `hooks/security-pipeline.sh` | Security validation |

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
