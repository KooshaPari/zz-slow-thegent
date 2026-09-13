# Change Proposal: atomsAgent Infrastructure Modernization

**Project:** agentapi/atomsAgent  
**Priority:** HIGH  
**Complexity:** LOW  
**Estimated Effort:** 20 hours  
**Risk Level:** MEDIUM (Vercel deployment)

---

## Current State Analysis

### Strengths

✅ Code generation CLI  
✅ Vercel deployment

### Issues

❌ No modern pyproject.toml  
❌ No uv configuration  
❌ Uses .env only  
❌ Missing quality tools

---

## Proposed Changes

### Phase 1: Foundation (8 hours)

- Create modern pyproject.toml
- Install uv, create uv.lock
- Configure ruff, mypy
- Remove requirements.txt

### Phase 2: Hybrid Configuration (8 hours)

**Like atoms-mcp-prod:**

```python
class AtomsAgentSettings(BaseSettings):
    @classmethod
    def load(cls):
        if os.getenv("VERCEL"):
            return cls()  # Environment variables
        else:
            return cls.from_yaml()  # YAML files
```

- Keep .env for Vercel
- Add config.yml and secrets.yml for local
- Implement pydantic-settings

### Phase 3: Code Quality (4 hours)

- Add bandit, vulture
- Setup pre-commit hooks
- Run quality checks

---

## Key Configuration

**config.yml:**

```yaml
app:
  name: "atoms-agent"
  debug: false

generation:
  default_model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000
```

**secrets.yml:**

```yaml
api_keys:
  openai: "sk-..."
  anthropic: "sk-ant-..."
```

---

## Migration Steps

1. Backup
2. Create pyproject.toml
3. Install uv
4. Implement hybrid settings
5. Add quality tools
6. Test locally and on Vercel

---

## Success Criteria

- [ ] Hybrid configuration working
- [ ] Local uses YAML
- [ ] Vercel uses .env
- [ ] Quality tools passing
- [ ] Tests passing
- [ ] Vercel deployment working

---

## Risks & Mitigations

**Risk:** Vercel deployment breaks  
**Mitigation:** Test on preview first, keep .env approach

---

## Dependencies

None
