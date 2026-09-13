# Change Proposal: morph Infrastructure Modernization

**Project:** morph  
**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Effort:** 30 hours  
**Risk Level:** LOW

---

## Current State Analysis

### Strengths

✅ MCP creation tool  
✅ Has basic structure

### Issues

❌ No modern pyproject.toml  
❌ No uv configuration  
❌ No YAML configuration  
❌ Missing quality tools  
❌ Could use library replacements

---

## Proposed Changes

### Phase 1: Foundation (10 hours)

- Create modern pyproject.toml with hatch
- Install uv, create uv.lock
- Configure ruff, mypy
- Remove requirements.txt

### Phase 2: Configuration (10 hours)

- Implement pydantic-settings
- Create config.yml and secrets.yml
- Update code to use settings

### Phase 3: Simplification (10 hours)

- Replace custom implementations with libraries
- Add quality tools (bandit, vulture)
- Setup pre-commit hooks
- Update documentation

---

## Key Changes

**pyproject.toml:**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "morph"
version = "1.0.0"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "typer>=0.9.0",
    "pyyaml>=6.0.1",
]
```

**Settings:**

```python
class MorphSettings(BaseSettings):
    app_name: str = "morph"
    debug: bool = False
    template_dir: str = "templates"
    output_dir: str = "output"
```

---

## Migration Steps

1. Create pyproject.toml
2. Install uv and dependencies
3. Implement settings
4. Add quality tools
5. Test and document

---

## Success Criteria

- [ ] Modern pyproject.toml
- [ ] uv.lock file
- [ ] YAML configuration
- [ ] Quality tools passing
- [ ] Tests passing

---

## Dependencies

None
