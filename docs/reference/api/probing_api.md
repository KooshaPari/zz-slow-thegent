# probing API Reference

> **Source**: `src/thegent/agents/probing.py`

WP-33004: Black-Box Probing & Fingerprinting.

Identifies the underlying model and capabilities of black-box agents via behavioral probing.
Generates an 'agent fingerprint' to enable better steering and policy enforcement.

---

## AgentFingerprint

Behavioral fingerprint of a black-box agent.

**Inherits from**: `BaseModel`

---

## AgentProber

Probes black-box agents to identify their characteristics.

### Methods

#### AgentProber.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### AgentProber.identify_deviations

```python
identify_deviations(self: Any, current_fp: AgentFingerprint, baseline_fp: AgentFingerprint)
```

Detect if an agent's behavior has drifted from its baseline fingerprint.

---

#### AgentProber.probe_agent

```python
probe_agent(self: Any, proxy_fn: Any)
```

Run a suite of behavioral probes and generate a fingerprint.

---

---

## identify_deviations

```python
identify_deviations(self: Any, current_fp: AgentFingerprint, baseline_fp: AgentFingerprint)
```

Detect if an agent's behavior has drifted from its baseline fingerprint.

---

## probe_agent

```python
probe_agent(self: Any, proxy_fn: Any)
```

Run a suite of behavioral probes and generate a fingerprint.

---
