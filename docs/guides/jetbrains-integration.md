# JetBrains IDE Integration

thegent integrates with JetBrains IDEs (IntelliJ IDEA, PyCharm, GoLand, CLion,
WebStorm, and others) by writing a standard `mcp.json` configuration file to
the IDE's configuration directory. The JetBrains AI plugin reads this file and
connects to the thegent MCP server automatically.

## Quick Start

```bash
# Detect installed IDEs and write mcp.json for each one
thegent jetbrains setup

# Dry-run: show what would be written without touching any files
thegent jetbrains setup --dry-run

# Point to a non-default MCP server URL
thegent jetbrains setup --mcp-url http://localhost:9000/mcp

# Scope Serena semantic tools to a specific project root
thegent jetbrains setup --project-root /Users/me/dev/myproject
```

## How It Works

### Config File Location

thegent writes to `~/.config/JetBrains/<IDE>/mcp.json` (macOS / Linux).
On macOS, the actual path is usually under
`~/Library/Application Support/JetBrains/<IDE>/<version>/mcp.json`.

| Platform | Base Directory                             |
| -------- | ------------------------------------------ |
| macOS    | `~/Library/Application Support/JetBrains/` |
| Linux    | `~/.config/JetBrains/` (XDG_CONFIG_HOME)   |
| Windows  | `%APPDATA%\JetBrains\`                     |

### Config File Format

```json
{
  "mcpServers": {
    "thegent": {
      "url": "http://localhost:3847/mcp"
    }
  }
}
```

When `--project-root` is set, an `env` block is added:

```json
{
  "mcpServers": {
    "thegent": {
      "url": "http://localhost:3847/mcp",
      "env": {
        "SERENA_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

Existing `mcpServers` entries from other tools are preserved.

## Supported IDEs

| IDE           | Config Dir Prefix        |
| ------------- | ------------------------ |
| IntelliJ IDEA | `IntelliJIdea`, `IdeaIC` |
| PyCharm       | `PyCharm`, `PyCharmCE`   |
| GoLand        | `GoLand`                 |
| CLion         | `CLion`                  |
| WebStorm      | `WebStorm`               |
| Rider         | `Rider`                  |
| DataGrip      | `DataGrip`               |
| RubyMine      | `RubyMine`               |
| PhpStorm      | `PhpStorm`               |
| Fleet         | `Fleet`                  |

## Starting the MCP Server

The JetBrains plugin connects to `http://localhost:3847/mcp` by default.
Start the thegent MCP server before opening your IDE:

```bash
thegent mcp serve
```

Or set a custom port:

```bash
thegent mcp serve --port 9000
thegent jetbrains setup --mcp-url http://localhost:9000/mcp
```

## Serena Integration

[Serena](https://github.com/oraios/serena) provides semantic code tools
(symbol search, references, definitions) via MCP. thegent mounts Serena
under the `serena` namespace.

### Backend Auto-Detection

thegent auto-detects whether the Serena JetBrains plugin is running:

```bash
# Show active Serena backend
thegent lsp serena-backend
```

If the plugin's MCP server is reachable on the configured port (default 8765),
thegent uses the JetBrains backend. Otherwise it falls back to the LSP backend
(`uvx serena start-mcp-server`).

### Configure the JetBrains Plugin Port

```bash
# In .env or environment
THGENT_SERENA_JETBRAINS_PORT=8765
```

### Serena Plugin Setup (JetBrains)

1. Open IntelliJ IDEA (or any JetBrains IDE).
2. Go to **Settings > Plugins**.
3. Search for **Serena** and install it.
4. Restart the IDE. The plugin starts an MCP server on port 8765 automatically.
5. Verify: `thegent lsp serena-backend` should print `jetbrains`.

## Python API

```python
from thegent.integrations.jetbrains import JetBrainsIntegration

integration = JetBrainsIntegration(
    mcp_server_url="http://localhost:3847/mcp",
    serena_project_root="/path/to/project",  # optional
)

# Detect all installed IDEs
configs = integration.detect_installed_ides()
for cfg in configs:
    print(cfg.ide_type, cfg.config_dir)

# Write mcp.json for a specific IDE
path = integration.write_mcp_config(configs[0])
print(f"Wrote {path}")

# Write for all detected IDEs at once
results = integration.setup_all()
for r in results:
    print(r["ide_type"], "success=" + str(r["success"]))

# Check whether thegent is already configured for an IDE
installed = integration.is_mcp_plugin_installed(configs[0])
```

## Troubleshooting

**No IDEs detected**

- Ensure at least one JetBrains IDE is installed.
- On macOS check: `~/Library/Application Support/JetBrains/`
- On Linux check: `~/.config/JetBrains/`

**Plugin does not connect**

- Confirm thegent MCP server is running: `thegent mcp serve`
- Verify the URL in `mcp.json` matches the running server.
- Check IDE plugin logs in **Help > Show Log in Finder/Explorer**.

**Backend stays on LSP even with plugin installed**

- Check the plugin port setting matches `THGENT_SERENA_JETBRAINS_PORT`.
- Ensure the IDE is running (the plugin only starts its MCP server when the
  IDE is open).

## See Also

- `thegent lsp serena-backend` — show active Serena backend
- `thegent lsp serena-jetbrains-setup` — guided Serena plugin setup
- `thegent lsp auto-setup` — setup all IDE integrations at once
- [Serena plugin page](https://plugins.jetbrains.com/plugin/28946/serena)
