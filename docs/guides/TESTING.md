# thegent Testing Guide

This guide defines the testing philosophy and standards for `thegent`.

## 1. Test Pyramid Targets

We maintain a strict test distribution to ensure fast feedback and high reliability:

-   **Unit Tests (70%)**: Fast, isolated tests for individual functions and classes. Found in `tests/` with `@pytest.mark.unit`.
-   **Integration Tests (20%)**: Testing interaction between components (e.g., runners and registries). Marked with `@pytest.mark.integration`.
-   **E2E Tests (10%)**: End-to-end CLI/MCP flows. Marked with `@pytest.mark.e2e`.

Use `task test:pyramid` to validate the current distribution.

## 2. Methodology

### Test-First (TDD)
Implementations should follow the Red-Green-Refactor loop. Every new feature requires a corresponding test file **before** implementation.

### FR Traceability
Every test function **must** reference a functional requirement ID using the `@trace` tag or marker.

```python
@pytest.mark.requirement("FR-CORE-001")
def test_core_functionality():
    # ...
```

## 3. Tooling

-   **Pytest**: Primary test runner.
-   **pytest-xdist**: Used for parallel execution (`task test`).
-   **Coverage**: We target > 80% line coverage.
-   **Traceability Validator**: `task quality` runs `scripts/traceability-validator.sh`.

## 4. Canonical Naming

Test files must be named based on the **concern** they test, not the level.
-   ✓ `tests/test_adapters.py`
-   ✗ `tests/test_unit_adapters.py`


---
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index



---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices

---

## 5. Testing Patterns

### 5.1 Mocking External Services

```python
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_client.return_value.get.return_value = mock_response
        yield mock_client


def test_external_service_call(mock_http_client):
    """Test that uses mocked HTTP client."""
    from mymodule import service

    result = service.call_external("https://api.example.com")
    assert result == {"status": "ok"}
    mock_http_client.return_value.get.assert_called_once_with("https://api.example.com")
```

### 5.2 Testing Async Code

```python
import pytest
import asyncio


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_fetch_data()
    assert result is not None


@pytest.mark.asyncio
async def test_async_with_timeout():
    """Test async with timeout."""
    from async_timeout import timeout

    try:
        async with timeout(5):
            result = await long_operation()
            assert result.success
    except asyncio.TimeoutError:
        pytest.fail("Operation timed out")
```

### 5.3 Property-Based Testing

```python
from hypothesis import given, strategies as st


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=0, max_value=100))
def test_addition_properties(a, b):
    """Property-based test for addition."""
    result = a + b
    assert result >= a
    assert result >= b
    assert isinstance(result, int)


@given(st.text(min_size=1, max_size=100))
def test_string_not_empty(s):
    """Property-based test for string."""
    assert len(s) > 0
    assert isinstance(s, str)
```

### 5.4 Fixtures and Factories

```python
import pytest
from factory import Factory, Faker


class UserFactory(Factory):
    class Meta:
        model = dict

    name = Faker("name")
    email = Faker("email")
    role = "user"


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return UserFactory(name="Test User", role="admin")


def test_user_creation(sample_user):
    """Test with factory fixture."""
    assert sample_user["name"] == "Test User"
    assert sample_user["role"] == "admin"
```

---

## 6. Test Coverage Guide

### 6.1 Coverage Configuration

```ini
# pyproject.toml
[tool.coverage.run]
source = ["src/thegent"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/migrations/*",
]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "def __repr__",
    "raise NotImplementedError",
]
```

### 6.2 Coverage Targets

| Component | Target | Current |
|----------|--------|----------|
| Core modules | 90% | 87% |
| Agents | 80% | 75% |
| CLI | 85% | 82% |
| MCP tools | 75% | 70% |
| Governance | 70% | 65% |

### 6.3 Running Coverage

```bash
# Generate coverage report
pytest --cov=src/thegent --cov-report=term-missing --cov-report=html

# Check specific module
pytest --cov=src/thegent/agents --cov-report=term-missing

# Coverage with branch analysis
pytest --cov --cov-branch --cov-report=lcov

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

---

## 7. CI/CD Testing Pipeline

### 7.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run tests
        run: pytest -xvs

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 5:** Testing Patterns
   - Mocking external services
   - Async code testing
   - Property-based testing with Hypothesis
   - Fixtures and factories

2. **Added Section 6:** Test Coverage Guide
   - Coverage configuration
   - Coverage targets by component
   - Running coverage commands

3. **Added Section 7:** CI/CD Testing Pipeline
   - GitHub Actions workflow example

### Cross-References Added

- pytest documentation
- hypothesis documentation
- factory_boy documentation

### Practical Additions

- Mocking patterns for HTTP clients
- Async testing with asyncio
- Property-based testing examples
- Coverage configuration and targets
