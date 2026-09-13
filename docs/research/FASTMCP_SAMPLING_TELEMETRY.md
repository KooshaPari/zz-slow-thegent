<DONE>
# FastMCP Sampling & Telemetry

**Source:** gofastmcp.com/servers/sampling, gofastmcp.com/servers/telemetry
**Date:** 2026-02-14
**Purpose:** Extract ctx.sample with result_type, get_tracer(), opentelemetry-instrument for thegent.

---

## 1. ctx.sample with result_type

### Basic usage

```python
result = await ctx.sample(f"Please summarize this:\n\n{content}")
return result.text or ""
```

### Structured output (result_type)

```python
from pydantic import BaseModel


class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    reasoning: str


result = await ctx.sample(
    messages=f"Analyze the sentiment of: {text}",
    result_type=SentimentResult,
)
return result.result  # Validated SentimentResult object
```

- `result_type` accepts Pydantic models, dataclasses, `int`, `list[str]`, `dict[str, int]`
- FastMCP creates `final_response` tool; validation failures trigger retry
- `result.result` = validated object; `result.text` = JSON representation

### Fallback handler (when client lacks sampling)

```python
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler

server = FastMCP(
    name="My Server",
    sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
    sampling_handler_behavior="fallback",  # or "always"
)
```

- `"fallback"` (default): Use handler when client doesn't support sampling
- `"always"`: Always use handler, bypass client

### thegent_suggest_prompt

```python
@mcp.tool
async def thegent_suggest_prompt(raw_prompt: str, ctx: Context) -> str:
    result = await ctx.sample(
        messages=f"Refine this prompt for clarity and completeness:\n\n{raw_prompt}",
        result_type=str,
    )
    return result.text or raw_prompt
```

---

## 2. get_tracer()

```python
from fastmcp.telemetry import get_tracer


@mcp.tool()
async def complex_operation(input: str) -> str:
    tracer = get_tracer()
    with tracer.start_as_current_span("parse_input") as span:
        span.set_attribute("input.length", len(input))
        parsed = parse(input)
    with tracer.start_as_current_span("process_data") as span:
        result = process(parsed)
    return result
```

### Span attributes

| Attribute | Description |
|-----------|-------------|
| mcp.method.name | tools/call, resources/read, prompts/get |
| mcp.session.id | Session identifier |
| fastmcp.component.type | tool, resource, prompt |
| fastmcp.component.key | e.g. tool:greet |

---

## 3. opentelemetry-instrument

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install

opentelemetry-instrument \
  --service_name my-fastmcp-server \
  --exporter_otlp_endpoint http://localhost:4317 \
  fastmcp run server.py
```

Or via env:

```bash
export OTEL_SERVICE_NAME=thegent-mcp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
opentelemetry-instrument fastmcp run mcp_server.py
```

For thegent:

```bash
opentelemetry-instrument python -m thegent.main serve --host 127.0.0.1 --port 3847
```

### Server spans (auto-generated)

| Span Name | Description |
|-----------|-------------|
| tools/call {name} | e.g. tools/call thegent_run |
| resources/read {uri} | e.g. resources/read thegent://session/.../logs |
| prompts/get {name} | e.g. prompts/get thegent_run_agent |

---

## 4. thegent Integration

| Feature | Use |
|---------|-----|
| ctx.sample | thegent_suggest_prompt tool |
| sampling_handler | OpenAISamplingHandler when client lacks sampling |
| get_tracer | Custom spans in thegent_run (parse, route, execute) |
| opentelemetry-instrument | Production trace export |


---
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index


---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added telemetry patterns
2. Added sampling configuration
3. Enhanced cross-references

### Cross-References Added
- FASTMCP_TRANSFORMS_DEPLOYMENT.md
- FASTMCP_SPEC_DEEP_DIVE.md

### Practical Additions
- Telemetry templates
- Sampling configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification deep dive
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
