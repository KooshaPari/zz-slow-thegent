# demo_gif_generator API Reference

> **Source**: `src/thegent/docgen/demo_gif_generator.py`

Auto-generate demo GIFs from scripts.

---

## DemoGIFGenerator

Generate demo GIFs from scripts using VHS or similar tools.

### Methods

#### DemoGIFGenerator.**init**

```python
__init__(self: Any, vhs_path: Any)
```

Initialize demo GIF generator.

**Parameters**:

- `vhs_path`: Path to VHS binary

---

#### DemoGIFGenerator.generate_from_commands

```python
generate_from_commands(self: Any, commands: list[str], output_path: Path)
```

Generate GIF from a list of commands.

**Parameters**:

- `commands`: List of shell commands
- `output_path`: Output GIF path

**Returns**: True if successful

---

#### DemoGIFGenerator.generate_from_script

```python
generate_from_script(self: Any, script_path: Path, output_path: Path)
```

Generate GIF from a script file.

**Parameters**:

- `script_path`: Path to script file (.tape for VHS)
- `output_path`: Output GIF path

**Returns**: True if successful

---

---

## generate_from_commands

```python
generate_from_commands(self: Any, commands: list[str], output_path: Path)
```

Generate GIF from a list of commands.

**Parameters**:

- `commands`: List of shell commands
- `output_path`: Output GIF path

**Returns**: True if successful

---

## generate_from_script

```python
generate_from_script(self: Any, script_path: Path, output_path: Path)
```

Generate GIF from a script file.

**Parameters**:

- `script_path`: Path to script file (.tape for VHS)
- `output_path`: Output GIF path

**Returns**: True if successful

---
