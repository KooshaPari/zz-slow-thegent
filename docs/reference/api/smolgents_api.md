# smolgents API Reference

> **Source**: `src/thegent/agents/smolgents/__init__.py`

SmolGents — minimalist agent hierarchy for thegent.

Provides a lightweight agent framework for task decomposition, tool calling,
memory, and parent/child delegation. Designed to be "smol" by design:
no heavy deps beyond the stdlib and existing thegent requirements.

Public API::

    from thegent.agents.smolgents import SmolAgent, Tool, AgentTree

---
