# Learning Paths for thegent

**Purpose:** Structured progression routes from beginner to advanced for different roles.
**Audience:** New developers, AI agents, DevOps engineers, and platform contributors.

---

## How to Use This Guide

Pick the path that matches your role and current level. Each path lists documents in reading order with estimated time. You do not need to read everything -- start with your path and branch out as needed.

---

## Path 1: User (Running thegent to orchestrate agents)

### Beginner -- First Day (30 min)

| Order | Document                                                 | Time   | What You Learn                              |
| ----- | -------------------------------------------------------- | ------ | ------------------------------------------- |
| 1     | [00_GETTING_STARTED.md](./00_GETTING_STARTED.md)         | 5 min  | Install, configure, run first command       |
| 2     | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md) | 15 min | Core vocabulary and how pieces fit together |
| 3     | [QUICK_START.md](./QUICK_START.md)                       | 5 min  | CLI commands and provider setup             |
| 4     | [PROVIDER_SETUP_GUIDE.md](./PROVIDER_SETUP_GUIDE.md)     | 5 min  | Detailed provider configuration             |

**Checkpoint:** You can run `thegent free "hello"`, check `thegent doctor`, and explain what a CSM is.

### Intermediate -- First Week (1-2 hours)

| Order | Document                                                 | Time   | What You Learn                 |
| ----- | -------------------------------------------------------- | ------ | ------------------------------ |
| 5     | [TASK_ROUTING_QUICK_REF.md](./TASK_ROUTING_QUICK_REF.md) | 10 min | How routing selects providers  |
| 6     | [WORKSTREAM_OPERATIONS.md](./WORKSTREAM_OPERATIONS.md)   | 10 min | Using the work stream backlog  |
| 7     | [SWARM_CONTROLLER_USAGE.md](./SWARM_CONTROLLER_USAGE.md) | 15 min | Multi-agent coordination       |
| 8     | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)               | 10 min | Common issues and fixes        |
| 9     | [DOCTOR_FIXES.md](./DOCTOR_FIXES.md)                     | 5 min  | Specific doctor-reported fixes |

**Checkpoint:** You can run multi-agent tasks, use work streams, and diagnose provider failures.

### Advanced -- Mastery (2-3 hours)

| Order | Document                                                                               | Time   | What You Learn                          |
| ----- | -------------------------------------------------------------------------------------- | ------ | --------------------------------------- |
| 10    | [PRD.md](../../PRD.md)                                                                 | 10 min | Full product vision and success metrics |
| 11    | [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](./AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md) | 20 min | Deep debugging techniques               |
| 12    | [CROSS_PLATFORM_COMPLETE.md](./CROSS_PLATFORM_COMPLETE.md)                             | 15 min | macOS/Windows/Linux/container specifics |
| 13    | [SHELL_ENVIRONMENT_MANAGEMENT.md](./SHELL_ENVIRONMENT_MANAGEMENT.md)                   | 15 min | Shell integration internals             |
| 14    | docs/architecture/civilization.md                                                      | 30 min | Multi-tenant civilization framework     |

**Checkpoint:** You can troubleshoot any thegent failure, configure complex multi-agent topologies, and operate across platforms.

---

## Path 2: Contributor (Developing thegent itself)

### Beginner -- Orientation (45 min)

| Order | Document                                                 | Time   | What You Learn                                |
| ----- | -------------------------------------------------------- | ------ | --------------------------------------------- |
| 1     | [00_GETTING_STARTED.md](./00_GETTING_STARTED.md)         | 5 min  | Install and project layout                    |
| 2     | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md) | 15 min | Domain model and vocabulary                   |
| 3     | [DEVELOPER_QUICKSTART.md](./DEVELOPER_QUICKSTART.md)     | 10 min | `task lint`, `task test`, common fixes        |
| 4     | [CLAUDE.md](../../CLAUDE.md)                             | 15 min | Project rules, forbidden patterns, governance |

**Checkpoint:** You can run `task quality`, know what is forbidden (fallbacks, legacy compat, process killing), and understand the hook system.

### Intermediate -- Productive Contributor (2-3 hours)

| Order | Document                                                       | Time   | What You Learn                                        |
| ----- | -------------------------------------------------------------- | ------ | ----------------------------------------------------- |
| 5     | [FUNCTIONAL_REQUIREMENTS.md](../../FUNCTIONAL_REQUIREMENTS.md) | 30 min | Formal FR-XXX-NNN requirements with traces            |
| 6     | [anti-patterns.md](./anti-patterns.md)                         | 15 min | What NOT to do and why                                |
| 7     | [architecture-enforcement.md](./architecture-enforcement.md)   | 15 min | Layer boundaries, import rules, tach.toml             |
| 8     | [TESTING.md](./TESTING.md)                                     | 15 min | Test-first mandate, coverage targets, maturity levels |
| 9     | docs/governance/GOVERNANCE_SUMMARY.md                          | 15 min | Governance policies overview                          |
| 10    | docs/reference/WORK_STREAM.md                                  | 10 min | Current backlog and how to claim items                |

**Checkpoint:** You can implement a new feature following TDD, trace it to an FR, pass all quality gates, and submit a PR.

### Advanced -- Architecture and Platform (3-4 hours)

| Order | Document                                                                      | Time   | What You Learn                       |
| ----- | ----------------------------------------------------------------------------- | ------ | ------------------------------------ |
| 11    | [ADR.md](../../ADR.md)                                                        | 20 min | Architecture decisions and rationale |
| 12    | docs/architecture/civilization.md                                             | 30 min | Full civilization framework          |
| 13    | docs/concepts/coordination.md                                                 | 20 min | Cross-project communication patterns |
| 14    | docs/reference/CLAUDE_CORE_GUIDELINES.md                                      | 20 min | Full global baseline for agents      |
| 15    | docs/reference/CLAUDE_THEGENT_RUNTIME_APPENDIX.md                             | 15 min | Runtime operations specifics         |
| 16    | docs/context/GOVERNANCE.md                                                    | 15 min | Context documentation standards      |
| 17    | docs/governance/POLYGLOT_RUNTIME_COVERAGE_AND_CONVERSION_MATRIX_2026-02-21.md | 20 min | Multi-language runtime policy        |

**Checkpoint:** You can design new subsystems, write ADRs, define new contracts, and extend the civilization framework.

---

## Path 3: AI Agent (Operating inside thegent as an autonomous agent)

This path is for AI agents (Claude, Codex, etc.) that are running tasks within a thegent-managed environment.

### Essential -- Before First Task (10 min)

| Order | Document                                                                    | Time  | What You Learn                                 |
| ----- | --------------------------------------------------------------------------- | ----- | ---------------------------------------------- |
| 1     | [CLAUDE.md](../../CLAUDE.md)                                                | 5 min | Critical rules (especially FORBIDDEN sections) |
| 2     | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md) (Glossary section) | 3 min | Vocabulary                                     |
| 3     | [DEVELOPER_QUICKSTART.md](./DEVELOPER_QUICKSTART.md)                        | 2 min | Quality commands                               |

**Checkpoint:** You know what you must never do (kill processes, add fallbacks, silent error handling) and how to run quality checks.

### Operational -- Autonomous Work (20 min)

| Order | Document                                                         | Time   | What You Learn                          |
| ----- | ---------------------------------------------------------------- | ------ | --------------------------------------- |
| 4     | [AGENT_INSTRUCTIONS_THEGENT.md](./AGENT_INSTRUCTIONS_THEGENT.md) | 10 min | Agent-specific operational instructions |
| 5     | docs/reference/WORK_STREAM.md                                    | 5 min  | Current backlog                         |
| 6     | [anti-patterns.md](./anti-patterns.md)                           | 5 min  | Patterns to avoid                       |

**Checkpoint:** You can claim work items, execute them with proper quality gates, and avoid all anti-patterns.

### Advanced -- Multi-Agent Coordination (30 min)

| Order | Document                            | Time   | What You Learn                       |
| ----- | ----------------------------------- | ------ | ------------------------------------ |
| 7     | docs/concepts/coordination.md       | 15 min | How to communicate with other agents |
| 8     | docs/concepts/swarm-architecture.md | 10 min | Self-healing swarm controller        |
| 9     | docs/architecture/civilization.md   | 5 min  | Overview of civilization framework   |

**Checkpoint:** You can participate in multi-agent coordination, handle task dispatch, and escalate properly.

---

## Path 4: DevOps / Platform Engineer

### Quick Ramp (30 min)

| Order | Document                                                                      | Time   | What You Learn                    |
| ----- | ----------------------------------------------------------------------------- | ------ | --------------------------------- |
| 1     | [00_GETTING_STARTED.md](./00_GETTING_STARTED.md)                              | 5 min  | Install and basics                |
| 2     | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md) (Governance section) | 5 min  | Guardrails, audit trail, policies |
| 3     | [CROSS_PLATFORM_QUICK_START.md](./CROSS_PLATFORM_QUICK_START.md)              | 10 min | Platform-specific setup           |
| 4     | docs/concepts/security-model.md                                               | 10 min | Security architecture             |

### Operational (1 hour)

| Order | Document                                                             | Time   | What You Learn                  |
| ----- | -------------------------------------------------------------------- | ------ | ------------------------------- |
| 5     | [SHELL_ENVIRONMENT_MANAGEMENT.md](./SHELL_ENVIRONMENT_MANAGEMENT.md) | 15 min | Shell integration and hardening |
| 6     | [RUNTIME_OPTIMIZATION.md](./RUNTIME_OPTIMIZATION.md)                 | 15 min | Performance tuning              |
| 7     | [SWARM_CONTROLLER_USAGE.md](./SWARM_CONTROLLER_USAGE.md)             | 15 min | Swarm operations                |
| 8     | [INSTALLATION.md](./INSTALLATION.md)                                 | 10 min | Detailed installation reference |

**Checkpoint:** You can deploy thegent in production, configure governance policies, tune performance, and operate the swarm controller.

---

## Concept Dependency Graph

Understanding which concepts build on others helps you know when to backtrack:

```
Installation
    |
    v
CLI Basics (free, run, doctor, ps)
    |
    v
Providers & Routing ----------> Fallback Chains
    |                                |
    v                                v
CSM & Contracts -------> Semantic Validation
    |
    v
Governance (guardrails, cost, policies)
    |
    v
Hooks & Lifecycle
    |
    +-------> Work Streams & Plans
    |
    +-------> Agent Mesh & Coordination
    |              |
    |              v
    |         Civilization Framework
    |              |
    |              v
    |         Multi-Agent Execution Modes
    |
    +-------> MCP Server & Tools
    |
    +-------> Memory & Gardener
```

If you encounter a concept you do not understand, trace it back up this graph to find the prerequisite.

---

## Reading Strategy Tips

1. **Skim first, deep-read second.** On first pass, read headings and tables. Return for full text when you need it.

2. **Use the glossary.** The [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md) glossary defines every domain term. Refer to it when you hit unfamiliar vocabulary.

3. **Run commands as you read.** Every guide includes runnable commands. Execute them in a test environment to build muscle memory.

4. **Follow cross-references.** thegent docs are heavily cross-linked. When a document points to another, that link is intentional -- the referenced doc fills a gap the current doc assumes.

5. **Check the date.** Some docs carry dates. If a doc is older than 30 days, verify its claims against the current codebase -- thegent evolves rapidly.

6. **Start with your role's path.** Do not try to read everything. The paths above are ordered by importance for each role.

---

## Document Index by Topic

For quick lookup when you need a specific topic:

| Topic           | Primary Document                                                     | Backup                                                                                 |
| --------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Installation    | [00_GETTING_STARTED.md](./00_GETTING_STARTED.md)                     | [INSTALLATION.md](./INSTALLATION.md)                                                   |
| CLI commands    | [QUICK_START.md](./QUICK_START.md)                                   | [THGENT_CLI_REFERENCE.md](./THGENT_CLI_REFERENCE.md)                                   |
| Domain concepts | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md)             | [PRD.md](../../PRD.md)                                                                 |
| Architecture    | docs/architecture/                                                   | [ADR.md](../../ADR.md)                                                                 |
| Governance      | docs/governance/                                                     | [CLAUDE.md](../../CLAUDE.md)                                                           |
| Testing         | [TESTING.md](./TESTING.md)                                           | [PR_TEST_IMPACT_REDUCTION.md](./PR_TEST_IMPACT_REDUCTION.md)                           |
| Debugging       | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)                           | [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](./AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md) |
| Multi-agent     | docs/concepts/coordination.md                                        | [SWARM_CONTROLLER_USAGE.md](./SWARM_CONTROLLER_USAGE.md)                               |
| Cross-platform  | [CROSS_PLATFORM_QUICK_START.md](./CROSS_PLATFORM_QUICK_START.md)     | [CROSS_PLATFORM_COMPLETE.md](./CROSS_PLATFORM_COMPLETE.md)                             |
| Shell           | [SHELL_ENVIRONMENT_MANAGEMENT.md](./SHELL_ENVIRONMENT_MANAGEMENT.md) | [SHELL_ADVANCED_FEATURES.md](./SHELL_ADVANCED_FEATURES.md)                             |
| Security        | docs/concepts/security-model.md                                      | [OAUTH_ONLY_AUTHENTICATION.md](./OAUTH_ONLY_AUTHENTICATION.md)                         |
| Performance     | [RUNTIME_OPTIMIZATION.md](./RUNTIME_OPTIMIZATION.md)                 | [JOB_POOL_USAGE.md](./JOB_POOL_USAGE.md)                                               |
