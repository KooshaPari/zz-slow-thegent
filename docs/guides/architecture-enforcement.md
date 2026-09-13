# Architecture Enforcement Guide

## Overview

All Python projects in the portfolio use **import-linter** to enforce hexagonal architecture layer boundaries. This ensures domain logic stays pure, application logic doesn't depend on infrastructure, and dependencies always point inward.

## How It Works

### The Hexagonal Layers

```
+---------------------------------------------------+
|  infrastructure/   (outermost -- config, DI, boot) |
|  +-----------------------------------------------+ |
|  |  adapters/      (driving + driven)            | |
|  |  +-------------------------------------------+ | |
|  |  |  application/  (use cases, orchestration) | | |
|  |  |  +---------------------------------------+ | | |
|  |  |  |  domain/     (pure business logic)    | | | |
|  |  |  +---------------------------------------+ | | |
|  |  +-------------------------------------------+ | |
|  +-----------------------------------------------+ |
+---------------------------------------------------+
```

**Dependency rule**: Arrows point inward only. An inner layer NEVER imports from an outer layer.

| Layer          | Can Import From               | Cannot Import From                    |
| -------------- | ----------------------------- | ------------------------------------- |
| domain         | stdlib, third-party only      | application, adapters, infrastructure |
| application    | domain                        | adapters, infrastructure              |
| adapters       | domain, application           | infrastructure                        |
| infrastructure | domain, application, adapters | (unrestricted)                        |

### import-linter Configuration

Each project has an `.importlinter` file at its root defining three contracts:

1. **hexagonal-layers** (type: `layers`) -- Enforces the overall layer ordering
2. **domain-independence** (type: `forbidden`) -- Blocks domain from importing other layers
3. **application-no-adapters** (type: `forbidden`) -- Blocks application from importing adapters/infrastructure

### Running the Check

```bash
# From any project root:
task lint:architecture

# Or directly:
import-linter
```

### CI Integration

The `lint:architecture` task is included in the quality gate pipeline. It runs alongside lint, typecheck, and tests.

## Reading Violation Errors

When import-linter finds a violation, it prints output like:

```
=============
import-linter
=============

CONTRACTS

Hexagonal architecture layer enforcement     BROKEN
Domain layer must not import from other layers  BROKEN

Broken contracts
----------------

Hexagonal architecture layer enforcement
-----------------------------------------

thegent.domain.agents.base is not allowed to import thegent.adapters.driving.cli
- thegent.domain.agents.base -> thegent.adapters.driving.cli (l. 5)

Domain layer must not import from other layers
----------------------------------------------

thegent.domain.models -> thegent.infrastructure.config
- thegent.domain.models (l. 3): import thegent.infrastructure.config
```

### How to Read This

- **Contract name** tells you WHICH rule was broken
- **Module path** tells you WHERE the violation is (`thegent.domain.agents.base`)
- **Arrow** tells you the DIRECTION of the illegal import (`-> thegent.adapters.driving.cli`)
- **Line number** tells you EXACTLY where (`l. 5`)

## How to Fix Violations

### Pattern 1: Domain imports infrastructure (most common)

**Problem**: Domain code imports config, database, or API client directly.

```python
# domain/scoring.py -- VIOLATION
from job_hunter.infrastructure.config import Settings


class Scorer:
    def __init__(self):
        self.settings = Settings()  # domain depends on infrastructure!
```

**Fix**: Use dependency injection. Domain defines a Protocol, infrastructure provides the implementation.

```python
# domain/ports.py
from typing import Protocol


class ScoringConfig(Protocol):
    min_score: float
    weights: dict[str, float]


# domain/scoring.py -- CLEAN
from job_hunter.domain.ports import ScoringConfig


class Scorer:
    def __init__(self, config: ScoringConfig):
        self.config = config  # injected, no infrastructure import
```

### Pattern 2: Application imports adapters

**Problem**: Use case code imports a specific adapter implementation.

```python
# application/search_jobs.py -- VIOLATION
from job_hunter.adapters.driven.scrapers.linkedin import LinkedInScraper


class SearchJobsUseCase:
    def execute(self):
        scraper = LinkedInScraper()  # coupled to specific adapter!
```

**Fix**: Application depends on domain ports, not adapter implementations.

```python
# domain/ports.py
class JobSearcher(Protocol):
    def search(self, query: str) -> list[Job]: ...


# application/search_jobs.py -- CLEAN
from job_hunter.domain.ports import JobSearcher


class SearchJobsUseCase:
    def __init__(self, searcher: JobSearcher):
        self.searcher = searcher  # any implementation works
```

### Pattern 3: Circular layer dependency

**Problem**: Two modules in different layers import each other.

**Fix**: Extract the shared concept into the innermost layer that both depend on. Usually this means creating a Protocol in domain/ that both layers reference.

## Adding import-linter to a New Project

1. Create `.importlinter` at the project root:

```ini
[importlinter]
root_packages =
    your_package

[importlinter:contract:hexagonal-layers]
name = Hexagonal architecture layer enforcement
type = layers
layers =
    your_package.infrastructure
    your_package.adapters
    your_package.application
    your_package.domain

[importlinter:contract:domain-independence]
name = Domain layer must not import from other layers
type = forbidden
source_modules =
    your_package.domain
forbidden_modules =
    your_package.application
    your_package.adapters
    your_package.infrastructure

[importlinter:contract:application-no-adapters]
name = Application layer must not import from adapters or infrastructure
type = forbidden
source_modules =
    your_package.application
forbidden_modules =
    your_package.adapters
    your_package.infrastructure
```

2. Add `import-linter` to dev dependencies in `pyproject.toml`
3. Add `lint:architecture` task to `Taskfile.yml`
4. Create the layer directories with `__init__.py` files

## Coexistence with tach

Some projects (e.g. thegent) also use `tach` for module-level boundary enforcement. The two tools complement each other:

- **tach** enforces boundaries between specific modules (e.g., `agents` cannot import `contracts`)
- **import-linter** enforces layer-level boundaries (e.g., `domain` cannot import `adapters`)

Both can run in the same project. `tach` is more granular; import-linter is more structural.

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

## 7. Common Violations and Fixes

### 7.1 Domain Importing Application

**Violation:**

```
domain/service.py imports application/use_cases.py
```

**Fix:** Move the shared logic to domain or create an interface in domain that application implements.

```python
# Before (violation)
from application.use_cases import CreateUserUseCase

# After (correct)
from domain.ports import UserRepository
from application.dependencies import get_user_repository
```

### 7.2 Application Importing Infrastructure

**Violation:**

```
application/service.py imports infrastructure/email.py
```

**Fix:** Use dependency injection to inject the email service.

```python
# Before (violation)
from infrastructure.email import EmailService


class UserService:
    def __init__(self):
        self.email = EmailService()


# After (correct)
from domain.ports import EmailPort


class UserService:
    def __init__(self, email_port: EmailPort):
        self.email = email_port  # Injected
```

### 7.3 Adapter Importing Infrastructure

**Violation:**

```
adapters/http.py imports infrastructure/config.py
```

**Fix:** This is allowed, but prefer depending on domain interfaces.

---

## 8. Creating New Layers

### 8.1 Adding a New Domain Object

```python
# domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Pure business entity - no framework dependencies."""

    id: Optional[str] = None
    name: str = ""
    email: str = ""
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    def activate(self):
        """Business logic stays in domain."""
        self.updated_at = datetime.utcnow()

    def can_delete(self) -> bool:
        """Logic that could be tested in isolation."""
        return self.created_at < datetime.utcnow() - timedelta(days=30)
```

### 8.2 Adding a New Application Service

```python
# application/services/user_service.py
from typing import Protocol
from domain.entities import User


class UserRepository(Protocol):
    """Domain defines the interface."""

    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> User: ...


class UserService:
    """Application service - orchestrates domain objects."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, name: str, email: str) -> User:
        """Use case - coordinates domain logic."""
        user = User(name=name, email=email)
        self.repo.save(user)
        return user
```

### 8.3 Adding a New Adapter

```python
# adapters/persistence/sqlalchemy_user_repository.py
from domain.entities import User
from application.services.user_service import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    """Infrastructure adapter - implements domain interface."""

    def __init__(self, session):
        self.session = session

    def save(self, user: User) -> None:
        """Implements the protocol."""
        orm_user = UserOrm(id=user.id, name=user.name, email=user.email)
        self.session.add(orm_user)

    def find_by_id(self, user_id: str) -> User:
        orm_user = self.session.query(UserOrm).filter_by(id=user_id).first()
        if orm_user:
            return User(id=orm_user.id, name=orm_user.name, email=orm_user.email)
        return None
```

---

## 9. Import-Linter Configuration Reference

### 9.1 Full Configuration

```json
{
  "importlinter": {
    "strict": true,
    "hide_context": false,
    "pep585_imports": "runtime"
  },
  "layers": [
    {
      "name": "domain-independence",
      "selector": "domain",
      "type": "forbidden",
      "forbidden": ["application", "adapters", "infrastructure"],
      "external-packages": ["dataclasses", "datetime"]
    },
    {
      "name": "hexagonal-layers",
      "type": "layers",
      "layers": ["domain", "application", "adapters", "infrastructure"]
    },
    {
      "name": "application-no-adapters",
      "selector": "application",
      "type": "forbidden",
      "forbidden": ["adapters", "infrastructure"]
    }
  ]
}
```

### 9.2 Running with Verbose Output

```bash
# See which modules are in each layer
import-linter --verbose

# Check specific layer
import-linter --layer hexagonal-layers

# Generate DOT graph
import-linter --output-format dot > architecture.dot
```

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 7:** Common Violations and Fixes
   - Domain importing application
   - Application importing infrastructure
   - Adapter importing infrastructure

2. **Added Section 8:** Creating New Layers
   - New domain object example
   - New application service example
   - New adapter example

3. **Added Section 9:** Import-Linter Configuration Reference
   - Full configuration example
   - Verbose output options

### Cross-References Added

- import-linter documentation
- Dependency injection patterns

### Practical Additions

- Real code examples for each layer
- Step-by-step guide for adding new components
- Configuration reference
