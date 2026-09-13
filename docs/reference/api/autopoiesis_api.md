# autopoiesis API Reference

> **Source**: `src/thegent/agents/autopoiesis.py`

WP-37001: Self-Authoring Agent Architectures (Autopoiesis).

Enables thegent to design, code, and deploy entire new agent personas autonomously.
Uses recursive synthesis to evolve the system's own architecture.

---

## AgentPersonaSpec

Specification for a new agent persona to be authored.

**Inherits from**: `BaseModel`

---

## AutopoiesisManager

Orchestrates the self-authoring of agent architectures.

### Methods

#### AutopoiesisManager.**init**

```python
__init__(self: Any, run_id: str)
```

---

#### AutopoiesisManager.author_persona

```python
author_persona(self: Any, spec: AgentPersonaSpec)
```

Autonomously author a new agent persona based on a purpose spec.

---

#### AutopoiesisManager.deploy_persona

```python
deploy_persona(self: Any, synthesis: SynthesisResult)
```

Deploy the synthesized persona into the live registry.

---

---

## author_persona

```python
author_persona(self: Any, spec: AgentPersonaSpec)
```

Autonomously author a new agent persona based on a purpose spec.

---

## deploy_persona

```python
deploy_persona(self: Any, synthesis: SynthesisResult)
```

Deploy the synthesized persona into the live registry.

---
