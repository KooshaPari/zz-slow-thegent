# OpenCode Harness Governance

**Status:** Draft
**Date:** 2026-05-01
**Supersedes:** N/A
**Related:** `23_ARCHITECTURAL_GOVERNANCE.md`, `TERMINOLOGY_LAYERS.md`

---

## 1. Purpose & Scope

This document establishes governance for the **OpenCode** harness integration in thegent.

OpenCode is a headless coding agent CLI that executes agentic tasks via direct invocation. It complements Codex as a CC0-licensed alternative harness.

### 1.1 Relationship to Codex

| Dimension               | Codex           | OpenCode            |
| ----------------------- | --------------- | ------------------- |
| License                 | Proprietary     | CC0 (public domain) |
| Execution mode          | Direct CLI      | Direct CLI          |
| Model routing           | Via proxy       | Via proxy           |
| Process pattern         | `codex`         | `opencode`          |
| Registry classification | `_PROXY_AGENTS` | `_DIRECT_AGENTS`    |

---

## 2. Integration Architecture

### 2.1 Registry Classification

```python
# src/thegent/agents/registry.py
_DIRECT_AGENTS = frozenset({"cursor-agent", "opencode"})
```

OpenCode runs as a **direct agent** (no proxy required).

### 2.2 Process Discovery

```python
# src/thegent/infra/discovery_v2.py
AGENT_PATTERNS = {
    "codex": ["codex"],
    "opencode": ["opencode"],
}
```

### 2.3 Execution Path

```
thegent dispatch → DirectAgentRunner → opencode CLI → model completion
```

---

## 3. wine→Phenotype Translation

> **Note:** "wine" refers to a hypothetical translation/adapter layer between external harnesses and the phenotype ecosystem. This section is a placeholder for future implementation.

### 3.1 Translation Contract

When a harness invokes phenotype-native commands, the translation layer MUST:

1. **Normalize paths** — Convert `/wine/...` → `/phenotype/...`
2. **Translate env vars** — Map harness-specific vars to phenotype equivalents
3. **Preserve semantics** — No lossy transformations

### 3.2 Placeholder Implementation

```python
# TODO: Implement wine→phenotype translation layer
# See: https://github.com/KooshaPari/thegent/issues/TODO
```

---

## 4. CC0 License Compliance

OpenCode is released under **CC0 1.0 Universal (Public Domain Dedication)**.

### 4.1 Obligations

- No attribution required (but recommended in documentation)
- No restrictions on use, modification, or distribution
- Phenotype integration does not create derivative work obligations

### 4.2 Comparison with Codex

| Aspect           | Codex              | OpenCode |
| ---------------- | ------------------ | -------- |
| License          | Proprietary EULA   | CC0      |
| Usage tracking   | Required           | None     |
| Commercial terms | Separate agreement | None     |

---

## 5. Governance Rules

### 5.1 Integration Requirements

- [ ] OpenCode binary resolution via `THGENT_OPENCODE_CMD` env var
- [ ] Fallback to `shutil.which("opencode")`
- [ ] Health check polling with 5s timeout
- [ ] Process cleanup on exit

### 5.2 Quality Gates

- [ ] Unit tests in `tests/unit/agents/test_opencode_*.py`
- [ ] Integration tests in `tests/integration/test_opencode_*.py`
- [ ] Discovery pattern coverage in `tests/agent_tests.rs`

### 5.3 Parity with Codex

OpenCode integration MUST maintain feature parity with Codex where applicable:

| Feature           | Codex | OpenCode     | Parity |
| ----------------- | ----- | ------------ | ------ |
| Direct invocation | ✅    | ✅           | ✅     |
| Proxy fallback    | ✅    | N/A (direct) | N/A    |
| Process discovery | ✅    | ✅           | ✅     |
| Model routing     | ✅    | ✅           | ✅     |
| Heartbeat monitor | ✅    | ✅           | ✅     |

---

## 6. Related Documents

| Document                            | Purpose                                          |
| ----------------------------------- | ------------------------------------------------ |
| `TERMINOLOGY_LAYERS.md`             | Layer vocabulary (harness/LLM/agent definitions) |
| `23_ARCHITECTURAL_GOVERNANCE.md`    | Hexagonal, XDD, SOLID mandates                   |
| `src/thegent/agents/registry.py`    | Agent registry and runner selection              |
| `src/thegent/infra/discovery_v2.py` | Process discovery patterns                       |

---

## 7. Open Questions

- [ ] **wine→phenotype scope:** What specific translations are needed?
- [ ] **Model selection:** Should OpenCode use same model router as Codex?
- [ ] **Fallback chains:** OpenCode in `_DIRECT_AGENTS` — should it have proxy fallback?

---

## 8. Changelog

| Date       | Change               |
| ---------- | -------------------- |
| 2026-05-01 | Initial stub created |

---

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->
<!-- Required for all Phenotype governance docs -->
