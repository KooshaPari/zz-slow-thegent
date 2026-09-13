# Project Documentation Index

**Last Updated:** February 20, 2026  
**Status:** Organized and consolidated

This directory contains documentation for all major projects in the system. Each project has its own README with quick links and overview.

## Project Overview

### Core Projects

#### [TheGent](./thegent/) - Agent Framework

The core agent framework for building AI-powered applications with lifecycle management, hooks, memory systems, and tool integration.

**Key Areas:**

- Agent registry and discovery
- Hook system for event-driven patterns
- Memory management (JSONL/SQLite)
- Runtime execution engine

**Links:** Architecture | API | Getting Started

---

#### [Zen MCP Server](./zen-mcp-server/) - Model Context Protocol Server

Complete MCP server implementation with protocol compliance, tool management, resource handling, and optimization.

**Key Areas:**

- MCP protocol implementation
- Tool registration and execution
- Resource management
- FastMCP migration support

**Links:** Architecture | API | Getting Started

---

#### [Atoms MCP Prod](./atoms-mcp-prod/) - Production MCP Tools

Production-ready MCP tools and integrations with authentication, live/mock architecture, and comprehensive examples.

**Key Areas:**

- Tool integrations
- Authentication system
- Agent demonstrations
- Developer setup

**Links:** Getting Started | Tool Reference | Advanced Patterns

---

#### [Pheno SDK](./pheno-sdk/) - Agent Development SDK

Comprehensive SDK for agent development with modern CLI framework, authentication, and migration support.

**Key Areas:**

- Agent framework
- CLI tools (Typer/Click)
- Authentication system
- Migration guides

**Links:** Getting Started | CLI Guide | Authentication

---

### Supporting Projects

#### [4SGM](./4sgm/) - LangFuse Integration

LangFuse monitoring and integration for agent performance tracking, tracing, and analytics.

**Key Areas:**

- LangFuse integration
- Agent monitoring
- Trace management
- Cost tracking

**Links:** Setup Guide | API | Quick Reference

---

#### [Bloc](./bloc/) - Business Logic & Components

Business logic and component management for application workflows and state handling.

**Key Areas:**

- Component lifecycle
- Business logic patterns
- State management

**Links:** Source Code | Examples

---

#### [AgentAPI](./agentapi/) - Agent API Framework

REST API framework for exposing agent services with authentication and auto-generated documentation.

**Key Areas:**

- REST endpoints
- Agent management
- Service integration
- Authentication

**Links:** API Docs | Examples

---

## Documentation Organization

Each project directory contains:

- **README.md** - Project overview and quick links
- **Linked documentation** - Full documentation in the component's own `/docs` directory
- **Architecture docs** - System design and components
- **API reference** - Function/endpoint documentation
- **Getting started** - Setup and quickstart guides
- **Guides** - How-to and best practices

## Cross-Project References

### Migration Guides

- **[Migration Overview](../guides/migration-overview.md)** - General migration strategies
- **[Legacy Migration](../guides/legacy-migration.md)** - Dependency and code migrations
- **[Data Migration](../guides/data-migration.md)** - Data format and storage migrations

### Architecture & Design

- **[System Architecture](../architecture/)** - Overall system design
- **[Concepts](../concepts/)** - Core concepts and patterns
- **[API Reference](../api/)** - Unified API documentation

### Development

- **[Development Setup](../development/)** - Environment setup
- **[Testing](../reference/)** - Testing strategies
- **[Deployment](../deployment/)** - Deployment guides

## Quick Navigation

### By Task

**Getting started with agents:**

1. Start with [TheGent](./thegent/) for core framework
2. Check [Pheno SDK](./pheno-sdk/) for development tools
3. See [Atoms MCP Prod](./atoms-mcp-prod/) for tool integration

**Building an API:**

1. Use [AgentAPI](./agentapi/) framework
2. Reference [Atoms MCP Prod](./atoms-mcp-prod/) for tools
3. Check [Zen MCP Server](./zen-mcp-server/) for protocol details

**Monitoring and analytics:**

1. Use [4SGM](./4sgm/) for LangFuse integration
2. Check TheGent monitoring capabilities
3. Reference agent metrics documentation

### By Technology

**Rust projects:**

- [TheGent](./thegent/) - Core agent framework

**Python projects:**

- [Zen MCP Server](./zen-mcp-server/)
- [Atoms MCP Prod](./atoms-mcp-prod/)
- [Pheno SDK](./pheno-sdk/)
- [4SGM](./4sgm/)
- [Bloc](./bloc/)
- [AgentAPI](./agentapi/)

---

## Adding New Projects

When adding a new project:

1. Create a directory in `/docs/projects/{project-name}`
2. Add a `README.md` with:
   - Project overview
   - Quick links
   - Key features
   - Development setup
   - Related projects
3. Link to full documentation in the project's own `/docs` directory
4. Update this index

---

## Documentation Status

- **TheGent** ✓ Comprehensive
- **Zen MCP Server** ✓ Comprehensive
- **Atoms MCP Prod** ✓ Comprehensive
- **Pheno SDK** ✓ Comprehensive
- **4SGM** ✓ Complete
- **Bloc** ⚠ Needs documentation
- **AgentAPI** ⚠ Needs documentation

---

## Related Documentation

- **[Root Documentation](../)** - Main docs index
- **[Migration Guides](../guides/)** - All migration guides
- **[API Documentation](../api/)** - Unified API reference
- **[Architecture](../architecture/)** - System architecture

---

**Generated:** 2026-02-20  
**Consolidated from:** 45+ migration files and component documentation across the project
