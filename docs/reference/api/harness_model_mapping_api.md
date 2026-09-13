# harness_model_mapping API Reference

> **Source**: `src/thegent/routing/harness_model_mapping.py`

Provider-harness-model mapping for universal parity across Codex, LiteLLM, and CLIProxy.

Ensures consistent model resolution and metadata when requests flow through:

- Codex harness (dex) -> CLIProxy adapter -> CLIProxyAPIPlus
- LiteLLM Router -> CLIProxyAPIPlus
- Direct CLIProxy API

When clode harness pairs with minimax/kilo + MiniMax-M2.5, see Minimax clode guidance:
https://platform.minimax.io/docs/coding-plan/claude-code

---

## resolve_model_for_backend

```python
resolve_model_for_backend(model: str)
```

Map Codex/provider-specific model ID to CLIProxy backend model ID.

---
