# Project Dependencies

**Project**: thegent  
**Classification**: Tier 2 - Platform Infrastructure  
**Last Updated**: 2026-04-02

## Overview

Unified agent orchestration CLI for Factory skills, droids, and multi-agent workflows.

## Direct Dependencies (Workspace)

| Path         | Purpose            |
| ------------ | ------------------ |
| `packages/*` | Workspace packages |
| `modules/*`  | Workspace modules  |

## External Dependencies (Production)

| Package           | Version  | Purpose            |
| ----------------- | -------- | ------------------ |
| httpx             | >=0.28.1 | HTTP client        |
| typer             | >=0.16.0 | CLI framework      |
| rich              | >=13.9.4 | Terminal output    |
| pydantic          | >=2.12.5 | Data validation    |
| pydantic-settings | >=2.8.1  | Configuration      |
| fastmcp           | >=3.0.0  | MCP protocol       |
| starlette         | >=0.46.0 | ASGI framework     |
| uvicorn           | >=0.34.0 | ASGI server        |
| granian           | >=1.7.4  | Rust HTTP server   |
| opentelemetry-api | >=1.31.0 | Observability      |
| opentelemetry-sdk | >=1.31.0 | Telemetry          |
| structlog         | >=24.0.0 | Structured logging |
| tenacity          | >=9.0.0  | Retry logic        |
| cachetools        | >=5.5.2  | Caching            |
| diskcache         | >=5.6.3  | Disk cache         |
| watchdog          | >=6.0.0  | File watching      |
| watchfiles        | >=1.0.4  | File watching      |
| apscheduler       | >=3.10.4 | Job scheduling     |
| playwright        | >=1.50.0 | Browser automation |
| textual           | >=1.0.0  | TUI framework      |
| Pillow            | >=10.0.0 | Image processing   |
| psutil            | >=7.0.0  | System monitoring  |

## Development Dependencies

| Package          | Version   | Purpose           |
| ---------------- | --------- | ----------------- |
| pytest           | >=9.0.2   | Testing framework |
| pytest-asyncio   | >=1.3.0   | Async testing     |
| pytest-cov       | >=6.0.0   | Coverage          |
| pytest-xdist     | >=3.6.1   | Parallel testing  |
| pytest-benchmark | >=4.0.0   | Benchmarks        |
| mypy             | >=1.19.1  | Type checking     |
| basedpyright     | >=1.31.1  | Type checking     |
| ruff             | >=0.15.1  | Linting           |
| pre-commit       | >=4.1.0   | Git hooks         |
| tach             | >=0.26.0  | Import checking   |
| hypothesis       | >=6.140.0 | Property testing  |
| litellm          | ==1.82.5  | LLM testing       |

## Platform Integrations

| Platform  | Integration                   |
| --------- | ----------------------------- |
| AgilePlus | Queue integration via fastmcp |
| Factory   | Skill execution via MCP       |

## Dependency Policy

- **Security patches**: Within 24 hours
- **Minor updates**: Weekly via `uv lock --upgrade`
- **Major updates**: Quarterly with ADR

## Constraints

- Python 3.13+ required
- Uses Rust wrappers for performance-critical paths
- Locked to fastmcp 3.x for MCP protocol compatibility
