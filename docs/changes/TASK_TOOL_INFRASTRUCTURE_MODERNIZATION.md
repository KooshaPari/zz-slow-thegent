# Change Proposal: task-tool Infrastructure Modernization

**Project:** task-tool  
**Priority:** MEDIUM  
**Complexity:** LOW  
**Estimated Effort:** 15 hours  
**Risk Level:** LOW

---

## Current State

MCP server for task management.

---

## Proposed Changes

### Phase 1: Foundation (6 hours)

- Modern pyproject.toml with FastMCP
- Install uv
- Configure ruff

### Phase 2: Configuration (6 hours)

```python
class TaskToolSettings(BaseSettings):
    app_name: str = "task-tool"
    storage_backend: str = "sqlite"
    database_url: SecretStr
```

**config.yml:**

```yaml
app:
  name: "task-tool"
storage:
  backend: "sqlite"
```

### Phase 3: MCP Standardization (3 hours)

- Align with atoms-mcp-prod and zen-mcp-server patterns
- Add quality tools
- Setup pre-commit

---

## Migration Steps

1. Create pyproject.toml
2. Install uv
3. Implement settings
4. Standardize MCP patterns
5. Test

---

## Success Criteria

- [ ] Modern setup
- [ ] YAML config
- [ ] MCP patterns standardized
- [ ] Quality tools passing
