# AgentAPI Project Documentation

**Project:** AgentAPI - API Framework for Agent Services  
**Main Directory:** `/agentapi`  
**Status:** Active Development

## Overview

AgentAPI provides a comprehensive API framework for building and exposing agent services. Features include:

- **REST API** - RESTful endpoints for agent operations
- **Agent management** - CRUD operations for agents
- **Service integration** - Integration with agent frameworks
- **Authentication** - API authentication and authorization
- **Documentation** - Auto-generated API documentation

## Project Structure

```
agentapi/
├── src/              # Source code
├── tests/            # Test suite
├── examples/         # Example implementations
└── scripts/          # Utilities
```

## Quick Start

### Setup

```bash
cd agentapi
# Check pyproject.toml or setup.py for dependencies
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Running Tests

```bash
pytest tests/
```

### Starting the Server

```bash
# Check examples/ or src/ for startup scripts
python -m agentapi.server
```

## Common Tasks

- **Create an API endpoint** - See source code structure
- **Integrate with agents** - Follow patterns in `examples/`
- **Add authentication** - See auth implementation in `src/`
- **Deploy to production** - See deployment guides

## API Documentation

API documentation is available through:

- Interactive API documentation (when server is running) - Check `http://localhost:8000/docs`
- Source code comments and docstrings
- Example files in `examples/` directory

## Related Projects

- **thegent** - Agent framework
- **atoms-mcp-prod** - MCP tools and integrations
- **pheno-sdk** - SDK for development

---

**Last Updated:** 2026-02-20  
**Note:** This project is being documented. For detailed API information, see generated documentation when running the server.
