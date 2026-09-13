# Testing Standards

## Test-First Mandate (TDD)

All code MUST be tested before or during implementation:

1. **New modules**: Test file MUST exist before implementation file
2. **Bug fixes**: Failing test MUST be written before the fix
3. **Refactors**: Existing tests must pass before AND after changes

## Test Pyramid

Target test distribution:

| Type        | Target | Tolerance |
| ----------- | ------ | --------- |
| Unit        | 70%    | ±5%       |
| Integration | 20%    | ±5%       |
| E2E         | 10%    | ±5%       |

## Test File Organization

### Naming Conventions

```
# Python
tests/
├── unit/
│   ├── test_user_service.py
│   ├── test_auth_handler.py
│   └── test_validators.py
├── integration/
│   ├── test_auth_integration.py
│   ├── test_db_integration.py
│   └── test_external_api_integration.py
├── e2e/
│   ├── test_user_flow_e2e.py
│   ├── test_auth_flow_e2e.py
│   └── conftest.py
└── fixtures/
    ├── factories.py
    ├── seeds.py
    └── mocks.py

# TypeScript
tests/
├── unit/
│   ├── UserService.test.ts
│   ├── AuthHandler.test.ts
│   └── validators.test.ts
├── integration/
│   ├── auth.integration.test.ts
│   ├── database.integration.test.ts
│   └── api.integration.test.ts
├── e2e/
│   ├── userFlow.e2e.test.ts
│   └── authFlow.e2e.test.ts
└── fixtures/
    ├── factories.ts
    ├── seeds.ts
    └── mocks.ts
```

### File Naming Rules

- **Unit tests**: `test_<module>_<class/function>.py` or `<Module>.test.ts`
- **Integration tests**: `test_<domain>_integration.py` or `<domain>.integration.test.ts`
- **E2E tests**: `test_<user_flow>_e2e.py` or `<userFlow>.e2e.test.ts`

## Functional Requirements (FR) Traceability

**All tests MUST reference an FR ID** to ensure coverage of specifications.

### Marking Tests with FR IDs

```python
# Python: Option 1 — pytest marker
@pytest.mark.requirement("FR-THEGENT-001")
def test_user_can_login():
    pass


# Python: Option 2 — Comment tag
def test_user_can_login():
    """
    Test that user can login with valid credentials.

    Traces to: FR-THEGENT-001
    """
    pass


# Python: Option 3 — Docstring
def test_user_can_login():
    # @trace FR-THEGENT-001
    pass
```

```typescript
// TypeScript: Option 1 — Test name
describe("FR-THEGENT-001: User can login", () => {
  test("should login with valid credentials", () => {
    // ...
  });
});

// TypeScript: Option 2 — JSDoc
/**
 * Test that user can login with valid credentials.
 * @traces FR-THEGENT-001
 */
test("should login with valid credentials", () => {
  // ...
});
```

### FR Coverage Verification

All FRs MUST have corresponding tests:

```bash
# Find all FRs
grep -r "^## FR-" FUNCTIONAL_REQUIREMENTS.md

# Verify test coverage
grep -r "FR-THEGENT-" tests/ | sort | uniq
```

## Unit Tests

### Purpose

- Test individual functions, methods, or classes in isolation
- Fast execution (milliseconds)
- Comprehensive coverage of edge cases

### Structure (AAA Pattern)

```python
# Python
def test_calculate_discount_for_premium_customer():
    # Arrange
    base_price = 100.0
    customer_tier = "premium"

    # Act
    result = calculate_discount(base_price, customer_tier)

    # Assert
    assert result == 80.0  # 20% discount
```

```typescript
// TypeScript
test("should calculate discount for premium customer", () => {
  // Arrange
  const basePrice = 100;
  const customerTier = "premium";

  // Act
  const result = calculateDiscount(basePrice, customerTier);

  // Assert
  expect(result).toBe(80); // 20% discount
});
```

### Mocking

```python
# ✅ Good: Mock external dependencies
from unittest.mock import Mock, patch


def test_get_user_with_cache():
    # Arrange
    mock_db = Mock()
    mock_cache = Mock()
    mock_cache.get.return_value = None  # Cache miss
    mock_db.query.return_value.first.return_value = User(id=1, name="Alice")

    service = UserService(db=mock_db, cache=mock_cache)

    # Act
    user = service.get_user(1)

    # Assert
    assert user.name == "Alice"
    mock_db.query.assert_called_once()
    mock_cache.get.assert_called_once()
```

```python
# ❌ Bad: Testing implementation details
def test_get_user_with_cache():
    service = UserService()
    user = service.get_user(1)
    assert user.name == "Alice"
    # What was actually tested? Internal cache behavior, DB behavior...
```

### Fixtures

```python
# ✅ Good: Reusable fixtures
import pytest


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def user_service(mock_db):
    return UserService(db=mock_db)


def test_get_user(user_service, mock_db):
    # Arrange
    mock_db.query.return_value.first.return_value = User(id=1)

    # Act
    user = user_service.get_user(1)

    # Assert
    assert user.id == 1
```

## Integration Tests

### Purpose

- Test multiple components working together
- Test database operations
- Test API routes/handlers
- Slower than unit tests (seconds)

### Example: Database Integration Test

```python
@pytest.mark.integration
def test_create_and_retrieve_user(db_session):
    """Test creating a user and retrieving it from DB."""
    # Arrange
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # Retrieve
    retrieved = db_session.query(User).filter_by(id=user_id).first()

    # Assert
    assert retrieved.name == "Alice"
    assert retrieved.email == "alice@example.com"
```

### Example: API Integration Test

```python
@pytest.mark.integration
def test_get_user_endpoint(client, db_session):
    """Test GET /api/users/{id} endpoint."""
    # Arrange
    user = User(name="Bob", email="bob@example.com")
    db_session.add(user)
    db_session.commit()

    # Act
    response = client.get(f"/api/users/{user.id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Bob"
```

## E2E Tests

### Purpose

- Test complete user workflows
- Test from user perspective (UI/API calls)
- Slowest tests (seconds to minutes)
- Usually run against staging environment

### Example: Browser E2E Test

```typescript
// With Playwright
test("User can complete login flow", async ({ page }) => {
  // Arrange
  await page.goto("http://localhost:3000/login");

  // Act
  await page.fill('input[name="email"]', "user@example.com");
  await page.fill('input[name="password"]', "password123");
  await page.click('button[type="submit"]');

  // Wait for redirect
  await page.waitForURL("http://localhost:3000/dashboard");

  // Assert
  expect(page.url()).toBe("http://localhost:3000/dashboard");
  await expect(page.locator("h1")).toContainText("Welcome");
});
```

### Example: API E2E Test

```python
@pytest.mark.e2e
def test_complete_user_signup_flow(client):
    """Test complete signup workflow: register → verify → login."""
    # Arrange
    signup_data = {"name": "Charlie", "email": "charlie@example.com", "password": "secure123"}

    # Act: Register
    register_resp = client.post("/api/auth/signup", json=signup_data)
    assert register_resp.status_code == 201
    user_id = register_resp.json()["id"]

    # Act: Verify email
    verify_resp = client.post(f"/api/auth/verify/{user_id}")
    assert verify_resp.status_code == 200

    # Act: Login
    login_resp = client.post(
        "/api/auth/login", json={"email": signup_data["email"], "password": signup_data["password"]}
    )

    # Assert
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()
```

## Running Tests

### Python

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_service.py

# Run specific test function
pytest tests/unit/test_user_service.py::test_get_user

# Run with coverage
pytest --cov=src tests/

# Run only unit tests
pytest tests/unit/

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run with markers
pytest -m integration

# Run excluding markers
pytest -m "not e2e"
```

### TypeScript

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific file
npm test -- UserService.test.ts

# Run with watch mode
npm test -- --watch

# Run only unit tests
npm test -- tests/unit

# Run excluding e2e
npm test -- --testPathIgnorePatterns=e2e
```

## Coverage Requirements

### Minimum Coverage

- **Lines**: 80%
- **Branches**: 75%
- **Functions**: 80%
- **Statements**: 80%

### Coverage Report

```bash
# Generate coverage report
pytest --cov=src --cov-report=html tests/

# View HTML report
open htmlcov/index.html
```

### Coverage Exceptions

Don't test:

- External library code you don't control
- Generated code (migrations, protobuf)
- Thin wrapper functions with obvious behavior
- Vendor code and third-party integrations

## Test Isolation

### Good Practices

```python
# ✅ Good: Tests are independent
def test_create_user_with_valid_data():
    user = create_user(name="Alice")
    assert user.id is not None


def test_create_user_with_invalid_email():
    with pytest.raises(ValueError):
        create_user(name="Bob", email="invalid")
```

```python
# ❌ Bad: Tests have dependencies
def test_create_user():
    global user_id
    user = create_user(name="Alice")
    user_id = user.id
    assert user_id is not None


def test_get_user():
    user = get_user(user_id)  # Depends on test_create_user running first
    assert user.name == "Alice"
```

## Test Data Management

### Factories (Preferred)

```python
# ✅ Good: Use factory for consistent test data
@pytest.fixture
def user_factory():
    def _make_user(**kwargs):
        defaults = {"name": "Test User", "email": "test@example.com"}
        defaults.update(kwargs)
        return User(**defaults)

    return _make_user


def test_get_user(user_factory):
    user = user_factory(name="Alice")
    assert user.name == "Alice"
```

### Seeds (For Large Datasets)

```python
# ✅ Good: Seed for integration tests
@pytest.fixture
def populated_db(db_session):
    """Populate DB with test data."""
    users = [User(name=f"User {i}", email=f"user{i}@example.com") for i in range(100)]
    db_session.add_all(users)
    db_session.commit()
    return db_session
```

## Parametrized Tests

```python
# ✅ Good: Test multiple inputs with one test function
@pytest.mark.parametrize(
    "discount_tier,expected_discount",
    [
        ("premium", 0.20),
        ("standard", 0.05),
        ("none", 0.0),
    ],
)
def test_calculate_discount(discount_tier, expected_discount):
    result = calculate_discount(100, discount_tier)
    expected = 100 * (1 - expected_discount)
    assert result == expected
```

## Assertions

### Best Practices

```python
# ✅ Good: Clear, informative
assert user.name == "Alice", f"Expected name 'Alice', got '{user.name}'"

# ✅ Good: Use assertion helpers
assert response.status_code == 200
assert "error" not in response.json()

# ❌ Bad: Vague assertions
assert user
assert len(response) > 0
```

## Skipping Tests

```python
# Python: Skip with reason
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# TypeScript: Skip test
test.skip("Not implemented yet", () => {
  // ...
});

# Skip on condition
@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10+")
def test_requires_python_310():
    pass
```

## Test Performance

- **Unit tests**: Should complete in <100ms
- **Integration tests**: Should complete in <1s
- **E2E tests**: Should complete in <10s
- **Full suite**: Should complete in <5 minutes

## Continuous Integration

All tests MUST pass in CI:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pytest tests/ --cov=src --cov-report=xml
    coverage report --fail-under=80
```

## Related Documents

- [code-style.md](code-style.md) — Code style standards
- [AGENTS.md](../AGENTS.base.md) — § 7 Test-First Mandate
