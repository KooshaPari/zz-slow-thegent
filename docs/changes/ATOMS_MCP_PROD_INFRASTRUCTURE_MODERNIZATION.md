# Change Proposal: atoms-mcp-prod Infrastructure Modernization

**Project:** atoms-mcp-prod  
**Priority:** CRITICAL  
**Complexity:** MEDIUM  
**Estimated Effort:** 40 hours  
**Risk Level:** HIGH (Production Vercel deployment)

---

## Current State Analysis

### Strengths

✅ Already has comprehensive pyproject.toml  
✅ Uses uv (has uv.lock)  
✅ Uses ruff for linting/formatting  
✅ Has good test coverage setup  
✅ Modern dependencies (pydantic 2.x, fastmcp, etc.)

### Issues

❌ Still has .env file (needed for Vercel but not ideal for local)  
❌ No structured YAML configuration  
❌ Settings scattered across multiple files  
❌ Missing some modern quality tools (vulture, cloc)  
❌ Configuration not type-safe with pydantic-settings  
❌ No clear separation of config vs secrets

---

## Proposed Changes

### Phase 1: Configuration Modernization (12 hours)

#### 1.1 Create Pydantic Settings Structure

**File:** `settings/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional
import os
import yaml


class DatabaseSettings(BaseSettings):
    url: SecretStr
    pool_size: int = 10
    max_overflow: int = 20


class SupabaseSettings(BaseSettings):
    url: str
    anon_key: SecretStr
    service_role_key: SecretStr


class AtomsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ATOMS_", env_nested_delimiter="__", case_sensitive=False, env_ignore_empty=True
    )

    # App settings
    app_name: str = "atoms-mcp"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database: DatabaseSettings

    # Supabase
    supabase: SupabaseSettings

    # API Keys
    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None

    @classmethod
    def load(cls):
        """Load settings based on environment"""
        if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
            # Production: use environment variables
            return cls()
        else:
            # Local: use YAML files
            return cls.from_yaml()

    @classmethod
    def from_yaml(cls):
        """Load from YAML files (local development)"""
        # Load non-sensitive config
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        # Load secrets
        try:
            with open("secrets.yml", "r") as f:
                secrets = yaml.safe_load(f)
        except FileNotFoundError:
            secrets = {}

        # Merge and create settings
        merged = {**config, **secrets}
        return cls(**merged)
```

#### 1.2 Create config.yml Template

**File:** `config.yml`

```yaml
# Atoms MCP Configuration (Non-sensitive)
# This file is tracked in git

app:
  name: "atoms-mcp"
  debug: false
  log_level: "INFO"

database:
  pool_size: 10
  max_overflow: 20

supabase:
  url: "https://your-project.supabase.co"

# Feature flags
features:
  enable_caching: true
  enable_metrics: true
  enable_tracing: false
```

#### 1.3 Create secrets.yml.example

**File:** `secrets.yml.example`

```yaml
# Atoms MCP Secrets (Sensitive)
# Copy to secrets.yml and fill in your values
# secrets.yml is git-ignored

database:
  url: "postgresql://user:password@localhost:5432/atoms"

supabase:
  anon_key: "your-anon-key"
  service_role_key: "your-service-role-key"

# API Keys
openai_api_key: "sk-..."
anthropic_api_key: "sk-ant-..."
workos_api_key: "sk-..."
```

#### 1.4 Update .gitignore

```
# Secrets
secrets.yml
.env.local

# Keep .env for Vercel
# .env
```

#### 1.5 Update Code to Use New Settings

**File:** `server/core.py` (example)

```python
from settings.config import AtomsSettings

# Load settings once at startup
settings = AtomsSettings.load()


# Use throughout application
def get_database_url():
    return settings.database.url.get_secret_value()
```

---

### Phase 2: Enhanced Code Quality Tools (10 hours)

#### 2.1 Add Missing Tools to pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    # ... existing tools ...
    "vulture>=2.10.0",  # Dead code detection
    "cloc>=0.2.5",      # Code metrics
    "zuban>=0.1.0",     # Fast type checker (alternative to mypy)
]
```

#### 2.2 Configure Vulture

```toml
[tool.vulture]
paths = ["lib", "tools", "config", "server", "scripts", "src", "utils"]
exclude = ["tests", "archive", ".venv", "schemas/generated"]
min_confidence = 80
ignore_names = ["main", "cli", "settings", "app"]
```

#### 2.3 Add Pre-commit Hooks

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

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml", "-ll"]
```

---

### Phase 3: Vercel Integration (8 hours)

#### 3.1 Keep .env for Vercel

The `.env` file remains for Vercel deployments. The hybrid approach allows:

- **Local development:** Uses `config.yml` + `secrets.yml`
- **Vercel deployment:** Uses `.env` file (environment variables)

#### 3.2 Update Vercel Configuration

**File:** `vercel.json`

```json
{
  "buildCommand": "uv pip install -e .",
  "env": {
    "VERCEL": "1",
    "ATOMS_APP_NAME": "atoms-mcp-prod",
    "ATOMS_LOG_LEVEL": "INFO"
  }
}
```

#### 3.3 Create Deployment Script

**File:** `scripts/deploy.sh`

```bash
#!/bin/bash
# Deployment script for Vercel

# Ensure .env exists for Vercel
if [ ! -f .env ]; then
    echo "Error: .env file required for Vercel deployment"
    exit 1
fi

# Run tests
uv run pytest

# Deploy
vercel deploy --prod
```

---

### Phase 4: Testing & Validation (10 hours)

#### 4.1 Update Tests for New Settings

**File:** `tests/conftest.py`

```python
import pytest
from settings.config import AtomsSettings


@pytest.fixture
def test_settings():
    """Provide test settings"""
    return AtomsSettings(
        app_name="atoms-mcp-test",
        debug=True,
        database={"url": "postgresql://localhost/test"},
        supabase={"url": "http://localhost:54321", "anon_key": "test-key", "service_role_key": "test-key"},
    )
```

#### 4.2 Test Configuration Loading

**File:** `tests/test_settings.py`

```python
def test_settings_from_yaml(tmp_path):
    """Test loading settings from YAML"""
    config_file = tmp_path / "config.yml"
    config_file.write_text("""
app:
  name: "test-app"
  debug: true
""")

    # Test loading
    settings = AtomsSettings.from_yaml()
    assert settings.app_name == "test-app"
    assert settings.debug is True


def test_settings_from_env(monkeypatch):
    """Test loading settings from environment"""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("ATOMS_APP_NAME", "prod-app")

    settings = AtomsSettings.load()
    assert settings.app_name == "prod-app"
```

---

## Migration Steps

### Step 1: Backup

```bash
# Create backup
git checkout -b backup/pre-modernization
git push origin backup/pre-modernization
git checkout main
```

### Step 2: Create Configuration Files

```bash
# Create settings directory
mkdir -p settings

# Create config files
touch config.yml
touch secrets.yml.example
cp secrets.yml.example secrets.yml

# Update .gitignore
echo "secrets.yml" >> .gitignore
```

### Step 3: Install New Dependencies

```bash
# Add new dev dependencies
uv pip install vulture cloc zuban

# Update uv.lock
uv lock
```

### Step 4: Implement Settings

```bash
# Create settings module
# Implement AtomsSettings class
# Update code to use new settings
```

### Step 5: Test Locally

```bash
# Run tests
uv run pytest

# Test configuration loading
uv run python -c "from settings.config import AtomsSettings; print(AtomsSettings.load())"

# Run server locally
uv run python server/core.py
```

### Step 6: Test Vercel Deployment

```bash
# Deploy to preview
vercel deploy

# Test preview deployment
# Verify environment variables work

# Deploy to production
vercel deploy --prod
```

---

## Rollback Plan

If issues arise:

1. **Immediate Rollback:**

   ```bash
   git checkout backup/pre-modernization
   vercel deploy --prod
   ```

2. **Partial Rollback:**
   - Keep new pyproject.toml
   - Revert settings changes
   - Use old environment variable approach

3. **Configuration Rollback:**
   - Keep code changes
   - Revert to .env only
   - Remove YAML files

---

## Success Criteria

- [ ] Local development uses config.yml + secrets.yml
- [ ] Vercel deployment uses .env (environment variables)
- [ ] All tests passing
- [ ] No breaking changes to API
- [ ] Settings are type-safe with pydantic
- [ ] Secrets are properly separated from config
- [ ] Pre-commit hooks working
- [ ] Code quality tools passing
- [ ] Documentation updated

---

## Risks & Mitigations

### Risk 1: Vercel Deployment Breaks

**Mitigation:** Test on preview deployment first, keep .env approach as fallback

### Risk 2: Settings Migration Incomplete

**Mitigation:** Gradual migration, keep old approach working alongside new

### Risk 3: Test Failures

**Mitigation:** Comprehensive test coverage for settings loading

---

## Dependencies

- None (can be done independently)

---

## Follow-up Tasks

1. Monitor Vercel deployments for issues
2. Gather team feedback on new configuration approach
3. Document best practices for adding new settings
4. Create migration guide for other projects
