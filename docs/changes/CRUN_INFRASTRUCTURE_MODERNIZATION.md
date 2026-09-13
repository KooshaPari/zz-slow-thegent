# Change Proposal: crun Infrastructure Modernization

**Project:** crun  
**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Effort:** 40 hours  
**Risk Level:** LOW (Already has good setup)

---

## Current State Analysis

### Strengths
✅ Already has modern pyproject.toml  
✅ Uses uv (has uv.lock)  
✅ Uses ruff for linting  
✅ Uses msgspec for serialization  
✅ Good test infrastructure  
✅ Modern dependencies (pydantic 2.x, langgraph)

### Issues
❌ Configuration not using pydantic-settings  
❌ No YAML configuration files  
❌ Missing some quality tools (bandit, vulture)  
❌ No pre-commit hooks  
❌ Multi-agent orchestration patterns could be cleaner

---

## Proposed Changes

### Phase 1: Configuration Modernization (15 hours)

#### 1.1 Create Pydantic Settings
**File:** `src/crun/config/settings.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional, List
import yaml


class AgentSettings(BaseSettings):
    """Agent configuration"""

    max_concurrent: int = 5
    timeout: int = 300
    retry_attempts: int = 3


class LLMSettings(BaseSettings):
    """LLM configuration"""

    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    default_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000


class CrunSettings(BaseSettings):
    """Main crun settings"""

    model_config = SettingsConfigDict(env_prefix="CRUN_", env_nested_delimiter="__", case_sensitive=False)

    app_name: str = "crun"
    debug: bool = False
    log_level: str = "INFO"

    agents: AgentSettings = Field(default_factory=AgentSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    enable_caching: bool = True
    cache_ttl: int = 3600

    @classmethod
    def load(cls):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        try:
            with open("secrets.yml", "r") as f:
                secrets = yaml.safe_load(f)
        except FileNotFoundError:
            secrets = {}
        return cls(**{**config, **secrets})
```

#### 1.2 Create Configuration Files
**File:** `config.yml`
```yaml
app:
  name: "crun"
  debug: false
  log_level: "INFO"

agents:
  max_concurrent: 5
  timeout: 300
  retry_attempts: 3

llm:
  default_model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000

features:
  enable_caching: true
  cache_ttl: 3600
```

**File:** `secrets.yml.example`
```yaml
llm:
  openai_api_key: "sk-..."
  anthropic_api_key: "sk-ant-..."
```

---

### Phase 2: Code Quality Enhancement (10 hours)

#### 2.1 Add Quality Tools
```toml
[project.optional-dependencies]
dev = [
    # ... existing ...
    "bandit[toml]>=1.7.6",
    "vulture>=2.10.0",
    "pre-commit>=3.6.0",
]
```

#### 2.2 Configure Tools
```toml
[tool.bandit]
targets = ["src"]
exclude_dirs = ["tests"]

[tool.vulture]
paths = ["src/crun"]
min_confidence = 80
```

#### 2.3 Setup Pre-commit
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

---

### Phase 3: Multi-Agent Patterns (10 hours)

#### 3.1 Standardize Agent Interface
**File:** `src/crun/agents/base.py`
```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class AgentInput(BaseModel):
    """Standard agent input"""

    task: str
    context: Dict[str, Any] = {}


class AgentOutput(BaseModel):
    """Standard agent output"""

    result: Any
    metadata: Dict[str, Any] = {}


class Agent(ABC):
    """Base agent interface"""

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute agent task"""
        pass
```

#### 3.2 Implement Orchestration Patterns
**File:** `src/crun/orchestration/coordinator.py`
```python
from crun.agents.base import Agent, AgentInput, AgentOutput
from typing import List
import asyncio


class AgentCoordinator:
    """Coordinate multiple agents"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents

    async def execute_parallel(self, inputs: List[AgentInput]) -> List[AgentOutput]:
        """Execute agents in parallel"""
        tasks = [agent.execute(input) for agent, input in zip(self.agents, inputs)]
        return await asyncio.gather(*tasks)

    async def execute_sequential(self, inputs: List[AgentInput]) -> List[AgentOutput]:
        """Execute agents sequentially"""
        results = []
        for agent, input in zip(self.agents, inputs):
            result = await agent.execute(input)
            results.append(result)
        return results
```

---

### Phase 4: Testing & Documentation (5 hours)

#### 4.1 Update Tests
```python
# tests/conftest.py
import pytest
from crun.config.settings import CrunSettings


@pytest.fixture
def test_settings():
    return CrunSettings(debug=True, agents={"max_concurrent": 2}, llm={"default_model": "gpt-3.5-turbo"})
```

#### 4.2 Update Documentation
- Configuration guide
- Agent development guide
- Orchestration patterns

---

## Migration Steps

1. **Backup:** Create backup branch
2. **Configuration:** Implement pydantic-settings, create YAML files
3. **Quality Tools:** Add bandit, vulture, pre-commit
4. **Patterns:** Standardize agent interfaces
5. **Test:** Run all tests and quality checks
6. **Document:** Update documentation

---

## Success Criteria

- [ ] YAML configuration implemented
- [ ] Pydantic-settings working
- [ ] All quality tools passing
- [ ] Agent patterns standardized
- [ ] Tests passing
- [ ] Documentation updated

---

## Risks & Mitigations

**Risk:** Breaking changes to agent interfaces  
**Mitigation:** Maintain backward compatibility, gradual migration

---

## Dependencies

None

---

## Follow-up Tasks

1. Create agent development guide
2. Add more orchestration patterns
3. Optimize performance

