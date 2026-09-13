<DONE>
# Cross-Project Integration Guide — Kush Ecosystem

> **Status**: 🔗 **INTEGRATION GUIDE** | **Date**: 2026-02-18
> **Purpose**: Comprehensive guide for integrating projects across the kush ecosystem

---

## Executive Summary

This guide provides step-by-step instructions for integrating projects across the kush ecosystem. It covers common integration patterns, code examples, best practices, and troubleshooting.

**Target Audience**:

- Developers integrating multiple kush projects
- Architects designing cross-project solutions
- DevOps engineers setting up integrated deployments

---

## Part 1: Integration Patterns

### 1.1 Agent Orchestration Integration

**Pattern**: Integrate multiple agent orchestration systems

**Use Case**: Use thegent as primary orchestrator with plangent sub-agents

```python
# Integration: thegent + plangent
from thegent import AgentOrchestrator
from plangent import RootAgent, SubAgent

# Initialize thegent orchestrator
orchestrator = AgentOrchestrator()

# Register plangent root agent
root_agent = RootAgent(config={"adapter": "plangent", "sub_agents": ["code-review", "testing", "documentation"]})

orchestrator.register_agent("plangent-root", root_agent)

# Use in thegent workflow
result = await orchestrator.execute_task(agent_id="plangent-root", task="Review code and write tests")
```

---

### 1.2 MCP Server Integration

**Pattern**: Use multiple MCP servers together

**Use Case**: Combine atoms-mcp-prod and morph for workspace + research

```python
# Integration: atoms-mcp-prod + morph
from fastmcp import FastMCP
from atoms_mcp import AtomsMCPServer
from morph import MorphServer

# Create unified MCP server
mcp = FastMCP("unified-server")

# Register atoms-mcp-prod tools
atoms_server = AtomsMCPServer()
mcp.register_tools(atoms_server.get_tools())

# Register morph tools
morph_server = MorphServer()
mcp.register_tools(morph_server.get_tools())

# Use unified server
result = await mcp.call_tool("workspace_status", path="/workspace")
research = await mcp.call_tool("web_search", query="Python best practices")
```

---

### 1.3 CLI Tool Integration

**Pattern**: Compose CLI tools for unified workflow

**Use Case**: Use bloc + trace + usage for code analysis workflow

```python
# Integration: bloc + trace + usage
import subprocess
from pathlib import Path


def analyze_project(project_path: Path):
    """Analyze project using multiple CLI tools."""

    # 1. Code analysis with bloc
    bloc_result = subprocess.run(["bloc", str(project_path), "--health"], capture_output=True, text=True)

    # 2. Requirements traceability with trace
    trace_result = subprocess.run(["trace", "analyze", str(project_path)], capture_output=True, text=True)

    # 3. Usage tracking with usage
    usage_result = subprocess.run(["usage", "status", "--project", str(project_path)], capture_output=True, text=True)

    return {"code_analysis": bloc_result.stdout, "requirements": trace_result.stdout, "usage": usage_result.stdout}
```

---

### 1.4 SDK Integration

**Pattern**: Use pheno-sdk across multiple projects

**Use Case**: Share infrastructure code via pheno-sdk

```python
# Integration: pheno-sdk in multiple projects
from pheno_sdk import InfrastructureSDK

# In bloc project
from pheno_sdk.plugins import HealthCheckPlugin


class BlocHealthCheck(HealthCheckPlugin):
    def check(self, path: Path) -> HealthResult:
        # Implementation
        pass


# In crun project
from pheno_sdk.design_patterns import DependencyInjector


class CrunContainer(DependencyInjector):
    def configure(self):
        # Configuration
        pass
```

---

## Part 2: Common Integration Scenarios

### 2.1 Scenario: Multi-Agent Code Review

**Goal**: Use kimaki voice interface to trigger thegent orchestration with plangent agents

```python
# Integration: kimaki + thegent + plangent
from kimaki import VoiceInterface
from thegent import AgentOrchestrator
from plangent import RootAgent

# Setup voice interface
voice = VoiceInterface()

# Setup orchestrator
orchestrator = AgentOrchestrator()
orchestrator.register_agent("plangent", RootAgent())


# Voice command handler
@voice.command("review code")
async def review_code_handler():
    # Trigger orchestration
    result = await orchestrator.execute_task(
        agent_id="plangent", task="Review code in current workspace", sub_agents=["code-review", "testing"]
    )

    # Voice response
    await voice.speak(f"Code review complete: {result.summary}")
```

---

### 2.2 Scenario: Unified Project Management

**Goal**: Use trace for requirements + atoms-mcp-prod for entities + jobhunter for tasks

```python
# Integration: trace + atoms-mcp-prod + jobhunter
from trace import RequirementsManager
from atoms_mcp import EntityManager
from jobhunter import TaskManager


class UnifiedProjectManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.requirements = RequirementsManager(project_id)
        self.entities = EntityManager(project_id)
        self.tasks = TaskManager(project_id)

    async def create_feature(self, feature_spec: dict):
        # 1. Create requirement
        req = await self.requirements.create(feature_spec)

        # 2. Create entity
        entity = await self.entities.create({"type": "feature", "requirement_id": req.id, **feature_spec})

        # 3. Create tasks
        tasks = await self.tasks.create_from_requirement(req.id)

        return {"requirement": req, "entity": entity, "tasks": tasks}
```

---

### 2.3 Scenario: AI Usage Tracking Across Projects

**Goal**: Track AI usage from multiple projects using usage tool

```python
# Integration: usage tracking across projects
from usage import UsageTracker


class CrossProjectUsageTracker:
    def __init__(self):
        self.tracker = UsageTracker()

    async def track_thegent_usage(self, session_id: str):
        """Track thegent usage."""
        await self.tracker.track(provider="thegent", session_id=session_id, project="thegent")

    async def track_plangent_usage(self, task_id: str):
        """Track plangent usage."""
        await self.tracker.track(provider="plangent", session_id=task_id, project="plangent")

    async def get_cross_project_summary(self):
        """Get usage summary across all projects."""
        return await self.tracker.summary(group_by="project", period="monthly")
```

---

## Part 3: Integration Architecture

### 3.1 Integration Hub Pattern

```python
# Unified Integration Hub
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class IntegrationHub:
    """Central hub for cross-project integration."""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.mcp_servers: Dict[str, Any] = {}
        self.cli_tools: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}

    def register_agent(self, name: str, agent: Any):
        """Register an agent."""
        self.agents[name] = agent

    def register_mcp_server(self, name: str, server: Any):
        """Register an MCP server."""
        self.mcp_servers[name] = server

    def register_cli_tool(self, name: str, tool: Any):
        """Register a CLI tool."""
        self.cli_tools[name] = tool

    async def execute_cross_project_task(self, task: dict):
        """Execute task across multiple projects."""
        # 1. Route to appropriate agent
        agent = self._select_agent(task)

        # 2. Get required tools
        tools = self._get_tools(task)

        # 3. Execute with tools
        result = await agent.execute(task, tools)

        # 4. Track usage
        await self._track_usage(task, result)

        return result

    def _select_agent(self, task: dict) -> Any:
        """Select best agent for task."""
        # Implementation
        pass

    def _get_tools(self, task: dict) -> list:
        """Get required tools for task."""
        # Implementation
        pass

    async def _track_usage(self, task: dict, result: Any):
        """Track usage across projects."""
        # Implementation
        pass
```

---

### 3.2 Service Mesh Pattern

```python
# Service Mesh for Cross-Project Communication
from typing import Protocol


class ServiceProtocol(Protocol):
    """Protocol for services in the mesh."""

    async def call(self, method: str, **kwargs) -> Any:
        """Call a service method."""
        ...

    async def health_check(self) -> bool:
        """Check service health."""
        ...


class ServiceMesh:
    """Service mesh for cross-project communication."""

    def __init__(self):
        self.services: Dict[str, ServiceProtocol] = {}

    def register_service(self, name: str, service: ServiceProtocol):
        """Register a service."""
        self.services[name] = service

    async def call_service(self, service_name: str, method: str, **kwargs):
        """Call a service method."""
        if service_name not in self.services:
            raise ValueError(f"Service not found: {service_name}")

        service = self.services[service_name]
        return await service.call(method, **kwargs)

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services."""
        results = {}
        for name, service in self.services.items():
            results[name] = await service.health_check()
        return results
```

---

## Part 4: Code Examples

### 4.1 Example: Complete Integration

```python
# Complete integration example
from thegent import AgentOrchestrator
from atoms_mcp import AtomsMCPServer
from morph import MorphServer
from usage import UsageTracker
from trace import RequirementsManager


class IntegratedWorkflow:
    """Complete integrated workflow."""

    def __init__(self):
        # Initialize components
        self.orchestrator = AgentOrchestrator()
        self.atoms_mcp = AtomsMCPServer()
        self.morph_mcp = MorphServer()
        self.usage_tracker = UsageTracker()
        self.requirements = RequirementsManager()

    async def execute_feature_request(self, request: dict):
        """Execute a complete feature request workflow."""

        # 1. Create requirement
        req = await self.requirements.create(request)

        # 2. Research using morph
        research = await self.morph_mcp.call_tool("web_search", query=request["description"])

        # 3. Create entity in atoms-mcp-prod
        entity = await self.atoms_mcp.call_tool("create_entity", type="feature", data={**request, "research": research})

        # 4. Execute with thegent
        result = await self.orchestrator.execute_task(
            agent_id="feature-agent",
            task=f"Implement: {request['title']}",
            context={"requirement": req, "entity": entity, "research": research},
        )

        # 5. Track usage
        await self.usage_tracker.track(provider="thegent", project="feature-implementation", tokens=result.tokens_used)

        return {"requirement": req, "entity": entity, "result": result}
```

---

### 4.2 Example: CLI Tool Composition

```python
# CLI tool composition
import asyncio
from pathlib import Path


async def comprehensive_analysis(project_path: Path):
    """Comprehensive project analysis using multiple tools."""

    results = {}

    # Parallel execution
    tasks = [run_bloc(project_path), run_trace(project_path), run_usage_status(project_path)]

    bloc_result, trace_result, usage_result = await asyncio.gather(*tasks)

    return {"code_analysis": bloc_result, "requirements": trace_result, "usage": usage_result}


async def run_bloc(path: Path):
    """Run bloc analysis."""
    proc = await asyncio.create_subprocess_exec("bloc", str(path), "--health", stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode()


async def run_trace(path: Path):
    """Run trace analysis."""
    proc = await asyncio.create_subprocess_exec("trace", "analyze", str(path), stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode()


async def run_usage_status(path: Path):
    """Run usage status."""
    proc = await asyncio.create_subprocess_exec(
        "usage", "status", "--project", str(path), stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()
```

---

## Part 5: Configuration Management

### 5.1 Unified Configuration

```python
# Unified configuration for cross-project integration
from pydantic_settings import BaseSettings
from typing import Dict, Any


class UnifiedConfig(BaseSettings):
    """Unified configuration for kush ecosystem."""

    # Agent orchestration
    thegent_api_url: str = "http://localhost:8000"
    plangent_config: Dict[str, Any] = {}
    kimaki_config: Dict[str, Any] = {}

    # MCP servers
    atoms_mcp_url: str = "http://localhost:8001"
    morph_mcp_url: str = "http://localhost:8002"

    # CLI tools
    bloc_path: str = "bloc"
    trace_path: str = "trace"
    usage_path: str = "usage"

    # Infrastructure
    pheno_sdk_config: Dict[str, Any] = {}

    # Storage
    database_url: str = "postgresql://localhost/kush"
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_prefix = "KUSH_"
```

---

### 5.2 Environment Variables

```bash
# .env file for cross-project integration
KUSH_THEGENT_API_URL=http://localhost:8000
KUSH_PLANGENT_CONFIG={"adapter": "plangent"}
KUSH_ATOMS_MCP_URL=http://localhost:8001
KUSH_MORPH_MCP_URL=http://localhost:8002
KUSH_DATABASE_URL=postgresql://localhost/kush
KUSH_REDIS_URL=redis://localhost:6379
```

---

## Part 6: Error Handling

### 6.1 Cross-Project Error Handling

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Base exception for integration errors."""

    pass


class AgentNotFoundError(IntegrationError):
    """Agent not found error."""

    pass


class MCPServerError(IntegrationError):
    """MCP server error."""

    pass


async def safe_integration_call(func, *args, **kwargs):
    """Safely call integration function with error handling."""
    try:
        return await func(*args, **kwargs)
    except AgentNotFoundError as e:
        logger.error(f"Agent not found: {e}")
        # Fallback logic
        return None
    except MCPServerError as e:
        logger.error(f"MCP server error: {e}")
        # Retry logic
        return await retry_call(func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise IntegrationError(f"Integration failed: {e}") from e
```

---

## Part 7: Testing Integration

### 7.1 Integration Tests

```python
import pytest
from integrated_workflow import IntegratedWorkflow


@pytest.mark.asyncio
async def test_integrated_workflow():
    """Test integrated workflow."""
    workflow = IntegratedWorkflow()

    request = {"title": "Test Feature", "description": "Test description"}

    result = await workflow.execute_feature_request(request)

    assert result["requirement"] is not None
    assert result["entity"] is not None
    assert result["result"] is not None
```

---

## Part 8: Deployment

### 8.1 Docker Compose Integration

```yaml
# docker-compose.yml for integrated deployment
version: "3.8"

services:
  thegent:
    build: ./thegent
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/kush
      - REDIS_URL=redis://redis:6379

  atoms-mcp:
    build: ./atoms-mcp-prod
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/kush

  morph:
    build: ./morph
    ports:
      - "8002:8002"

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=kush
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7
```

---

## Part 9: Monitoring Integration

### 9.1 Unified Monitoring

```python
# Unified monitoring across projects
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("cross_project_operation")
async def monitored_integration():
    """Integration with monitoring."""
    with tracer.start_as_current_span("thegent_call"):
        # Call thegent
        pass

    with tracer.start_as_current_span("mcp_call"):
        # Call MCP server
        pass
```

---

## Part 10: Best Practices

### 10.1 Integration Best Practices

1. **Use Unified APIs**: Prefer unified APIs (agent registry, MCP tools) over direct integration
2. **Error Handling**: Always handle errors gracefully with fallbacks
3. **Monitoring**: Add monitoring and logging to all integration points
4. **Testing**: Write integration tests for cross-project workflows
5. **Documentation**: Document integration patterns and examples
6. **Configuration**: Use unified configuration management
7. **Versioning**: Pin versions for stability
8. **Security**: Validate inputs and sanitize outputs

---

## Part 11: Troubleshooting

### 11.1 Common Issues

**Issue**: Agent not found

- **Solution**: Check agent registry, verify agent registration

**Issue**: MCP server connection failed

- **Solution**: Check server URL, verify server is running

**Issue**: Configuration mismatch

- **Solution**: Verify environment variables, check config files

**Issue**: Performance degradation

- **Solution**: Add caching, optimize queries, use async operations

---

## See Also

- [KUSH_ECOSYSTEM_DEEP_DIVE.md](./KUSH_ECOSYSTEM_DEEP_DIVE.md) - Ecosystem analysis
- [UNIFIED_AGENT_REGISTRY_API.md](./UNIFIED_AGENT_REGISTRY_API.md) - Agent registry API
- [SHARED_MCP_TOOL_LIBRARY.md](./SHARED_MCP_TOOL_LIBRARY.md) - Shared MCP tools
- [KUSH_ECOSYSTEM_ARCHITECTURE_DIAGRAM.md](./KUSH_ECOSYSTEM_ARCHITECTURE_DIAGRAM.md) - Architecture diagrams

---

**Status**: 🔗 **INTEGRATION GUIDE COMPLETE** - Comprehensive cross-project integration guide
