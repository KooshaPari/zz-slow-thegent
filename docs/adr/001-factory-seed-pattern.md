# ADR-001: Factory Seed Pattern

**Status:** Accepted  
**Date:** 2026-04-02  
**Authors:** thegent Team  
**Reviewers:** Sage Research Agent

---

## Context

thegent needs to enable reproducible environment bootstrapping. New team members spend days setting up development environments. The question is how to capture and replay environment setup reliably.

### Research Reviewed

1. **"Nix: A Safe and Policy-Free System for Software Deployment"** (Dolstra, 2006)
   - Reproducible builds via pure functions
   - But: Steep learning curve

2. **"Infrastructure as Code"** (Morris, 2020)
   - Declarative infrastructure
   - Factory pattern for resource creation

3. **"Domain-Driven Design"** (Evans, 2003)
   - Factory pattern for complex object creation
   - Bounded contexts for platform differences

4. **Existing Tools Survey:**
   - chezmoi: No factory pattern, manual setup
   - Nix flakes: Factory-like, but Nix-only
   - Homebrew Bundle: Single package manager
   - Ansible: Imperative, complex

### Alternatives Considered

| Approach                     | Pros                     | Cons                       | Research           |
| ---------------------------- | ------------------------ | -------------------------- | ------------------ |
| Shell scripts                | Simple                   | Fragile, platform-specific | Anti-pattern       |
| Nix flakes                   | Reproducible             | Nix-only, steep curve      | Dolstra 2006       |
| Ansible playbooks            | Powerful                 | Imperative, heavy          | Morris 2020        |
| Docker images                | Isolated                 | Not native, slow           | Container research |
| **Factory seeds (selected)** | Templated, multi-manager | New concept                | DDD factories      |

---

## Decision

**Adopt the Factory Seed Pattern: Templated, reproducible environment bootstrapping.**

### Factory Seed Structure

```
factory-seed/
├── thegent-skills/
│   └── SKILL.md          # Skill definition
├── nix/
│   └── flake.nix         # Nix reproducibility
├── homebrew/
│   └── Brewfile          # macOS packages
├── cargo/
│   └── Cargo.toml        # Rust tools
└── setup.sh              # Cross-platform bootstrap
```

### Key Components

1. **SKILL.md:** Declares capabilities, dependencies, platform support
2. **Multi-manager:** Nix + Homebrew + Cargo + custom unified
3. **Platform detection:** Automatic platform-specific path selection
4. **Idempotency:** Safe to re-run

---

## Consequences

### Positive

1. **Reproducibility:** Same seed = same environment (Dolstra 2006)
2. **Multi-manager:** Not locked into single package manager
3. **Declarative:** Intent captured, not procedure
4. **Composable:** Seeds can depend on other seeds
5. **Testable:** Factory validation before application

### Negative

1. **New Abstraction:** Team must learn factory pattern
2. **Complexity:** More complex than single shell script
3. **Debugging:** Multi-layer abstraction complicates troubleshooting

### Neutral

1. **Performance:** Slightly slower than imperative scripts (acceptable)
2. **Storage:** Seeds stored alongside configs

---

## Research Links

- Nix PhD thesis: https://nixos.org/~eelco/pubs/phd-thesis.pdf
- Factory pattern: https://en.wikipedia.org/wiki/Factory_method_pattern
- DDD patterns: https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf
- Infrastructure as Code: https://www.oreilly.com/library/view/infrastructure-as-code/9781098114671/

---

## Implementation

- `factory-seed/` — Seed templates
- `factory-seed/thegent-skills/SKILL.md` — Skill system
- `crates/thegent-factory/` — Factory implementation (planned)

---

**Supersedes:** N/A  
**Superseded by:** N/A
