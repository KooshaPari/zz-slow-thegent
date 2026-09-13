# TheGent Project Documentation

**Project:** TheGent - Agent framework for building AI-powered applications  
**Main Directory:** `/thegent`  
**Status:** Active Development

## Quick Links

- **[Architecture](../../thegent/docs/architecture/)** - System design and components
- **[API Reference](../../thegent/docs/api/)** - Function and module documentation
- **[Getting Started](../../thegent/docs/)** - Development setup and quickstart
- **[Guides](../../thegent/docs/)** - How-to guides and examples

## Overview

TheGent provides a comprehensive framework for building and orchestrating AI agents. Key features include:

- **Agent lifecycle management** - Creation, configuration, execution
- **Hook system** - Event-driven patterns and middleware
- **Memory management** - Agent state persistence and recall
- **Tool integration** - LLM tool binding and execution
- **Architecture flexibility** - Pluggable components

## Project Structure

```
thegent/
├── docs/              # Comprehensive documentation
│   ├── architecture/  # System design
│   ├── api/          # API reference
│   ├── guides/       # How-to guides
│   └── agents/       # Agent specifications
├── crates/           # Rust components
├── hooks/            # Hook dispatcher system
├── tools/            # Tool integration
└── scripts/          # Utilities and scripts
```

## Key Components

### 1. Agent Registry

- Agent configuration and discovery
- Registration and metadata management
- See: `docs/AGENT_REGISTRY_DESIGN.md`

### 2. Hook System

- Event-driven middleware
- Request/response hooks
- Error handling hooks
- See: `docs/architecture/` for detailed design

### 3. Memory System

- JSONL-based memory storage
- Can migrate to SQLite (Phase 6)
- Semantic memory relationships
- See: `docs/guides/PHASE_6_MEMORY_MIGRATION_GUIDE.md`

### 4. Runtime

- Agent execution engine
- Tool binding and invocation
- Error handling and recovery
- See: `crates/thegent-runtime`

## Development

### Setup

```bash
cd thegent
cargo build
cargo test
```

### Running Tests

```bash
cargo test --workspace
cargo test --doc  # Documentation tests
```

### Building Documentation

```bash
cargo doc --open
```

## Common Tasks

- **Add a new agent** - See agent registry documentation
- **Create a hook** - See hook system guides
- **Integrate a tool** - See tool integration documentation
- **Migrate memory storage** - See Phase 6 migration guide

## Dependencies

- **Rust:** See `thegent/crates/*/Cargo.toml`
- **Python:** Agent configurations and scripts
- **External:** LLM APIs, tools, services

## Related Projects

- **zen-mcp-server** - MCP server implementation
- **atoms-mcp-prod** - MCP tools and integrations
- **pheno-sdk** - SDK for agent development

---

**Last Updated:** 2026-02-20  
**See:** Full documentation in `thegent/docs/`
