# Change Proposal: zen-mcp-server Infrastructure Modernization

**Project:** zen-mcp-server  
**Priority:** HIGH  
**Complexity:** LOW  
**Estimated Effort:** 30 hours  
**Risk Level:** MEDIUM (Large codebase, already modernized)

---

## Current State Analysis

### Strengths
✅ Already uses uv (has uv.lock)  
✅ Already uses ruff for linting/formatting  
✅ Already uses zuban for type checking  
✅ Has comprehensive pyproject.toml  
✅ Good test infrastructure (pytest)  
✅ Modern dependencies (pydantic 2.x, fastmcp)  
✅ Has work-prompts with architecture patterns  
✅ Well-structured codebase

### Issues
❌ Configuration scattered across multiple files  
❌ Still has .env file (should use YAML)  
❌ No pydantic-settings implementation  
❌ Missing some quality tools (vulture, cloc, bandit)  
❌ No pre-commit hooks configured  
❌ Settings not type-safe with pydantic-settings  
❌ No clear config vs secrets separation

---

## Proposed Changes

### Phase 1: Configuration Modernization (10 hours)

#### 1.1 Create Pydantic Settings Structure
**File:** `src/zen_mcp/config/settings.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator
from typing import Optional, List
import yaml
from pathlib import Path


class LLMProviderSettings(BaseSettings):
    """LLM provider configuration"""

    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    openrouter_api_key: Optional[SecretStr] = None


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    url: SecretStr = Field(default="sqlite:///zen_mcp.db")
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False


class ZenSettings(BaseSettings):
    """Main Zen MCP settings"""

    model_config = SettingsConfigDict(
        env_prefix="ZEN_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_ignore_empty=True,
        yaml_file="config.yml",
        secrets_dir=".",
    )

    # App settings
    app_name: str = "zen-mcp-server"
    debug: bool = False
    log_level: str = "INFO"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Components
    llm_providers: LLMProviderSettings = Field(default_factory=LLMProviderSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Features
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_metrics: bool = True
    enable_tracing: bool = False

    # Zen-specific
    max_context_length: int = 128000
    default_model: str = "gpt-4"
    enable_streaming: bool = True

    @classmethod
    def load(cls):
        """Load settings from YAML files"""
        config_path = Path("config.yml")
        secrets_path = Path("secrets.yml")

        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        secrets = {}
        if secrets_path.exists():
            with open(secrets_path, "r") as f:
                secrets = yaml.safe_load(f) or {}

        merged = {**config, **secrets}
        return cls(**merged)
```

#### 1.2 Create config.yml
**File:** `config.yml`
```yaml
# Zen MCP Server Configuration (Non-sensitive)

app:
  name: "zen-mcp-server"
  debug: false
  log_level: "INFO"

server:
  host: "0.0.0.0"
  port: 8000

database:
  pool_size: 5
  max_overflow: 10
  echo: false

features:
  enable_caching: true
  cache_ttl: 3600
  enable_metrics: true
  enable_tracing: false

zen:
  max_context_length: 128000
  default_model: "gpt-4"
  enable_streaming: true

# Tool configurations
tools:
  enabled:
    - "code_analysis"
    - "task_management"
    - "context_building"
  
# Resource configurations
resources:
  max_file_size_mb: 10
  allowed_extensions:
    - ".py"
    - ".md"
    - ".txt"
    - ".json"
    - ".yaml"
```

#### 1.3 Create secrets.yml.example
**File:** `secrets.yml.example`
```yaml
# Zen MCP Server Secrets (Sensitive)
# Copy to secrets.yml and fill in your values

llm_providers:
  openai_api_key: "sk-..."
  anthropic_api_key: "sk-ant-..."
  openrouter_api_key: "sk-or-..."

database:
  url: "sqlite:///zen_mcp.db"
  # For PostgreSQL:
  # url: "postgresql://user:password@localhost:5432/zen_mcp"

# Optional: External services
monitoring:
  sentry_dsn: "https://...@sentry.io/..."
  prometheus_endpoint: "http://localhost:9090"
```

#### 1.4 Update Code to Use Settings
**File:** `src/zen_mcp/server.py` (example)
```python
from zen_mcp.config.settings import ZenSettings

# Load settings once at startup
settings = ZenSettings.load()


# Use throughout application
def get_llm_client():
    api_key = settings.llm_providers.openai_api_key
    if api_key:
        return OpenAI(api_key=api_key.get_secret_value())
    return None
```

#### 1.5 Remove .env File
```bash
# Migrate all .env values to config.yml and secrets.yml
# Then remove .env
rm .env

# Update .gitignore
echo "secrets.yml" >> .gitignore
```

---

### Phase 2: Code Quality Enhancement (10 hours)

#### 2.1 Add Missing Tools to pyproject.toml
```toml
[project.optional-dependencies]
dev = [
    # ... existing tools ...
    "bandit[toml]>=1.7.6",  # Security scanning
    "vulture>=2.10.0",       # Dead code detection
    "cloc>=0.2.5",           # Code metrics
]
```

#### 2.2 Configure Bandit
```toml
[tool.bandit]
targets = ["src"]
exclude_dirs = ["tests", ".venv", "build"]
skips = ["B101", "B601"]  # Skip assert and shell injection (if needed)
```

#### 2.3 Configure Vulture
```toml
[tool.vulture]
paths = ["src/zen_mcp"]
exclude = ["tests", ".venv", "build", "dist"]
min_confidence = 80
ignore_names = ["main", "app", "cli", "settings"]
```

#### 2.4 Setup Pre-commit Hooks
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
      - id: check-merge-conflict
      - id: check-added-large-files

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

#### 2.5 Install and Run Pre-commit
```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

### Phase 3: Documentation & Cleanup (10 hours)

#### 3.1 Update README.md
Add sections for:
- Configuration (how to use config.yml and secrets.yml)
- Development setup (using uv)
- Code quality tools
- Pre-commit hooks

#### 3.2 Create Configuration Documentation
**File:** `docs/configuration.md`
```markdown
# Configuration Guide

## Overview
Zen MCP Server uses YAML-based configuration with pydantic-settings for type safety.

## Files
- `config.yml` - Non-sensitive configuration (git-tracked)
- `secrets.yml` - Sensitive data like API keys (git-ignored)
- `secrets.yml.example` - Template for secrets

## Setup
1. Copy secrets template:
   ```bash
   cp secrets.yml.example secrets.yml
   ```

2. Edit secrets.yml with your values

3. Run the server:
   ```bash
   uv run zen-mcp-server
   ```

## Configuration Options
[Document all settings from ZenSettings class]
```

#### 3.3 Clean Up Legacy Files
```bash
# Remove old configuration files
rm -f .env .env.example

# Remove old requirements files (if any)
rm -f requirements*.txt

# Clean up build artifacts
rm -rf build/ dist/ *.egg-info/
```

#### 3.4 Update work-prompts
Update work-prompts to reference new configuration approach:
- `work-prompts/python-patterns-guide.md`
- `work-prompts/tdd-architecture-prompts.md`

---

## Migration Steps

### Step 1: Backup
```bash
cd zen-mcp-server
git checkout -b backup/pre-modernization
git push origin backup/pre-modernization
git checkout main
git checkout -b feature/infrastructure-modernization
```

### Step 2: Create Configuration Structure
```bash
# Create config directory
mkdir -p src/zen_mcp/config
touch src/zen_mcp/config/__init__.py
touch src/zen_mcp/config/settings.py

# Create config files
touch config.yml
touch secrets.yml.example
cp secrets.yml.example secrets.yml
```

### Step 3: Implement Settings
```bash
# Implement ZenSettings class
# Update code to use new settings
# Test configuration loading
uv run python -c "from zen_mcp.config.settings import ZenSettings; print(ZenSettings.load())"
```

### Step 4: Add Quality Tools
```bash
# Install new tools
uv pip install bandit vulture cloc pre-commit

# Update uv.lock
uv lock

# Setup pre-commit
pre-commit install
pre-commit run --all-files
```

### Step 5: Run Quality Checks
```bash
# Ruff
ruff check --fix .
ruff format .

# Bandit
bandit -r src/ -c pyproject.toml

# Vulture
vulture src/ --min-confidence 80

# Zuban (already configured)
zuban check src/
```

### Step 6: Update Documentation
```bash
# Update README.md
# Create docs/configuration.md
# Update work-prompts
```

### Step 7: Test Everything
```bash
# Run tests
uv run pytest

# Test server startup
uv run zen-mcp-server --help

# Test configuration loading
uv run python -c "from zen_mcp.config.settings import ZenSettings; s = ZenSettings.load(); print(s.model_dump())"
```

### Step 8: Clean Up
```bash
# Remove old files
rm .env

# Update .gitignore
echo "secrets.yml" >> .gitignore

# Commit changes
git add .
git commit -m "feat: modernize infrastructure with YAML config and enhanced quality tools"
```

---

## Rollback Plan

If issues arise:

1. **Immediate Rollback:**
   ```bash
   git checkout backup/pre-modernization
   ```

2. **Partial Rollback:**
   - Keep new quality tools
   - Revert settings changes
   - Use old .env approach

3. **Configuration Rollback:**
   - Keep code changes
   - Revert to .env only
   - Remove YAML files

---

## Success Criteria

- [ ] No .env file (replaced with YAML)
- [ ] config.yml exists and is complete
- [ ] secrets.yml.example exists
- [ ] Pydantic settings implemented
- [ ] All code uses new settings
- [ ] Pre-commit hooks installed and passing
- [ ] Bandit security scan passing
- [ ] Vulture dead code < 5%
- [ ] Zuban type checking passing
- [ ] All tests passing
- [ ] Documentation updated
- [ ] work-prompts updated

---

## Risks & Mitigations

### Risk 1: Configuration Migration Incomplete
**Mitigation:** Comprehensive testing, gradual migration

### Risk 2: Breaking Changes for Users
**Mitigation:** Clear migration guide, backward compatibility where possible

### Risk 3: Test Failures
**Mitigation:** Update tests to use new settings, comprehensive test coverage

---

## Dependencies

- None (can be done independently)

---

## Follow-up Tasks

1. Monitor for configuration issues
2. Gather user feedback on new configuration approach
3. Create migration guide for users
4. Update CI/CD pipelines
5. Consider adding configuration validation CLI command

