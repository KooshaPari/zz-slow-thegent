# NeMo Guardrails Design (G-GP-02)

**Purpose:** Design input guardrails (NeMo-style) before OPA policy checks.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH

---

## 1. Current State

- **Gap:** No input validation rails before policy evaluation.
- **Risk:** Malformed prompts, injection patterns, or policy-bypass attempts reach PolicyEngine unfiltered.

---

## 2. Design Goals

1. **Input sanitization:** Validate/sanitize prompt, agent, model, cwd before OPA.
2. **Rail placement:** Input rails → OPA → execution (order matters).
3. **Configurable rules:** Allow org-specific blocklists, allowlists, regex patterns.

---

## 3. Architecture

```
User input (prompt, agent, model, cwd, ...)
    ↓
InputGuardrails.check(run_meta)
    ↓
[Pass] → OPA (or PolicyEngine)
[Fail] → Deny with rail_id, remediation hint
```

---

## 4. Rail Categories

| Rail             | Purpose                          | Example                         |
| ---------------- | -------------------------------- | ------------------------------- |
| prompt_length    | Max prompt chars                 | 64k default                     |
| prompt_blocklist | Block regex patterns             | PII, secrets, injection         |
| agent_allowlist  | Only known agents                | gemini, claude, cursor-agent    |
| cwd_restriction  | Path must be under allowed roots | /home, /workspace               |
| model_allowlist  | Only approved models             | claude-sonnet-4, gemini-3-flash |

---

## 5. Implementation Phases

| Phase | Deliverable                              | Effort |
| ----- | ---------------------------------------- | ------ |
| P1    | Design doc (this)                        | Done   |
| P2    | InputGuardrails class; config schema     | 2 days |
| P3    | Wire before PolicyEngine in execution.py | 1 day  |
| P4    | Default rules; CI tests                  | 2 days |

---

## 6. Configuration

```yaml
governance:
  input_guardrails:
    enabled: true
    prompt_max_chars: 65536
    prompt_blocklist_patterns: [] # Regex list
    agent_allowlist: [] # Empty = allow all
    cwd_allowed_prefixes: [] # Empty = allow all
```

---

## 7. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-02
- NeMo Guardrails: https://github.com/NVIDIA/NeMo-Guardrails
