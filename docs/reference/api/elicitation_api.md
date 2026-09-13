# elicitation API Reference

> **Source**: `src/thegent/mcp/tools/elicitation.py`

MCP tools exposing FastMCP elicitation API for interactive user input.

Provides three composable primitives for requesting user input mid-execution:

- elicit_confirmation: yes/no boolean
- elicit_choice: single selection from a list
- elicit_text: free-form text entry

Each function uses FastMCP's built-in ctx.elicit() mechanism and handles
AcceptedElicitation / DeclinedElicitation / CancelledElicitation outcomes.

Graceful fallback: if ctx.elicit is unavailable (older FastMCP), returns None
with a structured warning instead of raising.

---

## register_elicitation_tools

```python
register_elicitation_tools(mcp: FastMCP)
```

Register elicitation helper tools on the FastMCP server.

Exposes elicit_confirmation, elicit_choice, and elicit_text as
first-class MCP tools so that agent orchestrators can trigger
user elicitation flows via the standard MCP tool-call protocol.

**Parameters**:

- `mcp`: The FastMCP application instance.

---
