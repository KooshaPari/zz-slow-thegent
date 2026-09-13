<DONE>
# Proactive Governance Evolution Plan

> **Purpose**: Remove the need for users to explicitly indicate when governance should evolve. Agents and tooling should **proactively identify** governance gaps and **propose or implement** updates without being asked.
>
> **Status**: Plan | **Date**: 2026-02-16
> **Related**: [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md), [anti-patterns.md](../guides/anti-patterns.md)

---

## 1. Goal

**User should not need to say**: "Add governance for X" or "Update anti-patterns" or "We need a Library-First policy."

**Instead**: Agents and checkpoints should automatically detect when governance evolution is needed and either propose it or implement it as part of normal work.

---

## 2. Triggers for Governance Evolution

| Trigger | When | Action |
|---------|------|--------|
| **New pattern in code** | Agent writes custom retry/cache/watch/circuit-breaker | Check if anti-pattern exists; if not, add to anti-patterns.md and LIBRARY_FIRST_AUDIT |
| **Repeated violation** | Same pattern appears 2+ times in codebase | Propose governance rule; add to CLAUDE.md if generic |
| **New integration type** | Adding MCP server, new provider, new CLI surface | Check docs for governance; add section if missing |
| **Post-task completion** | Task touches governance domain (retry, cache, auth, etc.) | Checklist: "Does governance doc need updating?" |
| **Code review finding** | Reviewer flags "could use library" | Propose anti-pattern addition; update governance |
| **Hook detection** | suppress-* hooks fire on write/edit | Emit suggestion: "Consider adding to governance if pattern recurs" |

---

## 3. Agent Behavior (No User Prompt Required)

### 3.1 During Implementation

When implementing **any** feature, the agent should:

1. **Before writing**: If the work touches a governance domain (retry, cache, file watch, HTTP, auth, logging, etc.), check `docs/guides/anti-patterns.md` and `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md`, and follow existing guidance.

2. **If no guidance exists**: If the agent implements something in a domain that has no governance (e.g. a new type of rate limiting), **proactively add** a short governance note or update the relevant doc. Do not wait for the user to ask.

3. **If violating guidance**: If the agent must violate an existing rule (e.g. custom retry for a one-off case), **proactively document** why in an ADR or inline comment, and consider whether the rule should be refined.

### 3.2 At Task Completion

Before marking a task complete, the agent should run a **Governance Checkpoint**:

- Did this touch: retry, cache, file watch, HTTP, auth, logging, concurrency, subprocess?
- If yes: Is there governance for that domain? Is it up to date?
- If no or outdated: Propose or add a governance update as part of the same task.

### 3.3 When Discovering Patterns

When exploring or refactoring the codebase:

- If the agent finds a pattern that appears multiple times and has no governance (e.g. custom backoff in 3 places), **proactively propose** adding it to anti-patterns or LIBRARY_FIRST_AUDIT.
- Do not require the user to say "add governance for this."

---

## 4. Governance Domains (Checklist)

Agents should treat these as **governance domains** — when touching them, check and evolve governance:

| Domain | Governance Docs | Proactive Action |
|--------|-----------------|------------------|
| Retry/backoff | anti-patterns, TENACITY_RETRY_AUDIT, LIBRARY_FIRST | Use tenacity; if custom, add to audit |
| Caching | anti-patterns, LIBRARY_FIRST | Use cachetools; if custom, add pattern |
| File watching | anti-patterns, LIBRARY_FIRST | Use watchdog; if polling, add pattern |
| HTTP | anti-patterns | Use httpx |

| Circuit breaker | LIBRARY_FIRST | Use pybreaker or document |
| Logging | anti-patterns | Prefer structlog; document if stdlib |
| Rate limiting | — | Add governance when first implemented |
| Auth/security | — | Add governance when first implemented |
| Concurrency | — | Document patterns if novel |

---

## 5. Implementation Plan

### Phase 1: Agent Instructions (Immediate)

Add to CLAUDE.md, .cursor/rules, AGENTS.md:

- **Proactive Governance Evolution** section: Agents must check governance when touching governed domains; propose or add updates when gaps are found; do not wait for user to request.

### Phase 2: Task Completion Checklist

Add to task-done / story-done workflows (or equivalent):

- Step: "Governance checkpoint: Did this touch a governed domain? If governance missing or outdated, add/update as part of this task."

### Phase 3: Hook Enhancement (Optional)

Extend suppress-* hooks to append a suggestion when they fire:

- "Pattern detected. If this recurs, consider adding to docs/guides/anti-patterns.md."

### Phase 4: Scheduled Audit (Optional)

- Periodic (e.g. weekly or on release) job: Scan codebase for governance-domain patterns; compare against docs; emit report of gaps.

---

## 6. Proposed CLAUDE.md Addition

```markdown
# Proactive Governance Evolution

**Do not wait for the user to ask.** When your work touches a governance domain (retry, cache, file watch, HTTP, auth, logging, etc.):

1. **Check** existing governance (anti-patterns.md, LIBRARY_FIRST_AUDIT_AND_PLAN.md, CLAUDE.md).
2. **Follow** it. If governance is missing or outdated, **propose or add** an update as part of the same task.
3. **At task completion**: Run a governance checkpoint. If you touched a governed domain and governance is incomplete, update it.

You are not required to ask "should I add governance?" — if you see a gap, update it.
```

---

## 7. References

- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)
- [anti-patterns.md](../guides/anti-patterns.md)
- [TENACITY_RETRY_AUDIT_PLAN.md](./TENACITY_RETRY_AUDIT_PLAN.md)

---

## 4. IMPLEMENTATION: Governance Checkpoint

### 4.1 Checkpoint Script

```python
#!/usr/bin/env python3
# scripts/governance_checkpoint.py

import ast
from pathlib import Path
from typing import List, Tuple

GOVERNANCE_DOMAINS = [
    "retry",
    "cache",
    "file_watch",
    "http",
    "auth",
    "logging",
    "concurrency",
    "subprocess",
    "circuit_breaker",
]

ANTI_PATTERNS_PATH = Path(__file__).parent.parent / "docs" / "guides" / "anti-patterns.md"


def check_governance_domains(file_path: Path) -> List[Tuple[str, int]]:
    """Check if file touches governance domains."""
    try:
        content = file_path.read_text()
    except (UnicodeDecodeError, FileNotFoundError):
        return []

    violations = []

    # Check for custom implementations
    patterns = {
        "retry": [r"for\s+\w+\s+in\s+range\s*\(\s*\d+\s*\).*except", r"while.*sleep"],
        "cache": [r"dict\s*\(\s*\)", r"TTL.*cache", r"cache\[.*\]"],
        "http": [r"urllib\.request", r"requests\.get"],
        "subprocess": [r"subprocess\.Popen.*shell\s*=\s*True"],
    }

    for domain, regexes in patterns.items():
        import re

        for i, regex in enumerate(regexes):
            if re.search(regex, content, re.IGNORECASE):
                violations.append((domain, 0))
                break

    return violations


def run_checkpoint(file_path: Path):
    """Run governance checkpoint on a file."""
    violations = check_governance_domains(file_path)

    if violations:
        print(f"\n⚠️  Governance checkpoint triggered for: {file_path}")
        print(f"   Touched domains: {[v[0] for v in violations]}")
        print(f"   Action: Review anti-patterns and LIBRARY_FIRST_AUDIT")
        return False
    else:
        print(f"✅ {file_path.name} - No governance concerns")
        return True


if __name__ == "__main__":
    import sys

    file_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "src"
    run_checkpoint(file_path)
```

### 4.2 Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: governance-checkpoint
        name: Governance Checkpoint
        entry: python3 scripts/governance_checkpoint.py
        language: system
        pass_filenames: true
        stages: [pre-commit]
```

---

## 5. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added §4:** Implementation of Governance Checkpoint
   - Python checkpoint script
   - Pre-commit hook configuration
   - Governance domain detection

### Cross-References Added

- LIBRARY_FIRST_AUDIT_AND_PLAN.md
- anti-patterns.md

### Practical Additions

- Governance checkpoint script with domain detection
- Pre-commit hook for automated governance checks

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [GOVERNANCE_POLICY_AUDIT_RESEARCH.md](./GOVERNANCE_POLICY_AUDIT_RESEARCH.md) - Policy audit
- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md) - Library audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->
## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.

