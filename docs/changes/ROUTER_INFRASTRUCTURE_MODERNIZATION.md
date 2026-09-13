# Change Proposal: router (krouter) Infrastructure Modernization

**Project:** router (krouter)  
**Priority:** HIGH  
**Complexity:** HIGH  
**Estimated Effort:** 50 hours  
**Risk Level:** MEDIUM (Active development, complex ML/AI system)

---

## Current State Analysis

### Strengths

✅ Modern pyproject.toml with good structure  
✅ Uses uv (has uv.lock)  
✅ Uses ruff for linting/formatting  
✅ Has mypy, zuban, pyright for type checking  
✅ Good test infrastructure (pytest, pytest-asyncio)  
✅ Pydantic-settings configured  
✅ Comprehensive ML/AI dependencies

### Issues

❌ Heavy dependencies (torch, transformers, etc.) - optimization needed  
❌ Configuration scattered (config.yaml, secrets.yml.example, .env patterns)  
❌ No clear hexagonal architecture boundaries  
❌ Complex routing logic mixed with infrastructure  
❌ Missing some quality tools (vulture, cloc)  
❌ Pydantic-settings not fully utilized  
❌ No clear adapter pattern for model providers

---

## Proposed Changes

### Phase 1: Dependency Optimization (15 hours)

#### 1.1 Analyze and Optimize ML Dependencies

**Current Heavy Dependencies:**

- torch>=2.8.0 (large)
- transformers>=4.35.0 (large)
- scikit-learn>=1.7.0
- xgboost>=2.1.0

**Optimization Strategy:**

```toml
[project.optional-dependencies]
# Core routing (minimal)
core = [
    "fastapi>=0.115.0",
    "httpx>=0.25.0",
    "pydantic>=2.5.0",
    "tiktoken>=0.5.0",  # Lightweight token counting
]

# ML features (optional)
ml = [
    "torch>=2.8.0",
    "transformers>=4.35.0",
    "scikit-learn>=1.7.0",
]

# Advanced routing (optional)
advanced = [
    "xgboost>=2.1.0",
    "pandas>=2.2.0",
]

# Full installation
full = ["krouter[core,ml,advanced]"]
```

#### 1.2 Create Lightweight Default Installation

```bash
# Minimal installation (for basic routing)
uv pip install .

# Full installation (for ML features)
uv pip install ".[full]"
```

---

### Phase 2: Configuration Modernization (15 hours)

#### 2.1 Create Comprehensive Pydantic Settings

**File:** `router_core/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator
from typing import Optional, Dict, List
from enum import Enum
import yaml


class RouterStrategy(str, Enum):
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE = "performance"
    BALANCED = "balanced"
    CUSTOM = "custom"


class ModelProviderSettings(BaseSettings):
    """Settings for model providers"""

    openrouter_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None


class RoutingSettings(BaseSettings):
    """Routing configuration"""

    strategy: RouterStrategy = RouterStrategy.BALANCED
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_fallback: bool = True
    max_retries: int = 3

    # Cost optimization
    cost_threshold: float = 0.01  # Max cost per request
    prefer_free_models: bool = True

    # Performance
    max_latency_ms: int = 5000
    enable_streaming: bool = True


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    url: SecretStr
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


class KRouterSettings(BaseSettings):
    """Main krouter settings"""

    model_config = SettingsConfigDict(
        env_prefix="KROUTER_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_ignore_empty=True,
        yaml_file="config.yml",
        secrets_dir=".",
    )

    # App settings
    app_name: str = "krouter"
    debug: bool = False
    log_level: str = "INFO"

    # Components
    providers: ModelProviderSettings = Field(default_factory=ModelProviderSettings)
    routing: RoutingSettings = Field(default_factory=RoutingSettings)
    database: DatabaseSettings

    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = False
    prometheus_port: int = 9090

    @classmethod
    def load(cls):
        """Load settings from YAML files"""
        try:
            with open("config.yml", "r") as f:
                config = yaml.safe_load(f)

            try:
                with open("secrets.yml", "r") as f:
                    secrets = yaml.safe_load(f)
            except FileNotFoundError:
                secrets = {}

            merged = {**config, **secrets}
            return cls(**merged)
        except FileNotFoundError:
            # Fallback to environment variables
            return cls()
```

#### 2.2 Create Structured config.yml

**File:** `config.yml`

```yaml
# KRouter Configuration (Non-sensitive)

app:
  name: "krouter"
  debug: false
  log_level: "INFO"

routing:
  strategy: "balanced"
  enable_caching: true
  cache_ttl: 3600
  enable_fallback: true
  max_retries: 3

  # Cost optimization
  cost_threshold: 0.01
  prefer_free_models: true

  # Performance
  max_latency_ms: 5000
  enable_streaming: true

database:
  pool_size: 10
  max_overflow: 20
  echo: false

# Monitoring
monitoring:
  enable_metrics: true
  enable_tracing: false
  prometheus_port: 9090

# Model registry
models:
  registry_file: "configs/models.registry.yaml"
  auto_discover: true
  cache_ttl: 86400
```

#### 2.3 Create secrets.yml Template

**File:** `secrets.yml.example`

```yaml
# KRouter Secrets (Sensitive)
# Copy to secrets.yml and fill in your values

providers:
  openrouter_api_key: "sk-or-..."
  openai_api_key: "sk-..."
  anthropic_api_key: "sk-ant-..."

database:
  url: "postgresql://user:password@localhost:5432/krouter"

# Optional: External services
jaeger:
  endpoint: "http://localhost:14268/api/traces"

elasticsearch:
  url: "http://localhost:9200"
  username: "elastic"
  password: "changeme"
```

---

### Phase 3: Hexagonal Architecture Refactoring (15 hours)

#### 3.1 Define Port Interfaces

**File:** `router_core/domain/ports.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Model, RoutingRequest, RoutingResponse


class ModelRegistryPort(ABC):
    """Port for model registry"""

    @abstractmethod
    async def get_model(self, model_id: str) -> Optional[Model]:
        pass

    @abstractmethod
    async def list_models(self, filters: dict) -> List[Model]:
        pass

    @abstractmethod
    async def register_model(self, model: Model) -> None:
        pass


class RoutingStrategyPort(ABC):
    """Port for routing strategies"""

    @abstractmethod
    async def select_model(self, request: RoutingRequest) -> Model:
        pass

    @abstractmethod
    async def rank_models(self, request: RoutingRequest) -> List[Model]:
        pass


class ModelProviderPort(ABC):
    """Port for model providers"""

    @abstractmethod
    async def complete(self, model: Model, prompt: str) -> RoutingResponse:
        pass

    @abstractmethod
    async def stream(self, model: Model, prompt: str):
        pass
```

#### 3.2 Implement Adapters

**File:** `router_core/adapters/providers/openrouter.py`

```python
from router_core.domain.ports import ModelProviderPort
from router_core.domain.models import Model, RoutingResponse
import httpx


class OpenRouterAdapter(ModelProviderPort):
    """Adapter for OpenRouter API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1", headers={"Authorization": f"Bearer {api_key}"}
        )

    async def complete(self, model: Model, prompt: str) -> RoutingResponse:
        response = await self.client.post(
            "/chat/completions", json={"model": model.id, "messages": [{"role": "user", "content": prompt}]}
        )
        data = response.json()
        return RoutingResponse(model=model, content=data["choices"][0]["message"]["content"], usage=data["usage"])
```

#### 3.3 Create Application Services

**File:** `router_core/application/routing_service.py`

```python
from router_core.domain.ports import ModelRegistryPort, RoutingStrategyPort, ModelProviderPort
from router_core.domain.models import RoutingRequest, RoutingResponse


class RoutingService:
    """Application service for routing requests"""

    def __init__(self, registry: ModelRegistryPort, strategy: RoutingStrategyPort, provider: ModelProviderPort):
        self.registry = registry
        self.strategy = strategy
        self.provider = provider

    async def route_request(self, request: RoutingRequest) -> RoutingResponse:
        """Route a request to the best model"""
        # Select model using strategy
        model = await self.strategy.select_model(request)

        # Execute request using provider
        response = await self.provider.complete(model, request.prompt)

        return response
```

---

### Phase 4: Code Quality Enhancement (5 hours)

#### 4.1 Add Missing Tools

```toml
[project.optional-dependencies]
dev = [
    # ... existing ...
    "vulture>=2.10.0",
    "cloc>=0.2.5",
]
```

#### 4.2 Configure Vulture

```toml
[tool.vulture]
paths = ["router_core", "config"]
exclude = ["tests", ".venv", "build", "dist"]
min_confidence = 80
ignore_names = ["main", "app", "settings"]
```

#### 4.3 Setup Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

---

## Migration Steps

### Step 1: Backup

```bash
git checkout -b backup/pre-router-modernization
git push origin backup/pre-router-modernization
git checkout main
```

### Step 2: Optimize Dependencies

```bash
# Update pyproject.toml with optional dependencies
# Test minimal installation
uv pip install .

# Test full installation
uv pip install ".[full]"
```

### Step 3: Create Configuration

```bash
# Create config files
touch config.yml
touch secrets.yml.example
cp secrets.yml.example secrets.yml

# Implement settings
# Update code to use new settings
```

### Step 4: Refactor Architecture

```bash
# Create domain/ports.py
# Create adapters
# Create application services
# Update existing code to use new structure
```

### Step 5: Test

```bash
# Run tests
uv run pytest

# Test routing
uv run python -m router_core.cli route "test prompt"

# Run benchmarks
uv run pytest tests/benchmarks/
```

---

## Success Criteria

- [ ] Minimal installation < 500MB (vs current ~2GB)
- [ ] Configuration fully in YAML
- [ ] Clear hexagonal architecture
- [ ] All adapters implement ports
- [ ] Tests passing
- [ ] Benchmarks show no performance regression
- [ ] Code quality tools passing
- [ ] Documentation updated

---

## Risks & Mitigations

### Risk 1: Dependency Changes Break ML Features

**Mitigation:** Optional dependencies, comprehensive testing

### Risk 2: Architecture Refactoring Introduces Bugs

**Mitigation:** Incremental refactoring, maintain backward compatibility

### Risk 3: Performance Regression

**Mitigation:** Benchmark before/after, optimize critical paths

---

## Dependencies

- None (can be done independently)

---

## Follow-up Tasks

1. Optimize model loading (lazy loading)
2. Implement caching layer
3. Add more routing strategies
4. Enhance monitoring and metrics
