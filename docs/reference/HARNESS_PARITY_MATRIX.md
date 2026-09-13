# Harness Parity Matrix: Codex vs Claude Code vs Ante vs Gemini CLI vs Copilot Workspace

> **Status**: Reference matrix for Codex overhaul work
> **Updated**: February 2026
> **Scope**: AX (Agent Experience), UX (User Experience), DX (Developer Experience) comparison

---

## Executive Summary

This matrix compares five major agent harnesses across 13 feature categories. **Codex** leads in native Rust execution and MCP integration, and thegent now provides baseline project context, skills, and hook plumbing for Codex workflows. **Claude Code** still leads in session ergonomics and polished interactive UX. This document tracks parity deltas and next upgrades.

---

## Feature Comparison Matrix

| Feature Category               | Codex                                             | Claude Code                      | Ante\*                  | Gemini CLI                   | Copilot Workspace             | Priority to Add                     |
| ------------------------------ | ------------------------------------------------- | -------------------------------- | ----------------------- | ---------------------------- | ----------------------------- | ----------------------------------- |
| **Non-Interactive Mode**       | ✅ `codex exec`                                   | ✅ `--print`                     | ✅ Headless             | ✅ `--prompt`                | ⚠️ Limited (web-focused)      | N/A                                 |
| **JSONL/Streaming Output**     | ✅ `--json`                                       | ✅ `--output-format stream-json` | ⚠️ Partial              | ✅ JSON streaming            | ⚠️ Web-centric                | N/A                                 |
| **Project Memory/Context**     | ⚠️ Baseline (`.thegent/rules` -> `.codex/skills`) | ✅ `CLAUDE.md` + session memory  | ✅ Skills + memory      | ✅ Project config            | ❌ Per-issue only             | **P1: Expand memory depth**         |
| **Compact/Adaptive Context**   | ✅ Context compactor active                       | ✅ Adaptive thinking             | ✅ Selective context    | ✅ Hooks control context     | ✅ Specialized models         | **P2: Improve heuristics**          |
| **Skills/Commands System**     | ✅ `.codex/skills` + activate skill tools         | ✅ Skills (Anthropic standard)   | ✅ Skills + procedures  | ✅ Agent Skills (extensible) | ✅ Agent Skills               | **P1: Strengthen interoperability** |
| **Tool Approval/Permissions**  | ✅ `--dangerously-bypass-approvals`               | ✅ `--permission-mode`           | ✅ Fine-grained         | ✅ Built-in approval         | ✅ Multi-stage approval       | Configured                          |
| **Subprocess Invocation**      | ✅ Native Rust, direct                            | ✅ Via shell + monitoring        | ⚠️ Sandboxed            | ✅ Via shell                 | ✅ Via shell                  | N/A                                 |
| **MCP Integration**            | ✅ Full (Codex-native)                            | ✅ Full (100M+ downloads)        | ⚠️ Partial              | ✅ Full (Google-certified)   | ⚠️ Limited                    | N/A                                 |
| **Sub-Agent Spawning**         | ⚠️ Manual (Anthropic SDK)                         | ✅ Via Task tool                 | ✅ Built-in             | ⚠️ Via MCP                   | ✅ System of sub-agents       | Configured                          |
| **Session Continuity**         | ⚠️ Stateless (file-based)                         | ✅ Stateful (resume/teleport)    | ✅ Stateful             | ✅ Stateful                  | ✅ Workspace state            | **P1: Session persistence**         |
| **Multi-Model Support**        | ✅ 11+ models (via routing)                       | ✅ Multiple models               | ✅ Multiple models      | ✅ Multiple models           | ✅ Multi-model (experimental) | N/A                                 |
| **Filesystem Sandbox**         | ✅ Strict (workspace-write, full-auto)            | ✅ Sandbox mode (Linux/Mac)      | ✅ Strict               | ✅ Via hooks                 | ⚠️ Issue-scoped               | Configured                          |
| **Hooks/Middleware System**    | ⚠️ Post-run hook dispatcher baseline              | ⚠️ Limited (pre/post tool use)   | ✅ Extensive            | ✅ Rich lifecycle hooks      | ❌ None                       | **P1: Broaden lifecycle coverage**  |
| **Git Workflow Awareness**     | ⚠️ Basic (--skip-git-repo-check)                  | ✅ Native git operations         | ✅ Git-aware            | ✅ Git-aware                 | ✅ PR generation              | Configured                          |
| **Local/Offline Mode**         | ✅ Yes (Rust binary)                              | ✅ Yes (terminal-native)         | ✅ Yes                  | ⚠️ Needs internet            | ❌ Cloud-dependent            | N/A                                 |
| **Interactive Terminal UI**    | ⚠️ Minimal (JSON stream)                          | ✅ Rich TUI with diffs           | ✅ Rich TUI             | ✅ Rich TUI                  | ✅ Web UI (visual)            | **P2: Enhance TUI**                 |
| **Diff Review/Approval**       | ❌ None (JSON only)                               | ✅ Side-by-side diffs            | ✅ Built-in             | ✅ Built-in                  | ✅ Visual + PR                | **P1: Add diff UI**                 |
| **Provider Routing**           | ✅ LiteLLM router                                 | ✅ Native routing                | ⚠️ Limited              | ✅ Provider abstraction      | ⚠️ GitHub-centric             | N/A                                 |
| **API Key Management**         | ✅ Env-based, proxy-aware                         | ✅ Keyring + env                 | ✅ Secure storage       | ✅ Google Cloud IAM          | ✅ GitHub OAuth               | Configured                          |
| **Extensibility/Custom Tools** | ⚠️ Via MCP + SDK                                  | ✅ Skills + MCP                  | ✅ Skills + plugins     | ✅ Skills + MCP hooks        | ✅ Agent Skills + Actions     | N/A                                 |
| **Eval/Benchmark Mode**        | ❌ None                                           | ❌ None                          | ✅ Built-in metrics     | ⚠️ Partial                   | ⚠️ Partial (Terminal-Bench)   | **P2: Add benchmarking**            |
| **Error Recovery**             | ✅ Retry + hang detection                         | ✅ Adaptive retry                | ✅ Recovery logic       | ✅ Error handling            | ✅ Self-healing               | N/A                                 |
| **Cost Optimization**          | ✅ Model routing + caching                        | ✅ Model selection               | ✅ Selective processing | ✅ Token optimization        | ✅ Resource-aware             | Configured                          |

**Legend:**

- ✅ = Fully supported
- ⚠️ = Partial or limited
- ❌ = Not available

**Note on "Ante":** Ante refers to terminal agent patterns and open-source reference implementations (not a single harness). Features represent best-of-breed terminal agent UX.

---

## Critical Gaps (P0/P1 - Remaining Parity Work)

These features are fundamental to competitive parity with Claude Code and Gemini CLI:

### 1. **Project Memory/Context Depth** (Impact: HIGH)

- **Current baseline**: Codex flows already sync project instructions from `.thegent/rules/` into `.codex/skills/SKILL.md`, and runners can activate those skills.
- **Remaining gap**: Session-to-session memory depth and richer project state are still thinner than Claude Code-style continuity.
- **Impact on Codex**: Teams get baseline project guidance, but long-horizon continuity still requires manual carryover.
- **Recommended next step**:
  - Add explicit session memory persistence under `.codex/memory/`
  - Add compact project metadata (`.codex/project.yaml`) for defaults and policy knobs
  - Surface active project context in CLI status output

### 2. **Skills Interop and Coverage** (Impact: HIGH)

- **Current baseline**: `.codex/skills/` is already consumed and skill activation APIs are present.
- **Remaining gap**: Cross-harness interoperability and richer skill metadata contracts are incomplete.
- **Impact on Codex**: Teams can encode reusable workflows, but portability and consistency vary.
- **Recommended next step**:
  - Align skill metadata with shared external conventions where practical
  - Add validation/linting for skill manifests and activation failures
  - Expand discoverability and docs for skill activation flows

### 3. **Hooks Lifecycle Breadth** (Impact: MEDIUM)

- **Current baseline**: Codex runs dispatch post-agent hooks via the shared hook dispatcher.
- **Remaining gap**: Full lifecycle breadth (pre-init, pre/post tool, completion stages) is not yet symmetric with Gemini-style hooks.
- **Impact on Codex**: Post-run automation works, but teams still need additional hook points for full policy injection.
- **Recommended next step**:
  - Expand hook points beyond post-run events
  - Standardize hook payload schemas across lifecycle stages
  - Expose hook-point health/status in doctor/governance surfaces

### 4. **Diff Review UI** (Impact: MEDIUM)

- **Gap**: Codex outputs JSON only; no visual diff review for approvals.
- **What Claude Code does**: Side-by-side diffs, approval dialogs, easy review.
- **Impact on Codex**: Users must parse JSON or use external tools; slows approval workflows.
- **Recommended solution**:
  - Add TUI diff viewer when `--interactive` or no `--json` flag
  - Display file paths, additions/deletions, inline diffs
  - Approve/reject per file with keyboard navigation

---

## High-Value Improvements (P1 - Improve AX/DX)

These significantly enhance agent and developer experience without breaking current workflows:

### 1. **Session Persistence & Resumption** (Impact: MEDIUM-HIGH)

- **Gap**: Each Codex invocation is stateless; no resumable sessions.
- **What Claude Code does**: `--continue` flag, session IDs, state preservation.
- **Benefit**: Users can resume interrupted tasks, maintain context across multiple calls.
- **Recommended solution**:
  - Store session state in `.codex/.sessions/{session_id}/`
  - Add `--continue <session_id>` to resume
  - Auto-save state after each tool execution

### 2. **Context Compression/Adaptive Thinking** (Impact: MEDIUM)

- **Current baseline**: Context compaction already runs before Codex/LiteLLM execution.
- **Gap**: Heuristics and transparency are still weaker than top-tier adaptive systems.
- **What Claude Code does**: Adaptive thinking, selective context injection.
- **Benefit**: Faster responses, lower token cost for large codebases.
- **Recommended solution**:
  - Implement cost-aware context selection (file relevance scoring)
  - Add `--compact` mode for large projects
  - Cache and reuse file digests

### 3. **Interactive Mode Enhancements** (Impact: MEDIUM)

- **Gap**: No interactive TUI except JSON output; all approval is manual/external.
- **What Claude Code does**: Rich TUI with confirmations, diffs, inline approvals.
- **Benefit**: Better UX for developers; clear visibility into agent actions.
- **Recommended solution**:
  - Add `--interactive` mode with TUI (built on Rust terminal libs)
  - Display tool calls, ask for approval in real-time
  - Show diffs inline with approve/reject options

### 4. **Hooks Middleware System** (Impact: MEDIUM)

- **Current baseline**: Post-agent hook dispatch exists and is integrated.
- **Gap**: Missing broader lifecycle hook surface and config ergonomics.
- **What Gemini CLI does**: Full hook lifecycle for customization.
- **Benefit**: Teams can enforce policies, add logging, implement guardrails.
- **Recommended solution**:
  - Implement hook dispatcher (already designed in code)
  - Support bash/Python scripts in `.codex/hooks/`
  - Hook payload = JSON context for inspection/modification

---

## Quick Wins (Can be added in <1 sprint)

These are low-effort, high-value additions:

### 1. **Better Error Messages**

- Current: Generic "Agent stopped" or LiteLLM errors
- Recommended: Contextual errors with recovery hints, actionable messages

### 2. **Explicit Session IDs in Output**

- Current: No way to track or resume sessions
- Recommended: Print session ID at start, in JSON output

### 3. **Improved Hang Detection Logging**

- Current: Silent kill after idle timeout
- Recommended: Log why agent was killed, timestamps, last action

### 4. **Config File Support** (`.codexrc` or `.codex/config.yaml`)

- Current: All config via CLI flags and env vars
- Recommended: Project-level defaults (sandbox mode, model, timeout, hooks)

### 5. **Better Sandboxing Documentation**

- Current: `--sandbox workspace-write` and `--full-auto` are unclear
- Recommended: Clear matrix of what each mode allows (file ops, network, etc.)

---

## Codex Strengths (Already Leading)

These are areas where Codex excels and should be highlighted:

| Strength                          | Why It Matters                                                | Current State                  |
| --------------------------------- | ------------------------------------------------------------- | ------------------------------ |
| **Native Rust Binary**            | Fast startup, no interpreter overhead, strong isolation       | ✅ Unique among CLI agents     |
| **Direct MCP Support**            | Can talk directly to MCP servers; no proxy needed             | ✅ Already fully integrated    |
| **Multiple Sandbox Modes**        | Fine-grained control (workspace-write, full-auto, read-only)  | ✅ Better than most            |
| **Activity-Based Hang Detection** | Intelligent timeout (monitors actual activity, not wall time) | ✅ Unique feature              |
| **Retry + Adaptive Backoff**      | Transient error recovery is solid                             | ✅ Via resilience module       |
| **LiteLLM Router Integration**    | Can route to 11+ provider APIs transparently                  | ✅ Already working             |
| **Provider Abstraction**          | Supports claude, gemini, copilot, minimax, glm via same CLI   | ✅ Strong multi-provider story |

---

## Terminal Benchmark Spec

Use this spec to evaluate agent harnesses on standard tasks. Benchmarks should run across all harnesses for fair comparison.

### Test Categories

#### 1. **Code Generation** (Baseline capability)

- **Task**: Implement a function given a specification
- **Metrics**:
  - Success rate (code compiles, passes tests)
  - Latency (wall time from prompt to completion)
  - Tokens used (input + output)
  - Tool calls required (lower is better)
- **Test cases**:
  - Fibonacci function (simple, <10 lines)
  - Sorting algorithm (medium, <50 lines)
  - REST API handler (complex, multi-file, dependencies)

#### 2. **File Manipulation** (Core agent capability)

- **Task**: Modify, create, or refactor files per specification
- **Metrics**:
  - Correctness (changes match spec, no regressions)
  - Precision (unnecessary changes = penalty)
  - Tool call count (batch operations = better)
- **Test cases**:
  - Rename variable across 3 files
  - Add function to existing module
  - Refactor class into multiple files

#### 3. **Multi-Step Workflows** (Agent reasoning)

- **Task**: Complete a task requiring multiple tool calls and decisions
- **Metrics**:
  - Success rate
  - Steps to completion (fewer steps = more capable reasoning)
  - Feedback loop handling (how well it uses errors to self-correct)
- **Test cases**:
  - Setup test suite (create test dir, write config, generate tests)
  - Implement feature with tests (write code, verify tests pass, refactor)
  - Dependency upgrade (find outdated deps, update, run tests, fix breakage)

#### 4. **Tool Use & Error Recovery** (Robustness)

- **Task**: Recover from errors and use available tools correctly
- **Metrics**:
  - Recovery rate (tries again vs. gives up)
  - Attempt count (how many tries before success)
  - Error analysis (does it read error messages?)
- **Test cases**:
  - Syntax error in generated code (agent sees test failure, fixes it)
  - Missing import (agent reads error, adds import)
  - Broken reference (agent searches, finds, and fixes)

#### 5. **Codebase Understanding** (Context awareness)

- **Task**: Answer questions about codebase structure, dependencies, patterns
- **Metrics**:
  - Accuracy (correct answer rate)
  - Tool usage (does it read files or just guess?)
- **Test cases**:
  - Identify where to add new feature (which file, which function?)
  - Explain architecture (how do components interact?)
  - Find similar patterns (where is similar code?)

#### 6. **Git Awareness** (Workflow integration)

- **Task**: Understand and use git history/state
- **Metrics**:
  - Correctness (right files, right changes)
  - Git-native operations (commits, diffs, blame)
- **Test cases**:
  - Create feature branch, make changes, open PR
  - Find bug origin (git blame, git log analysis)
  - Understand pending changes (git status, git diff)

### Benchmark Execution

#### Setup

```bash
# For each harness, run:
./benchmark.sh --harness codex --suite code-gen --test fibonacci
./benchmark.sh --harness claude-code --suite code-gen --test fibonacci
# etc.
```

#### Metrics Collection

For each test, collect:

```json
{
  "harness": "codex",
  "suite": "code-gen",
  "test": "fibonacci",
  "latency_sec": 12.5,
  "tokens_input": 4200,
  "tokens_output": 340,
  "tool_calls": 3,
  "success": true,
  "error_recovery_attempts": 0,
  "timestamp": "2026-02-20T14:30:00Z"
}
```

#### Scoring

```
Success Rate: % tests that pass (0-100)
Efficiency Score: 100 - (latency_sec * 0.1 + tool_calls * 2)
Token Efficiency: success_rate / avg_tokens_per_test
Overall: (success_rate * 0.5 + efficiency_score * 0.3 + token_efficiency * 0.2)
```

#### Reporting

Summary table:
| Harness | Success Rate | Avg Latency | Avg Tool Calls | Overall Score |
|---|---|---|---|---|
| Codex | 92% | 11.2s | 3.4 | 87 |
| Claude Code | 95% | 9.8s | 3.1 | 91 |
| Gemini CLI | 88% | 10.5s | 3.8 | 82 |
| Copilot Workspace | 91% | 8.2s | 2.9 | 89 |

---

## Gap Analysis: Codex vs Claude Code (Detailed)

### Where Claude Code Leads

| Feature              | Codex                                | Claude Code                | Codex Path to Parity                                   |
| -------------------- | ------------------------------------ | -------------------------- | ------------------------------------------------------ |
| **Project Context**  | Baseline via synced `.codex/skills`  | CLAUDE.md + session memory | Add deeper persisted session memory + project metadata |
| **Skills**           | Active skills discovery + activation | Agent Skills (standard)    | Improve interop contracts + validation                 |
| **Hooks**            | Post-run dispatcher active           | Pre/post tool hooks        | Expand lifecycle coverage and hook UX                  |
| **Session Resume**   | Stateless                            | `--continue <id>`          | Add session ID tracking, state storage                 |
| **Diff UI**          | None                                 | Side-by-side diffs         | Add TUI diff viewer                                    |
| **Error Messages**   | Generic                              | Contextual + actionable    | Improve error module, add recovery hints               |
| **Interactive Mode** | JSON only                            | Rich TUI with approvals    | Implement interactive TUI                              |

### Where Codex Leads

| Feature               | Codex                                     | Claude Code              | Advantage                  |
| --------------------- | ----------------------------------------- | ------------------------ | -------------------------- |
| **Startup Speed**     | <100ms (Rust binary)                      | ~200ms (Node/TypeScript) | 2x faster                  |
| **Direct MCP**        | Native support                            | Via proxy                | Lower latency, no overhead |
| **Sandbox Isolation** | Fine-grained (workspace-write, full-auto) | Sandbox mode (newer)     | More control               |
| **Multi-Provider**    | 11+ providers (via routing)               | Native + routing         | Same parity                |
| **Hang Detection**    | Activity-based (smarter)                  | Timeout-based            | Better hang recovery       |

---

## Roadmap Summary

### Phase 1: Foundation (Month 1-2)

- [x] Baseline project-context sync (`.thegent/rules` -> `.codex/skills`)
- [x] Baseline skills activation and MCP skill tooling
- [x] Baseline post-run hook dispatcher
- [ ] Add deeper project/session memory system (`.codex/project.yaml` + `.codex/memory/`)

### Phase 2: UX Improvements (Month 2-3)

- [ ] Implement session persistence and resumption
- [ ] Add TUI diff viewer for review
- [ ] Enhance error messages with recovery hints

### Phase 3: Advanced Features (Month 3+)

- [ ] Context compaction heuristic upgrades and operator controls
- [ ] Full hooks lifecycle customization
- [ ] Benchmarking harness for competitive analysis

### Phase 4: Optimization (Ongoing)

- [ ] Token efficiency improvements
- [ ] Cost-aware model routing
- [ ] Performance profiling and tuning

---

## References & Data Sources

- **Claude Code**: [Claude Code Docs](https://code.claude.com/docs/en/overview) | [GitHub Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- **Gemini CLI**: [Gemini CLI GitHub](https://github.com/google-gemini/gemini-cli) | [Hooks Documentation](https://developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/)
- **GitHub Copilot Workspace**: [Agent Mode Preview](https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode) | [Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- **Agent Skills Standard**: [Agent Skills Overview](https://agentskills.io/home) | [Anthropic Standard Spec](https://agentskills.io/)
- **Terminal Benchmark**: [Terminal-Bench Leaderboard](https://www.tbench.ai/leaderboard)
- **Codex**: Internal thegent integration (`src/thegent/agents/codex_proxy.py`)

---

## Questions for Roadmap Prioritization

1. **Should Codex adopt the Anthropic Agent Skills standard?** (Aligns with Claude Code, Gemini CLI, Copilot)
2. **Is project-level memory a must-have for enterprise adoption?**
3. **How much TUI investment vs. staying JSON-focused?** (Terminal-first vs. integrations)
4. **Should session persistence use SQLite, files, or cloud state?**
5. **Which benchmarks matter most for competitive analysis?**

---

## Document Maintenance

Last updated: 2026-02-20
Maintained by: Codex Overhaul Task Force
Next review: March 31, 2026
