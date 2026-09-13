# Sandboxing Design (G-GP-08)

**Purpose:** Design agent sandbox isolation for trust boundary enforcement.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH, WP-3007, FR-014

---

## 1. Current State

- **Gap:** Agents run in host process; no isolation.
- **Risk:** Malicious or buggy agent output could affect host (file writes, network, env).

---

## 2. Design Goals

1. **Isolation:** Agent subprocess in restricted environment.
2. **Configurable:** Sandbox on/off; network egress allowlist; filesystem write restrictions.
3. **Trust boundary:** Document env transitions (host → sandbox → host).

---

## 3. Architecture Options

| Option                     | Isolation | Complexity | Use Case                     |
| -------------------------- | --------- | ---------- | ---------------------------- |
| A. Subprocess + env filter | Low       | Low        | Filter env vars only         |
| B. Docker                  | Medium    | Medium     | Container per run            |
| C. Firecracker/gVisor      | High      | High       | Strong isolation, cold start |

---

## 4. Recommended Phased Approach

### Phase 1: Env and CWD Restriction

- Restrict `cwd` to allowed prefixes.
- Filter env vars to safe subset (PATH, HOME, etc.).
- No new process isolation.

### Phase 2: Docker Runner

- Optional `THGENT_SANDBOX_DOCKER_IMAGE` — run agent in container.
- Mount only cwd (read-write) or read-only.
- Network: none or allowlist.

### Phase 3: Firecracker (Future)

- MicroVM per run for strongest isolation.
- Higher latency; for high-trust environments.

---

## 5. Implementation Phases

| Phase | Deliverable                         | Effort   |
| ----- | ----------------------------------- | -------- |
| P1    | Design doc (this)                   | Done     |
| P2    | CWD + env filter in runner          | 1–2 days |
| P3    | Docker runner option; config        | 3–5 days |
| P4    | Trust boundary doc; audit checklist | 1 day    |

---

## 6. Configuration

```yaml
governance:
  sandbox:
    enabled: false
    mode: env_filter # env_filter | docker | none
    cwd_allowed_prefixes: []
    env_allowlist: ["PATH", "HOME", "LANG"]
    docker_image: "" # e.g. thegent-agent:latest
    docker_network: none # none | host | allowlist
```

---

## 7. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-08
- FR-014 (sandboxing requirement)
- Firecracker: https://firecracker-microvm.github.io/
- gVisor: https://gvisor.dev/
