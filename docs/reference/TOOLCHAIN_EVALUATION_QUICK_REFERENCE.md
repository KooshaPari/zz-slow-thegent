---
title: 2026 Toolchain & Framework Evaluation Quick Reference
date: 2026-02-22
status: active
owner: thegent
tags: [reference, tools, frameworks, adoption-guide]
---

# Quick Reference: Which Tool to Use (2025-2026 Landscape)

**TL;DR:** Adopt LiteLLM + Pyright now. Rust hooks in Q2. Monitor Letta for later.

---

## Cost Governance

### Q: How do I enforce cost budgets per agent/team?

**Answer:** Use **LiteLLM Proxy** with tag-based budgets.

```python
# In orchestrator
from litellm import Router

router = Router(
    model_list=[...],
    cost_tracking={
        "tags": {
            "team-ml": {"max_budget": 100.00, "budget_duration": "monthly"},
            "project-x": {"max_budget": 50.00, "budget_duration": "weekly"},
        }
    },
)

# Tag each call
response = router.completion(model="claude-3", messages=[...], metadata={"tags": ["team-ml", "project-x"]})
```

**Status:** ADOPT NOW (Q1 2026)

**Links:**
- [LiteLLM Tag Budgets](https://docs.litellm.ai/docs/proxy/tag_budgets)
- [LiteLLM Cost Tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)

---

## Hook/Lifecycle Management

### Q: Our shell script hooks (99KB) are unmaintainable. What's the replacement?

**Answer:** Migrate to **Rust event dispatcher** + **PyO3 bindings**.

**Architecture:**
```
Python (thegent orchestrator)
  ↓
PyO3 binding (hook_dispatch function)
  ↓
Rust event dispatcher (orsomafo or event-manager)
  ↓
Hook handlers (type-safe, compiled)
```

**Example Rust code:**
```rust
use pyo3::prelude::*;

#[pyfunction]
fn dispatch_hook(event_type: &str, context: PyDict) -> PyResult<PyDict> {
    // Type-safe event dispatch
    match event_type {
        "cost_limit_exceeded" => handle_cost_limit(context),
        "model_select" => handle_model_routing(context),
        _ => Err(PyErr::from_value(context))
    }
}

#[pymodule]
fn thegent_hooks(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(dispatch_hook, m)?)?;
    Ok(())
}
```

**Status:** ADOPT IN Q2 2026 (Weeks 5-8)

**Expected Gains:**
- 10-100x faster hook dispatch (50ms vs 500ms+).
- Type-safe governance.
- Parallel hook support.

**Links:**
- [orsomafo Event Dispatcher](https://github.com/shiftrightonce/orsomafo)
- [rust-vmm event-manager](https://github.com/rust-vmm/event-manager)
- [PyO3 User Guide](https://pyo3.rs/)
- [maturin](https://www.maturin.rs/tutorial.html)

---

## Type Checking

### Q: Type checking takes 5 minutes. How do I speed it up?

**Answer:** Replace **mypy** with **Pyright** or **Basedpyright**.

**Config change (pyrightconfig.json):**
```json
{
  "include": ["src/"],
  "typeCheckingMode": "strict",
  "pythonVersion": "3.14"
}
```

**CI change (GitHub Actions):**
```yaml
# Before
- run: mypy src/

# After
- run: pyright .
```

**Status:** ADOPT NOW (Q1 2026, 1 day)

**Expected Gains:**
- 3-5x faster type checking (5min → 1-2min).
- Stricter type errors (catches more issues).

**Why:** Pyright uses lazy/JIT type evaluation; mypy uses multi-pass analysis.

**Links:**
- [Pyright (Microsoft)](https://github.com/microsoft/pyright)
- [Basedpyright (Community fork)](https://docs.basedpyright.com/)
- [Performance Comparison](https://medium.com/@asma.shaikh_19478/python-type-checking-mypy-vs-pyright-performance-battle-fce38c8cb874)

---

## Agent Memory

### Q: My agents need persistent memory across sessions. What should I use?

**Answer Options (in order of recommendation):**

1. **Keep current (MAIF artifacts)** if memory complexity is low (simple state per agent).
2. **Evaluate Letta** if agents have multi-turn conversations (>10 turns) or shared memory.
3. **Evaluate Mem0** if managed scaling is a priority.

**Comparison:**

| System | Use Case | Effort | Status |
|--------|----------|--------|--------|
| **MAIF (Current)** | Simple state, low complexity | 0 | Keep |
| **Letta (MemGPT)** | Multi-turn + shared memory + self-editing | 2-4 weeks | MONITOR |
| **Mem0** | Managed service + consolidation | 1-2 weeks setup | MONITOR |

**When to Switch (Letta):**
- Agents have multi-turn conversations (>10 turns).
- Need for cross-agent memory sharing (teams).
- Memory consolidation is latency bottleneck (>1s).

**Status:** MONITOR (Q2-Q3 2026)

**Links:**
- [Letta](https://www.letta.com/)
- [Letta GitHub](https://github.com/letta-ai/letta)
- [Mem0](https://arxiv.org/html/2504.19413v1)

---

## Model Routing

### Q: How do I reduce agent cost without losing accuracy?

**Answer:** Implement **Pareto-frontier-based dynamic routing**.

**Concept:**
- Simple tasks → cheap models (Qwen3-32B, ~$0.001/call).
- Medium tasks → mid-tier (Claude-Sonnet, ~$0.01/call).
- Complex tasks → premium (Claude-Opus, ~$0.05/call).

**Expected result:** 5-10x cost reduction with <5% accuracy loss.

**Implementation (pseudo-code):**
```python
def select_model(task_context):
    complexity = classify_task(task_context)  # simple/medium/complex

    pareto_routing = {"simple": "qwen3-32b", "medium": "claude-sonnet", "complex": "claude-opus"}

    return pareto_routing[complexity]


# Use with LiteLLM
response = router.completion(model=select_model(task), messages=[...], metadata={"tags": ["pareto-routed"]})
```

**Status:** ADOPT IN Q2 2026 (Weeks 3-4)

**Links:**
- [syftr: Pareto-Optimal GenAI](https://arxiv.org/abs/2505.20266)
- [LLM Arena Pareto Frontier](https://winston-bosan.github.io/llm-pareto-frontier/)

---

## MCP (Model Context Protocol)

### Q: Do we need to replace FastMCP with a newer MCP framework?

**Answer:** No. FastMCP is production-ready and competitive.

**When to consider alternatives:**

| Alternative | When to Use |
|------------|------------|
| **Rust SDK** | If performance-critical; need compiled binary. |
| **Go SDK** | If multi-tenant; need distributed deployments. |
| **mcp.zig** | If Zig is part of polyglot strategy. |

**Official SDKs (2025+):**
- [MCP Rust SDK](https://github.com/modelcontextprotocol/rust-sdk)
- [MCP Go SDK](https://github.com/modelcontextprotocol/go-sdk)
- [mcp.zig](https://muhammad-fiaz.github.io/mcp.zig/)

**Status:** HOLD (no current blocker)

**Transport Note:**
- STDIO transport (current) is stable and unaffected.
- SSE deprecated as of MCP spec v2026-03-26; superseded by Streamable HTTP (no action needed unless remote federation planned).

**Links:**
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com/)

---

## Performance Optimization

### Q: I profiled and found hotspots in Python. Should I convert to Rust?

**Answer:** Yes, but only for performance-critical hot paths (10-20% of codebase).

**Tools:**

| Tool | Language | Maturity | Effort | Speedup |
|------|----------|----------|--------|---------|
| **PyO3 + maturin** | Rust → Python | Stable (2025) | 2-4 weeks per module | 5-15x |
| **Zig + pydust** | Zig → Python | Production-ready | 2-4 weeks per module | 5-15x (algorithm-dependent) |
| **CFFI** | C/Zig → Python | Mature | 1-2 weeks | Variable (no abstraction overhead) |

**When to convert (decision tree):**
1. Is the module in the critical path?
2. Is it CPU-bound (not I/O-bound)?
3. Does profiling show >50ms latency?
4. Is the algorithm amenable to compiled optimization?

If all true → use PyO3 + maturin.

**Example (PyO3):**
```rust
// Rust (src/lib.rs)
use pyo3::prelude::*;

#[pyfunction]
fn compute_expensive(data: Vec<i32>) -> i32 {
    // Critical algorithm here (now compiled)
    data.iter().sum()
}
```

```python
# Python (transparent)
from module import compute_expensive

result = compute_expensive([1, 2, 3])  # Calls compiled Rust!
```

**Status:** MONITOR (Q3 2026+)

**Links:**
- [PyO3 User Guide](https://pyo3.rs/)
- [maturin](https://www.maturin.rs/tutorial.html)
- [Zig Python Interop](https://lab.abilian.com/Tech/Python/Python%20%E2%86%94%EF%B8%8E%20Zig%20Interop/)

---

## Observability & Tracing

### Q: How do I trace multi-agent workflows end-to-end?

**Answer (Future):** Use **OpenTelemetry** for distributed tracing.

**When to adopt:**
- Multi-agent orchestration (>10 agents).
- Distributed deployment (agents across services).
- Enterprise observability requirement (audit trail).

**Current approach:** structlog (Python; sufficient for single-agent).

**OpenTelemetry semantic conventions for agents (2025):**
- Task, Action, Agent, Team, Artifact, Memory (standardizing).
- Works with CrewAI, LangGraph, AutoGen, IBM Bee, etc.

**Status:** MONITOR (Q3 2026+)

**Links:**
- [OpenTelemetry AI Agent Observability](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [VictoriaMetrics Stack](https://victoriametrics.com/blog/ai-agents-observability/)

---

## Guardrails & Safety

### Q: Do we need safety/content moderation for agents?

**Answer:** Only if required by compliance or SLA.

**Options (if needed):**

| Tool | Type | Use Case |
|------|------|----------|
| **Guardrails AI** | Open-source | Output validation + custom validators |
| **Lakera Guard** | SaaS | Drop-in proxy; jailbreak detection |
| **LlamaGuard** | Open-source | Unsafe prompt detection |
| **NeMo Guardrails** | Open-source | State machines for complex flows |

**Default recommendation:** Guardrails AI (open-source, flexible).

**Status:** HOLD (no current blocker)

**Links:**
- [Guardrails AI](https://www.guardrailsai.com/)
- [Lakera Guard](https://www.lakera.ai/)
- [LlamaGuard (Hugging Face)](https://huggingface.co/meta-llama/Llama-Guard-3-8B)

---

## Policy & Governance (Advanced)

### Q: Do we need Open Policy Agent (OPA) for fine-grained governance?

**Answer:** Not yet. Use hook-based governance (being migrated to Rust in Q2).

**When to adopt OPA:**
- Multi-tenant deployments (per-org, per-user policies).
- Complex policy language needed (Rego).
- Enterprise access control framework.

**Current:** Shell hooks + Rust dispatcher (sufficient).

**Status:** HOLD

**Links:**
- [Open Policy Agent](https://www.openpolicyagent.org/)

---

## Decision Tree: What Should I Use?

```
┌─────────────────────────────────────────┐
│ What's your problem?                    │
└─────────────────────────────────────────┘
            │
    ┌───────┼───────┬─────────┬──────────┬─────────────┐
    │       │       │         │          │             │
    v       v       v         v          v             v
  Cost    Hooks  Type       Memory    Routing      Safety
  Budget         Checking
    │       │       │         │          │             │
    │       │       │         │          │             │
    v       v       v         v          v             v
LiteLLM  Rust+   Pyright    Keep or   Pareto     Guardrails
Proxy   PyO3                Letta     Routing    AI or
(Q1)    (Q2)    (Q1)        (Q3)      (Q2)       Lakera
                                                  (TBD)
```

---

## Implementation Timeline

| Quarter | What | Effort | Expected Benefit |
|---------|------|--------|-------------------|
| **Q1 2026** | LiteLLM + Pyright | 3 days | Cost visibility + faster CI |
| **Q2 2026** | Rust hooks + Pareto routing | 6 weeks | 100x hook perf + 5-10x cost savings |
| **Q3 2026** | Monitor/evaluate Letta, OpenTel, PyO3 | — | Prepare for advanced use cases |

---

## When In Doubt

1. **Cost problem?** → LiteLLM
2. **Performance problem?** → Profile first; PyO3 only for hotspots
3. **Governance/hook problem?** → Rust + PyO3 (Q2)
4. **Memory problem?** → Keep MAIF for now; monitor Letta
5. **Safety problem?** → Guardrails AI (if needed)
6. **Type checking slow?** → Pyright (immediate)
7. **Model cost exploding?** → Pareto routing (Q2)

---

## Links & Resources

**Full Research:**
- [2025-2026 Landscape Research](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md)
- [Adoption Decision Framework](./ADOPTION_DECISION_FRAMEWORK_2026.md)

**Key Papers & Benchmarks:**
- [Pareto-Optimal GenAI (syftr)](https://arxiv.org/abs/2505.20266)
- [LLM Arena Pareto Frontier](https://winston-bosan.github.io/llm-pareto-frontier/)
- [Mem0: Production-Ready AI Agents](https://arxiv.org/html/2504.19413v1)
- [Rust FFI with PyO3](https://pyo3.rs/)

**Official SDKs & Tools:**
- [MCP Official](https://modelcontextprotocol.io/)
- [LiteLLM](https://docs.litellm.ai/)
- [Pyright](https://github.com/microsoft/pyright)
- [Letta](https://www.letta.com/)
- [Mem0](https://mem0.ai/)

---

## Questions?

See the full research document: [LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md)

Or the detailed roadmap: [ADOPTION_DECISION_FRAMEWORK_2026.md](./ADOPTION_DECISION_FRAMEWORK_2026.md)
