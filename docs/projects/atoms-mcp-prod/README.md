# Atoms MCP Prod Documentation

**Project:** Atoms MCP Prod - Production MCP tools and integrations  
**Main Directory:** `/atoms-mcp-prod`  
**Status:** Active Development

## Quick Links

- **[Architecture](../../atoms-mcp-prod/docs/architecture/)** - System design
- **[API Reference](../../atoms-mcp-prod/docs/api/)** - Tool and endpoint documentation
- **[Getting Started](../../atoms-mcp-prod/docs/02-getting-started/)** - Setup and quickstart
- **[Tool Reference](../../atoms-mcp-prod/docs/03-tool-reference/)** - Tool specifications
- **[Advanced Patterns](../../atoms-mcp-prod/docs/04-advanced-patterns/)** - Advanced usage
- **[Developer Setup](../../atoms-mcp-prod/docs/05-developer-setup/)** - Development environment

## Overview

Atoms MCP Prod provides production-ready MCP (Model Context Protocol) tools and integrations for AI applications. It includes:

- **Tool integrations** - Pre-built tools for common tasks
- **Authentication system** - Secure API key management
- **Live/Mock architecture** - Development and testing modes
- **Agent demonstrations** - Example implementations
- **CLI documentation** - Command-line tool serving

## Project Structure

```
atoms-mcp-prod/
├── docs/              # Complete documentation
│   ├── architecture/  # System design
│   ├── api/          # API reference
│   ├── 01-agent-demonstrations/  # Examples
│   ├── 02-getting-started/      # Setup
│   ├── 03-tool-reference/       # Tools
│   ├── 04-advanced-patterns/    # Advanced usage
│   └── 05-developer-setup/      # Development
├── src/              # Source code
├── tools/            # Tool implementations
└── scripts/          # Utilities
```

## Key Features

### 1. Authentication System

- API key management
- Token handling
- Secure storage
- See: `docs/AUTH_SYSTEM_COMPLETE_GUIDE.md`

### 2. Tool Integration

- Pre-built MCP tools
- Custom tool development
- Tool composition
- See: `docs/03-tool-reference/`

### 3. Agent Demonstrations

- Example agent implementations
- Integration patterns
- Best practices
- See: `docs/01-agent-demonstrations/`

### 4. Live/Mock Architecture

- Live API connections
- Mock implementations for testing
- Hybrid modes
- See: `docs/00_live_mock_architecture.md`

## Development

### Setup

```bash
cd atoms-mcp-prod
# Follow docs/05-developer-setup/
```

### Running Tests

```bash
pytest tests/
```

### Building and Serving

```bash
# See CLI documentation in docs/
```

## Common Tasks

- **Integrate a new tool** - See tool reference documentation
- **Create an authentication flow** - See auth guide
- **Build an agent** - See agent demonstrations
- **Deploy to production** - See developer setup guide

## Dependencies

- Python 3.9+
- See `pyproject.toml` for package dependencies
- MCP protocol support

## Related Projects

- **thegent** - Agent framework
- **zen-mcp-server** - MCP server implementation
- **pheno-sdk** - SDK for development

---

**Last Updated:** 2026-02-20  
**See:** Full documentation in `atoms-mcp-prod/docs/`
