# config_wizard API Reference

> **Source**: `src/thegent/infra/config_wizard.py`

Interactive configuration wizard for thegent setup.

This module provides a step-by-step wizard for configuring thegent with
sensible defaults and validation at each step.

---

## ConfigWizard

Interactive configuration wizard.

### Methods

#### ConfigWizard.**init**

```python
__init__(self: Any, config_path: Any)
```

Initialize the wizard.

**Parameters**:

- `config_path`: Path to .env file (default: .env in current directory)

---

#### ConfigWizard.run

```python
run(self: Any)
```

Run the configuration wizard.

**Returns**: True if configuration was successful, False otherwise

---

---

## run

```python
run(self: Any)
```

Run the configuration wizard.

**Returns**: True if configuration was successful, False otherwise

---

## run_wizard

```python
run_wizard(config_path: Any)
```

Run the configuration wizard.

**Parameters**:

- `config_path`: Path to .env file (default: .env in current directory)

**Returns**: True if configuration was successful, False otherwise

---
