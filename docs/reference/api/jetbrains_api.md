# jetbrains API Reference

> **Source**: `src/thegent/integrations/jetbrains.py`

JetBrains IDE integration utilities for thegent.

Provides detection of installed JetBrains IDEs and configuration of the MCP
server endpoint so the JetBrains AI plugin can connect to thegent.

MCP config path per IDE: ~/.config/JetBrains/&lt;IDE&gt;/mcp.json
MCP config format:
{"mcpServers": {"thegent": {"url": "http://localhost:3847/mcp"}}}

FR traceability: FR-IDE-001 (JetBrains MCP integration)

---

## JetBrainsConfig

Configuration record for a detected JetBrains IDE installation.

### Methods

#### JetBrainsConfig.mcp_config_path

```python
mcp_config_path(self: Any)
```

Absolute path to the mcp.json configuration file.

---

---

## JetBrainsIntegration

Detect installed JetBrains IDEs and manage their MCP configuration.

Usage::

    integration = JetBrainsIntegration()
    configs = integration.detect_installed_ides()
    for cfg in configs:
        path = integration.write_mcp_config(cfg)
        print(f"Wrote {path}")

### Methods

#### JetBrainsIntegration.**init**

```python
__init__(self: Any, mcp_server_url: str, serena_project_root: str)
```

Initialise with target MCP server URL and optional project root.

**Parameters**:

- `mcp_server_url`: URL of the thegent MCP server.
- `serena_project_root`: Absolute project root for Serena context.
  If empty, the IDE plugin will use its own
  project root.

---

#### JetBrainsIntegration.detect_installed_ides

```python
detect_installed_ides(self: Any)
```

Return a list of JetBrainsConfig for every installed JetBrains IDE.

The method scans the platform-appropriate JetBrains config base
directory (e.g. ~/Library/Application Support/JetBrains on macOS) for
sub-directories whose names match known IDE patterns.

**Returns**: List of JetBrainsConfig instances, one per detected IDE installation.
Returns an empty list when no JetBrains IDEs are found.

---

#### JetBrainsIntegration.is_mcp_plugin_installed

```python
is_mcp_plugin_installed(self: Any, config: JetBrainsConfig)
```

Check whether the thegent MCP plugin entry exists in the IDE config.

**Parameters**:

- `config`: JetBrainsConfig for the IDE to inspect.

**Returns**: True if mcp.json exists and contains a `thegent` entry under
`mcpServers`; False otherwise.

---

#### JetBrainsIntegration.read_existing_config

```python
read_existing_config(self: Any, config: JetBrainsConfig)
```

Read and parse an existing mcp.json for the given IDE.

**Parameters**:

- `config`: JetBrainsConfig whose `mcp_config_path` will be read.

**Returns**: Parsed JSON as a dict, or `None` if the file does not exist or
cannot be parsed.

---

#### JetBrainsIntegration.setup_all

```python
setup_all(self: Any)
```

Detect all JetBrains IDEs and write MCP config for each.

Convenience method that combines :meth:`detect_installed_ides` and

---

#### JetBrainsIntegration.write_mcp_config

```python
write_mcp_config(self: Any, config: JetBrainsConfig)
```

Write (or merge) the thegent MCP server entry into the IDE mcp.json.

If mcp.json already exists, the existing `mcpServers` entries are
preserved and the `thegent` entry is added / updated. Other entries
are left untouched.

**Parameters**:

- `config`: JetBrainsConfig describing the target IDE installation.

**Returns**: Path to the written mcp.json file.

---

---

## detect_installed_ides

```python
detect_installed_ides(self: Any)
```

Return a list of JetBrainsConfig for every installed JetBrains IDE.

The method scans the platform-appropriate JetBrains config base
directory (e.g. ~/Library/Application Support/JetBrains on macOS) for
sub-directories whose names match known IDE patterns.

**Returns**: List of JetBrainsConfig instances, one per detected IDE installation.
Returns an empty list when no JetBrains IDEs are found.

---

## is_mcp_plugin_installed

```python
is_mcp_plugin_installed(self: Any, config: JetBrainsConfig)
```

Check whether the thegent MCP plugin entry exists in the IDE config.

**Parameters**:

- `config`: JetBrainsConfig for the IDE to inspect.

**Returns**: True if mcp.json exists and contains a `thegent` entry under
`mcpServers`; False otherwise.

---

## mcp_config_path

```python
mcp_config_path(self: Any)
```

Absolute path to the mcp.json configuration file.

---

## read_existing_config

```python
read_existing_config(self: Any, config: JetBrainsConfig)
```

Read and parse an existing mcp.json for the given IDE.

**Parameters**:

- `config`: JetBrainsConfig whose `mcp_config_path` will be read.

**Returns**: Parsed JSON as a dict, or `None` if the file does not exist or
cannot be parsed.

---

## setup_all

```python
setup_all(self: Any)
```

Detect all JetBrains IDEs and write MCP config for each.

Convenience method that combines :meth:`detect_installed_ides` and

---

## write_mcp_config

```python
write_mcp_config(self: Any, config: JetBrainsConfig)
```

Write (or merge) the thegent MCP server entry into the IDE mcp.json.

If mcp.json already exists, the existing `mcpServers` entries are
preserved and the `thegent` entry is added / updated. Other entries
are left untouched.

**Parameters**:

- `config`: JetBrainsConfig describing the target IDE installation.

**Returns**: Path to the written mcp.json file.

**Raises**:

- `OSError`: If the config directory cannot be created or written.

---
