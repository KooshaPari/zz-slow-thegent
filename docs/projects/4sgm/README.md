# 4SGM Project Documentation

**Project:** 4SGM - LangFuse Integration and Monitoring  
**Main Directory:** `/4sgm`  
**Status:** Active Development

## Quick Links

- **[Architecture](../../4sgm/docs/architecture/)** - System design
- **[API Reference](../../4sgm/docs/api/)** - API documentation
- **[LangFuse Setup](../../4sgm/docs/LANGFUSE_SETUP.md)** - Configuration guide
- **[LangFuse Reference](../../4sgm/docs/LANGFUSE_QUICK_REFERENCE.md)** - Quick reference

## Overview

4SGM provides LangFuse integration and monitoring capabilities for AI applications. Features include:

- **LangFuse integration** - Complete integration with LangFuse platform
- **Agent monitoring** - Performance tracking and analytics
- **Trace management** - Request tracing and debugging
- **Cost tracking** - Token and API cost monitoring
- **Quality metrics** - Quality score and evaluation

## Project Structure

```
4sgm/
├── docs/              # Documentation
│   ├── architecture/  # System design
│   ├── api/          # API reference
│   ├── plans/        # Implementation plans
│   └── *.md          # Guides and references
├── src/              # Source code
├── examples/         # Example implementations
└── scripts/          # Utilities
```

## Key Features

### 1. LangFuse Integration

- Agent tracing
- Span management
- Context propagation
- See: `docs/LANGFUSE_SETUP.md`

### 2. Monitoring

- Performance metrics
- Token counting
- Cost analysis
- See: `docs/architecture/`

### 3. Quality Tracking

- Quality scores
- Evaluation results
- Analytics
- See: `docs/INDEX_LANGFUSE.md`

## Development

### Setup

```bash
cd 4sgm
# Follow docs/LANGFUSE_SETUP.md
```

### Running Tests

```bash
pytest tests/
```

## Common Tasks

- **Set up LangFuse** - See setup guide
- **Add tracing to agent** - See integration documentation
- **Monitor performance** - See monitoring guide
- **Analyze costs** - See analytics documentation

## Dependencies

- See `pyproject.toml` or `requirements.txt`
- LangFuse SDK
- Related project integrations

## Related Projects

- **thegent** - Agent framework
- **atoms-mcp-prod** - MCP tools
- **zen-mcp-server** - MCP server

---

**Last Updated:** 2026-02-20  
**See:** Full documentation in `4sgm/docs/`
