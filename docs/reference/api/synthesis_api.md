# synthesis API Reference

> **Source**: `src/thegent/agents/synthesis.py`

WP-27001: Neural-Symbolic Program Synthesis.

Combines LLM-based code generation with symbolic verification and formal methods.
Ensures synthesized programs are correct and safe by construction.

---

## ProgramSynthesizer

Orchestrates neural-symbolic program generation.

### Methods

#### ProgramSynthesizer.**init**

```python
__init__(self: Any, run_id: str)
```

---

#### ProgramSynthesizer.synthesize

```python
synthesize(self: Any, prompt: str, formal_spec: Any)
```

Synthesize a program from a prompt and optional formal spec.

---

---

## SynthesisResult

Result of a neural-symbolic synthesis operation.

**Inherits from**: `BaseModel`

---

## synthesize

```python
synthesize(self: Any, prompt: str, formal_spec: Any)
```

Synthesize a program from a prompt and optional formal spec.

---
