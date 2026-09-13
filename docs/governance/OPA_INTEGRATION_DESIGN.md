# OPA Integration Design (G-GP-01)

**Purpose:** Design Open Policy Agent (OPA) integration for declarative policy decisions.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH, WP-3001

---

## 1. Current State

- **PolicyEngine** (`src/thegent/execution.py`): Python-based policy evaluation before run execution.
- **Policies:** Critical lane confidence, unknown agents, production trust threshold, override with reason.
- **Gap:** Policies are hardcoded Python logic, not declarative Rego.

---

## 2. Design Goals

1. **Declarative policies:** Rego rules for auditability and non-developer edits.
2. **Phase 1 compatibility:** PolicyEngine remains primary; OPA as optional Phase 2.
3. **Input/output contract:** PolicyEngine → OPA input JSON; OPA → allow/deny + reason.

---

## 3. OPA Integration Architecture

```
RunMeta (run_id, agent, model, prompt, owner, cwd, ...)
    ↓
PolicyEngine.pre_check(run_meta)
    ↓
[If THGENT_OPA_URL set]
    → HTTP POST /v1/data/thegent/allow
    → Input: {"input": {"run_meta": {...}, "context": {...}}}
    → Output: {"result": {"allow": bool, "reason": str, "policy_id": str}}
    ↓
[Else] PolicyEngine Python logic (current)
    ↓
allow | deny
```

---

## 4. Rego Policy Structure

```
# policies/thegent/allow.rego
package thegent

default allow = false

allow = true {
    input.run_meta.agent != ""
    not is_unknown_agent(input.run_meta.agent)
    not critical_lane_low_confidence(input)
    not production_trust_violation(input)
}

allow = true {
    input.run_meta.override_reason != ""
    # Override with reason bypasses other checks
}

is_unknown_agent(agent) { ... }
critical_lane_low_confidence(input) { ... }
production_trust_violation(input) { ... }
```

---

## 5. Implementation Phases

| Phase | Deliverable                                                       | Effort          |
| ----- | ----------------------------------------------------------------- | --------------- |
| P1    | Document PolicyEngine as Phase 1 PDP; OPA as Phase 2 option       | Done (this doc) |
| P2    | Add `THGENT_OPA_URL` config; optional OPA client in PolicyEngine  | 2–3 days        |
| P3    | Ship default Rego policies; CI policy tests                       | 3–4 days        |
| P4    | Migrate all PolicyEngine rules to Rego; deprecate Python policies | 5–7 days        |

---

## 6. Configuration

```yaml
# config.example.yaml
governance:
  opa_url: "" # e.g. http://localhost:8181
  opa_timeout_ms: 500
  opa_fallback_allow: false # If OPA unreachable, allow or deny?
```

---

## 7. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-01
- `src/thegent/execution.py` — PolicyEngine
- OPA: https://www.openpolicyagent.org/
