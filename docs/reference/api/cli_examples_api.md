# cli_examples API Reference

> **Source**: `src/thegent/docgen/cli_examples.py`

Auto-generate CLI examples.

---

## CLIExamplesGenerator

Generate CLI examples automatically.

### Methods

#### CLIExamplesGenerator.**init**

```python
__init__(self: Any, command: str)
```

Initialize CLI examples generator.

**Parameters**:

- `command`: Command name

---

#### CLIExamplesGenerator.generate_examples

```python
generate_examples(self: Any, command: str)
```

Generate examples for a command.

**Parameters**:

- `command`: Command name

**Returns**: List of example dictionaries

---

#### CLIExamplesGenerator.get_all_commands

```python
get_all_commands(self: Any)
```

Get all available commands.

**Returns**: List of command names

---

#### CLIExamplesGenerator.render_markdown

```python
render_markdown(self: Any, examples: list[dict[(str, Any)]])
```

Render examples as markdown.

**Parameters**:

- `examples`: List of example dictionaries

**Returns**: Markdown string

---

---

## generate_examples

```python
generate_examples(self: Any, command: str)
```

Generate examples for a command.

**Parameters**:

- `command`: Command name

**Returns**: List of example dictionaries

---

## get_all_commands

```python
get_all_commands(self: Any)
```

Get all available commands.

**Returns**: List of command names

---

## render_markdown

```python
render_markdown(self: Any, examples: list[dict[(str, Any)]])
```

Render examples as markdown.

**Parameters**:

- `examples`: List of example dictionaries

**Returns**: Markdown string

---
