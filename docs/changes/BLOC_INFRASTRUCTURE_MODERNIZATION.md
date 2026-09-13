# Change Proposal: bloc Infrastructure Modernization

**Project:** bloc  
**Priority:** LOW  
**Complexity:** LOW  
**Estimated Effort:** 10 hours  
**Risk Level:** LOW

---

## Current State

Simple code analysis CLI tool.

---

## Proposed Changes (Quick Modernization)

### Phase 1: Foundation (4 hours)

```toml
[project]
name = "bloc"
dependencies = [
    "typer>=0.9.0",
    "pydantic-settings>=2.1.0",
    "pyyaml>=6.0.1",
]
```

### Phase 2: Configuration (3 hours)

```python
class BlocSettings(BaseSettings):
    debug: bool = False
    output_format: str = "json"
```

### Phase 3: Quality (3 hours)

- Add ruff, bandit
- Setup pre-commit
- Test

---

## Migration Steps

1. Create pyproject.toml
2. Install uv
3. Add settings
4. Add quality tools
5. Test

---

## Success Criteria

- [ ] Modern setup
- [ ] YAML config
- [ ] Quality tools passing
