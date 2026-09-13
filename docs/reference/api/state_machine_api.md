# state_machine API Reference

> **Source**: `src/thegent/agents/state_machine.py`

Fallback State Machine for agent orchestration.

Manages the lifecycle of a task run across multiple providers and retry attempts,
enforcing fallback policies and semantic validation gates.

---

## FallbackStateMachine

State machine for managing orchestration fallbacks.

### Methods

#### FallbackStateMachine.**init**

```python
__init__(self: Any, providers: list[str], run_id: Any, policy: Any, telemetry: Any, max_retries_per_provider: int, retry_delay_base: float)
```

---

#### FallbackStateMachine.run

```python
run(self: Any, runner_factory: Any, prompt: str, model: Any)
```

Execute the orchestration loop.

---

#### FallbackStateMachine.suggest_fallbacks

```python
suggest_fallbacks(self: Any)
```

Suggest safe fallback options for the current failed/blocked state (WP-4003).

---

#### FallbackStateMachine.validate_transition

```python
validate_transition(self: Any, from_state: str, to_state: str)
```

Validate if a state transition is allowed (WP-1004).

---

---

## OrchestrationState

State of an orchestration attempt.

---

## PromotionGate

WP-1005: Evidence capture and validation before state promotion.

### Methods

#### PromotionGate.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### PromotionGate.capture_evidence

```python
capture_evidence(self: Any, run_id: str, csm: Any)
```

Capture and hash CSM state as evidence.

---

#### PromotionGate.validate_promotion

```python
validate_promotion(self: Any, csm: Any, policy: Any)
```

Validate if CSM is ready for promotion based on policy.

---

---

## capture_evidence

```python
capture_evidence(self: Any, run_id: str, csm: Any)
```

Capture and hash CSM state as evidence.

---

## run

```python
run(self: Any, runner_factory: Any, prompt: str, model: Any)
```

Execute the orchestration loop.

---

## suggest_fallbacks

```python
suggest_fallbacks(self: Any)
```

Suggest safe fallback options for the current failed/blocked state (WP-4003).

---

## validate_promotion

```python
validate_promotion(self: Any, csm: Any, policy: Any)
```

Validate if CSM is ready for promotion based on policy.

---

## validate_transition

```python
validate_transition(self: Any, from_state: str, to_state: str)
```

Validate if a state transition is allowed (WP-1004).

---
