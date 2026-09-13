# optimizer API Reference

> **Source**: `src/thegent/agents/optimizer.py`

WP-20003: Automated Prompt Optimization (DSPy).

Optimizes agent prompts using logical verification and performance-driven feedback loops.
Inspired by DSPy's programmatic prompt optimization.

---

## PromptOptimizer

Optimizes agent prompts by tracking version performance and proposing improvements.

### Methods

#### PromptOptimizer.**init**

```python
__init__(self: Any, agent_id: str, registry: Any)
```

---

#### PromptOptimizer.get_best_prompt

```python
get_best_prompt(self: Any)
```

Return the prompt content with the highest success rate.

---

#### PromptOptimizer.optimize

```python
optimize(self: Any, current_prompt: str, feedback: Any)
```

WP-20003: Optimize the current prompt based on feedback or performance history.

---

#### PromptOptimizer.record_run

```python
record_run(self: Any, version_id: str, result: RunResult, tokens: int, cost: float)
```

Record the outcome of a prompt version's execution.

---

---

## PromptVersion

A specific version of a prompt for an agent.

---

## get_best_prompt

```python
get_best_prompt(self: Any)
```

Return the prompt content with the highest success rate.

---

## optimize

```python
optimize(self: Any, current_prompt: str, feedback: Any)
```

WP-20003: Optimize the current prompt based on feedback or performance history.

---

## record_run

```python
record_run(self: Any, version_id: str, result: RunResult, tokens: int, cost: float)
```

Record the outcome of a prompt version's execution.

---
