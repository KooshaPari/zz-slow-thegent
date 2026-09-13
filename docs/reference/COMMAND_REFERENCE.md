# Command Reference

Quick reference for common commands organized by use case. Each section includes the most-used commands for that workflow.

---

## Getting Started (3 commands)

**Initial setup and environment configuration**

```bash
# 1. Install dependencies
pip install -e .

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 3. Verify installation
python -c "import semantic_tool_router; print('Installation successful')"
```

---

## Daily Development (5 commands)

**Commands you'll run during active development**

```bash
# 1. Run the application
python -m semantic_tool_router

# 2. Run tests (all)
pytest

# 3. Run tests (watch mode - reruns on file change)
pytest --watch

# 4. Run specific test
pytest tests/test_routing.py::test_semantic_similarity

# 5. Format code
ruff format .
```

**IDE Integration**: Configure your editor to run formatters on save using Ruff.

---

## Code Quality & Linting (4 commands)

**Check and maintain code quality**

```bash
# 1. Lint code (check only)
ruff check .

# 2. Lint and fix automatically
ruff check . --fix

# 3. Type checking
mypy src/

# 4. Run full quality suite
pytest && ruff check . && mypy src/
```

---

## Deployment & Operations (5 commands)

**Production deployment and operational tasks**

```bash
# 1. Build distribution package
python -m build

# 2. Deploy to staging
bash scripts/deploy-staging.sh

# 3. Deploy to production
bash scripts/deploy-production.sh

# 4. Check system health
python -m semantic_tool_router health-check

# 5. View logs
tail -f logs/application.log
```

---

## Database & Migration (4 commands)

**Database management and schema migrations**

```bash
# 1. Initialize database
python -m semantic_tool_router db init

# 2. Run migrations
python -m semantic_tool_router db migrate

# 3. Seed database with test data
python -m semantic_tool_router db seed

# 4. Reset database (development only)
python -m semantic_tool_router db reset --force
```

---

## Documentation (3 commands)

**Documentation building and validation**

```bash
# 1. Validate documentation
bash scripts/validate-docs.sh

# 2. Generate documentation index
bash scripts/generate-docs-index.sh

# 3. Build documentation site
python -m sphinx docs/ docs/_build/html
```

---

## Troubleshooting (4 commands)

**Debugging and problem resolution**

```bash
# 1. Show debug logs
DEBUG=1 python -m semantic_tool_router

# 2. Test connectivity to external services
python -m semantic_tool_router test-connections

# 3. Check system diagnostics
python -m semantic_tool_router diagnostics

# 4. View recent errors
grep -i error logs/application.log | tail -20
```

---

## Advanced / Rare (6 commands)

**Less common but important operations**

```bash
# 1. Clean build artifacts
python -m build --clean

# 2. Update dependencies to latest compatible versions
pip install --upgrade -r requirements.txt

# 3. Run integration tests (slower, requires external services)
pytest -m integration

# 4. Performance profiling
python -m cProfile -o profile.stats -m semantic_tool_router

# 5. Generate test coverage report
pytest --cov=src --cov-report=html

# 6. Dry-run deployment (shows what would be deployed)
bash scripts/deploy-production.sh --dry-run
```

---

## Helper Scripts

The `scripts/` directory contains automated helpers:

| Script                   | Purpose                        |
| ------------------------ | ------------------------------ |
| `delegate_5_items.sh`    | Delegate work items to agents  |
| `generate_writeups.sh`   | Generate writeup documentation |
| `validate-docs.sh`       | Validate documentation quality |
| `update_hooks_to_zsh.sh` | Configure git hooks            |

---

## Environment Variables

Key variables for configuration (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis Cache
REDIS_URL=redis://localhost:6379

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info
```

---

## Quick Workflows

### Setup a new development environment

```bash
pip install -e .
cp .env.example .env
pytest              # Verify everything works
```

### Make and test a change

```bash
# Edit files...
ruff format .       # Format code
ruff check . --fix  # Auto-fix linting issues
pytest              # Run tests
mypy src/           # Type check
```

### Deploy to production

```bash
# Review changes
git diff HEAD

# Run tests
pytest && ruff check . && mypy src/

# Deploy
bash scripts/deploy-production.sh --dry-run  # Preview
bash scripts/deploy-production.sh            # Execute
```

### Debug a failing test

```bash
# Run with verbose output
pytest -vv tests/test_routing.py::test_semantic_similarity

# Run with print statements
pytest -s tests/test_routing.py

# Drop into debugger on failure
pytest --pdb tests/test_routing.py
```

---

## Cheat Sheet

| Task       | Command                             |
| ---------- | ----------------------------------- |
| Install    | `pip install -e .`                  |
| Test       | `pytest`                            |
| Format     | `ruff format .`                     |
| Lint       | `ruff check . --fix`                |
| Type check | `mypy src/`                         |
| Run app    | `python -m semantic_tool_router`    |
| Deploy     | `bash scripts/deploy-production.sh` |
| Docs       | `bash scripts/validate-docs.sh`     |
| Debug      | `pytest -s --pdb`                   |

---

## Getting Help

- **Installation issues**: See [CRUN Setup & Installation Guide](./docs/guides/setup-guide.md)
- **Test failures**: See [Troubleshooting Guide](./docs/troubleshooting/faq.md)
- **Deployment problems**: See [Deployment Guide](./docs/deployment/deployment-overview.md)
- **API questions**: See [API Reference](./docs/api/rest-api.md)

---

**Last updated**: 2026-02-20
For more information, see [Documentation Hub](./docs/README.md)
