# Change Proposal: pheno-sdk Infrastructure Modernization

**Project:** pheno-sdk  
**Priority:** HIGH  
**Complexity:** HIGH  
**Estimated Effort:** 50 hours  
**Risk Level:** MEDIUM (Dependency for other projects, large codebase)

---

## Current State Analysis

### Strengths
✅ Large, comprehensive SDK  
✅ Has pyproject.toml  
✅ Good structure with multiple modules  
✅ Pydantic models for data validation  
✅ Test infrastructure present

### Issues
❌ No uv configuration (likely using pip/poetry)  
❌ Configuration scattered across files  
❌ No clear hexagonal architecture boundaries  
❌ Missing modern quality tools (ruff, bandit, vulture)  
❌ No pydantic-settings for configuration  
❌ Public API not clearly defined  
❌ Infrastructure code mixed with domain logic  
❌ No clear adapter pattern for external services

---

## Proposed Changes

### Phase 1: Foundation Setup (15 hours)

#### 1.1 Create Modern pyproject.toml
```toml
[build-system]
requires = ["hatchling>=1.21.0"]
build-backend = "hatchling.build"

[project]
name = "pheno-sdk"
version = "1.0.0"
description = "Infrastructure SDK for Pheno platform"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.25.0",
    "tenacity>=8.2.0",
    "structlog>=24.1.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
aws = [
    "boto3>=1.34.0",
    "aioboto3>=12.3.0",
]
gcp = [
    "google-cloud-storage>=2.14.0",
    "google-cloud-compute>=1.15.0",
]
azure = [
    "azure-storage-blob>=12.19.0",
    "azure-mgmt-compute>=30.5.0",
]
all = ["pheno-sdk[aws,gcp,azure]"]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.8.0",
    "mypy>=1.8.0",
    "bandit[toml]>=1.7.6",
    "vulture>=2.10.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM", "RET", "PTH", "RUF"]
ignore = ["E501"]

[tool.hatch.build.targets.wheel]
packages = ["src/pheno_sdk"]
```

#### 1.2 Install uv and Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Create lock file
uv lock
```

---

### Phase 2: Hexagonal Architecture Refactoring (20 hours)

#### 2.1 Define Domain Layer
**File:** `src/pheno_sdk/domain/models.py`
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResourceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Resource(BaseModel):
    """Domain model for infrastructure resource"""

    id: str
    name: str
    type: str
    status: ResourceStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class Deployment(BaseModel):
    """Domain model for deployment"""

    id: str
    name: str
    resources: list[Resource]
    status: ResourceStatus
    config: Dict[str, Any]
```

#### 2.2 Define Port Interfaces
**File:** `src/pheno_sdk/domain/ports.py`
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Resource, Deployment


class InfrastructureProviderPort(ABC):
    """Port for infrastructure providers (AWS, GCP, Azure)"""

    @abstractmethod
    async def create_resource(self, resource: Resource) -> Resource:
        """Create a new infrastructure resource"""
        pass

    @abstractmethod
    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID"""
        pass

    @abstractmethod
    async def list_resources(self, filters: dict) -> List[Resource]:
        """List resources with filters"""
        pass

    @abstractmethod
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource"""
        pass


class DeploymentPort(ABC):
    """Port for deployment operations"""

    @abstractmethod
    async def deploy(self, deployment: Deployment) -> Deployment:
        """Deploy infrastructure"""
        pass

    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> ResourceStatus:
        """Get deployment status"""
        pass


class StoragePort(ABC):
    """Port for storage operations"""

    @abstractmethod
    async def upload(self, key: str, data: bytes) -> str:
        """Upload data to storage"""
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download data from storage"""
        pass
```

#### 2.3 Implement Adapters
**File:** `src/pheno_sdk/adapters/aws/infrastructure.py`
```python
from pheno_sdk.domain.ports import InfrastructureProviderPort
from pheno_sdk.domain.models import Resource, ResourceStatus
import boto3
from typing import List, Optional


class AWSInfrastructureAdapter(InfrastructureProviderPort):
    """AWS implementation of infrastructure provider"""

    def __init__(self, region: str, credentials: dict):
        self.region = region
        self.ec2 = boto3.client("ec2", region_name=region, **credentials)

    async def create_resource(self, resource: Resource) -> Resource:
        """Create AWS resource (EC2, etc.)"""
        # Implementation
        pass

    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get AWS resource"""
        # Implementation
        pass

    async def list_resources(self, filters: dict) -> List[Resource]:
        """List AWS resources"""
        # Implementation
        pass

    async def delete_resource(self, resource_id: str) -> bool:
        """Delete AWS resource"""
        # Implementation
        pass
```

**File:** `src/pheno_sdk/adapters/gcp/infrastructure.py`
```python
from pheno_sdk.domain.ports import InfrastructureProviderPort
from google.cloud import compute_v1


class GCPInfrastructureAdapter(InfrastructureProviderPort):
    """GCP implementation of infrastructure provider"""

    # Similar structure to AWS adapter
    pass
```

#### 2.4 Create Application Services
**File:** `src/pheno_sdk/application/infrastructure_service.py`
```python
from pheno_sdk.domain.ports import InfrastructureProviderPort
from pheno_sdk.domain.models import Resource, ResourceStatus
from typing import List, Optional


class InfrastructureService:
    """Application service for infrastructure operations"""

    def __init__(self, provider: InfrastructureProviderPort):
        self.provider = provider

    async def provision_resource(self, resource: Resource) -> Resource:
        """Provision a new resource"""
        # Business logic
        created = await self.provider.create_resource(resource)
        # Additional orchestration
        return created

    async def get_resource_status(self, resource_id: str) -> Optional[ResourceStatus]:
        """Get resource status"""
        resource = await self.provider.get_resource(resource_id)
        return resource.status if resource else None
```

#### 2.5 Define Public API
**File:** `src/pheno_sdk/__init__.py`
```python
"""
Pheno SDK - Infrastructure SDK for Pheno platform

Public API:
- InfrastructureService: Main service for infrastructure operations
- Resource, Deployment: Domain models
- AWSInfrastructureAdapter, GCPInfrastructureAdapter: Provider adapters
"""

# Public API exports
from pheno_sdk.application.infrastructure_service import InfrastructureService
from pheno_sdk.domain.models import Resource, Deployment, ResourceStatus
from pheno_sdk.adapters.aws.infrastructure import AWSInfrastructureAdapter
from pheno_sdk.adapters.gcp.infrastructure import GCPInfrastructureAdapter

__all__ = [
    "InfrastructureService",
    "Resource",
    "Deployment",
    "ResourceStatus",
    "AWSInfrastructureAdapter",
    "GCPInfrastructureAdapter",
]

__version__ = "1.0.0"
```

---

### Phase 3: Configuration Modernization (10 hours)

#### 3.1 Create Pydantic Settings
**File:** `src/pheno_sdk/config/settings.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional
import yaml


class AWSSettings(BaseSettings):
    """AWS configuration"""

    region: str = "us-east-1"
    access_key_id: Optional[SecretStr] = None
    secret_access_key: Optional[SecretStr] = None


class GCPSettings(BaseSettings):
    """GCP configuration"""

    project_id: str
    credentials_file: Optional[str] = None


class PhenoSDKSettings(BaseSettings):
    """Main SDK settings"""

    model_config = SettingsConfigDict(env_prefix="PHENO_", env_nested_delimiter="__", case_sensitive=False)

    # General
    debug: bool = False
    log_level: str = "INFO"

    # Providers
    aws: Optional[AWSSettings] = None
    gcp: Optional[GCPSettings] = None

    # Features
    enable_caching: bool = True
    cache_ttl: int = 3600
    max_retries: int = 3
    timeout: int = 30

    @classmethod
    def load(cls):
        """Load settings from YAML"""
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
            return cls()
```

#### 3.2 Create Configuration Files
**File:** `config.yml`
```yaml
# Pheno SDK Configuration

general:
  debug: false
  log_level: "INFO"

aws:
  region: "us-east-1"

gcp:
  project_id: "my-project"

features:
  enable_caching: true
  cache_ttl: 3600
  max_retries: 3
  timeout: 30
```

**File:** `secrets.yml.example`
```yaml
# Pheno SDK Secrets

aws:
  access_key_id: "AKIA..."
  secret_access_key: "..."

gcp:
  credentials_file: "/path/to/credentials.json"
```

---

### Phase 4: Code Quality & Testing (5 hours)

#### 4.1 Configure Quality Tools
```toml
[tool.bandit]
targets = ["src"]
exclude_dirs = ["tests"]

[tool.vulture]
paths = ["src/pheno_sdk"]
min_confidence = 80

[tool.mypy]
python_version = "3.11"
strict = true
```

#### 4.2 Setup Pre-commit
**File:** `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

#### 4.3 Update Tests
```python
# tests/conftest.py
import pytest
from pheno_sdk.config.settings import PhenoSDKSettings


@pytest.fixture
def test_settings():
    return PhenoSDKSettings(
        debug=True,
        aws={"region": "us-east-1"},
    )
```

---

## Migration Steps

### Step 1: Backup
```bash
git checkout -b backup/pre-modernization
git push origin backup/pre-modernization
git checkout main
git checkout -b feature/infrastructure-modernization
```

### Step 2: Setup Foundation
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create pyproject.toml
# Install dependencies
uv pip install -e ".[dev]"
uv lock
```

### Step 3: Refactor Architecture
```bash
# Create new directory structure
mkdir -p src/pheno_sdk/{domain,application,adapters,config}

# Move and refactor code
# Implement ports and adapters
# Define public API
```

### Step 4: Implement Configuration
```bash
# Create settings
# Create config files
# Update code to use settings
```

### Step 5: Test
```bash
pytest
ruff check --fix .
bandit -r src/
```

---

## Success Criteria

- [ ] Hexagonal architecture implemented
- [ ] Clear port/adapter boundaries
- [ ] Public API well-defined
- [ ] YAML configuration
- [ ] All quality tools passing
- [ ] Tests passing
- [ ] Documentation updated

---

## Risks & Mitigations

### Risk 1: Breaking Changes for Dependent Projects
**Mitigation:** Maintain backward compatibility, versioning

### Risk 2: Architecture Refactoring Complexity
**Mitigation:** Incremental refactoring, comprehensive testing

---

## Dependencies

- Should be completed before projects that depend on it

---

## Follow-up Tasks

1. Update dependent projects
2. Create migration guide for SDK users
3. Publish new version

