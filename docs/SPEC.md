# Technical Specification

Technical architecture and design documents for **thegent**.

---

## Core Architecture

The primary architectural documentation is:

- **[ARCHITECTURE_LAYERS.md](./ARCHITECTURE_LAYERS.md)** - System architecture overview
- **[concepts/](./concepts/)** - Core concepts and design patterns

---

## API Specifications

| API          | Documentation                                |
| ------------ | -------------------------------------------- |
| REST API     | [api/rest-api.md](./api/rest-api.md)         |
| MCP Protocol | [api/mcp-protocol.md](./api/mcp-protocol.md) |
| CLI          | [reference/cli/](./reference/cli/)           |

---

## Component Specifications

### Routing

- [routing/provider_types.py](https://github.com/KooshaPari/temp-PRODVERCEL/485/kush/thegent/blob/main/src/thegent/routing/provider_types.py) - Provider type definitions
- [routing/harness_model_mapping.py](https://github.com/KooshaPari/temp-PRODVERCEL/485/kush/thegent/blob/main/src/thegent/routing/harness_model_mapping.py) - Model mappings

### Quality Gates

- [governance/quality_matrix.py](https://github.com/KooshaPari/temp-PRODVERCEL/485/kush/thegent/blob/main/src/thegent/governance/quality_matrix.py) - Quality validation
- [hooks/](https://github.com/KooshaPari/temp-PRODVERCEL/485/kush/thegent/tree/main/hooks/) - Hook scripts

### MCP Server

- [MCP Server Implementation](./guides/fastmcp-deployment.md)
- [Provider Operations](./guides/provider-operations.md)

---

## Data Models

| Model    | Location                 |
| -------- | ------------------------ |
| Agent    | `src/thegent/agents/`    |
| Provider | `src/thegent/providers/` |
| Hook     | `src/thegent/hooks/`     |
| Quality  | `src/thegent/quality/`   |

---

## Configuration

| Config    | File                    |
| --------- | ----------------------- |
| Main      | `config/thegent.yaml`   |
| Providers | `config/providers/`     |
| Hooks     | `.claude/settings.json` |

---

_Last updated: 2026-02-23_
