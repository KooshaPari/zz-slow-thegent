# Pheno SDK Documentation

**Project:** Pheno SDK - Comprehensive SDK for Agent Development  
**Main Directory:** `/pheno-sdk`  
**Status:** Active Development

## Quick Links

- **[Architecture](../../pheno-sdk/docs/architecture/)** - System design and components
- **[API Reference](../../pheno-sdk/docs/api/)** - Module and function documentation
- **[Getting Started](../../pheno-sdk/docs/)** - Setup and quickstart
- **[CLI Guide](../../pheno-sdk/docs/cli/)** - Command-line tool reference
- **[Authentication](../../pheno-sdk/docs/auth/)** - Auth system guide

## Overview

Pheno SDK provides a complete toolkit for building and managing AI agents. Features include:

- **Agent framework** - Complete lifecycle management
- **CLI tools** - Command-line interface with modern frameworks
- **Authentication** - Secure token and API key management
- **API client** - Full API integration
- **DevOps utilities** - Deployment and monitoring
- **Migration support** - Upgrade paths and compatibility

## Project Structure

```
pheno-sdk/
├── docs/              # Comprehensive documentation
│   ├── architecture/  # System design
│   ├── api/          # API reference
│   ├── api-reference/ # Detailed API docs
│   ├── cli/          # CLI tool guide
│   ├── auth/         # Authentication
│   ├── migration/    # Migration guides
│   ├── audits/       # Audit reports
│   └── guides/       # How-to guides
├── src/              # Source code
├── examples/         # Example implementations
├── tools/            # Utilities and tools
└── scripts/          # Setup and deployment scripts
```

## Key Features

### 1. Agent Framework

- Agent creation and configuration
- Lifecycle management
- State persistence
- See: `docs/architecture/`

### 2. CLI Framework

- Modern CLI with Typer
- Legacy Click support
- Command structure
- See: `docs/cli/` and migration guides

### 3. Authentication System

- API key management
- Token handling
- Secure storage
- See: `docs/auth/`

### 4. Migration Paths

- CLI framework migrations (Click → Typer)
- Legacy compatibility
- Upgrade procedures
- See: `docs/migration/` and `docs/guides/`

## Development

### Setup

```bash
cd pheno-sdk
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
pytest tests/ -v --cov=src/
```

### Building Documentation

```bash
cd docs
make html
```

## Common Tasks

- **Create a new agent** - See agent framework documentation
- **Build a CLI tool** - See CLI guide
- **Implement authentication** - See auth documentation
- **Migrate from Click to Typer** - See migration guides
- **Deploy an agent** - See DevOps documentation

## Dependencies

- Python 3.9+
- See `pyproject.toml` for package dependencies
- Optional: Typer (modern CLI), Click (legacy CLI support)

## Related Projects

- **thegent** - Agent framework (Rust)
- **atoms-mcp-prod** - MCP tools and integrations
- **zen-mcp-server** - MCP server implementation

---

**Last Updated:** 2026-02-20  
**See:** Full documentation in `pheno-sdk/docs/`
