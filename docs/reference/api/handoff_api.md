# handoff API Reference

> **Source**: `src/thegent/governance/handoff.py`

## HandoffIntegrity

WP-16005: Verifies that delegated prompts are complete and context-aware.

### Methods

#### HandoffIntegrity.**init**

```python
__init__(self: Any, workspace_root: Path)
```

---

#### HandoffIntegrity.analyze_prompt

```python
analyze_prompt(self: Any, prompt: str)
```

Analyze a prompt for potential missing context.

---

#### HandoffIntegrity.suggest_improvements

```python
suggest_improvements(self: Any, prompt: str, analysis: Any)
```

Suggest ways to improve the handoff prompt.

**Parameters**:

- `prompt`: Original prompt
- `analysis`: Optional analysis result from analyze_prompt()

**Returns**: Improved prompt with suggestions

---

#### HandoffIntegrity.validate_handoff

```python
validate_handoff(self: Any, prompt: str, min_completeness_score: int)
```

Validate that a handoff prompt meets minimum quality requirements.

**Parameters**:

- `prompt`: Prompt to validate
- `min_completeness_score`: Minimum completeness score required (default: 2)

**Returns**: Tuple of (is_valid, error_message)

---

---

## analyze_prompt

```python
analyze_prompt(self: Any, prompt: str)
```

Analyze a prompt for potential missing context.

---

## suggest_improvements

```python
suggest_improvements(self: Any, prompt: str, analysis: Any)
```

Suggest ways to improve the handoff prompt.

**Parameters**:

- `prompt`: Original prompt
- `analysis`: Optional analysis result from analyze_prompt()

**Returns**: Improved prompt with suggestions

---

## validate_handoff

```python
validate_handoff(self: Any, prompt: str, min_completeness_score: int)
```

Validate that a handoff prompt meets minimum quality requirements.

**Parameters**:

- `prompt`: Prompt to validate
- `min_completeness_score`: Minimum completeness score required (default: 2)

**Returns**: Tuple of (is_valid, error_message)

---
