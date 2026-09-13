# Zen MCP Server Documentation

**Project:** Zen MCP Server - Model Context Protocol Server Implementation  
**Main Directory:** `/zen-mcp-server`  
**Status:** Active Development

## Quick Links

- **[Architecture](../../zen-mcp-server/docs/architecture/)** - System design and components
- **[API Reference](../../zen-mcp-server/docs/api/)** - MCP API documentation
- **[Getting Started](../../zen-mcp-server/docs/)** - Setup and quickstart
- **[Guides](../../zen-mcp-server/docs/)** - How-to guides

## Overview

Zen MCP Server is a comprehensive Model Context Protocol server implementation. It provides:

- **Protocol compliance** - Full MCP specification support
- **Tool management** - Tool registration and execution
- **Resource handling** - File and resource access
- **Context management** - Message and state handling
- **Performance optimization** - Caching and indexing

## Project Structure

```
zen-mcp-server/
├── docs/              # Comprehensive documentation
│   ├── architecture/  # System design
│   ├── api/          # API reference
│   ├── adr/          # Architecture decision records
│   └── guides/       # How-to guides
├── src/              # Source code
├── examples/         # Example implementations
├── scripts/          # Utilities and scripts
└── tests/            # Test suite
```

## Key Components

### 1. Protocol Implementation

- MCP protocol compliance
- Request/response handling
- Session management
- See: `docs/architecture/`

### 2. Tool System

- Tool registration
- Tool discovery
- Execution engine
- See: `docs/api/` and examples

### 3. Resource Handler

- File access patterns
- Resource management
- Access control
- See: `docs/guides/`

### 4. Migration Support

- Tool migrations
- FastMCP compatibility
- Schema upgrades
- See: `docs/fastmcp/migration-guide.md`

## Development

### Setup

```bash
cd zen-mcp-server
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
pytest tests/ -v  # Verbose
```

### Building Documentation

```bash
cd docs
make html  # Build HTML docs
```

## Common Tasks

- **Add a new tool** - See tool system documentation
- **Handle a new resource type** - See resource handler docs
- **Migrate from FastMCP** - See migration guide
- **Debug protocol issues** - See architecture documentation

## Dependencies

- Python 3.9+
- See `pyproject.toml` for package dependencies
- MCP protocol library

## Related Projects

- **thegent** - Agent framework
- **atoms-mcp-prod** - MCP tools and integrations
- **pheno-sdk** - SDK for development

---

**Last Updated:** 2026-02-20  
**See:** Full documentation in `zen-mcp-server/docs/`
