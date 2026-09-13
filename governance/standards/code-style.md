# Code Style Standards

## General Principles

- **Readability first**: Code is read more often than written
- **Consistency**: Match existing patterns in the codebase
- **Clarity over cleverness**: Explicit beats implicit
- **DRY**: Don't Repeat Yourself
- **SOLID principles**: Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion

## Python

### Line Length

- **Limit**: 100 characters (hard limit)
- **Exceptions**: URLs, long strings that cannot be split

### Imports

```python
# ✅ Good: Grouped and sorted
import os
import sys
from pathlib import Path

from typing import Optional, Dict, List

import requests
from pydantic import BaseModel, Field

from .models import User
from .utils import helper_function
```

```python
# ❌ Bad: Unsorted, wildcard imports
from os import *
import sys, os
from . import *
```

### Naming

| Type | Style | Example |
|------|-------|---------|
| Module | `snake_case` | `user_service.py` |
| Class | `PascalCase` | `UserService` |
| Function | `snake_case` | `get_user_by_id()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES = 3` |
| Private | `_leading_underscore` | `_internal_method()` |

### Functions

```python
# ✅ Good: Type hints, docstring, manageable size
def process_user_data(
    user_id: int,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Process user data and return formatted dictionary.

    Args:
        user_id: The user's ID
        include_details: Whether to include full details

    Returns:
        Dictionary with user data

    Raises:
        UserNotFoundError: If user doesn't exist
    """
    if user_id <= 0:
        raise ValueError("user_id must be positive")

    user = get_user(user_id)
    return format_user_data(user, include_details)
```

```python
# ❌ Bad: No types, no docstring, too complex
def process_user_data(user_id, include_details=False):
    if user_id <= 0:
        user = None
    else:
        user = get_user(user_id)
        if include_details:
            details = get_user_details(user_id)
            if details:
                user["details"] = details

    return user
```

### Classes

```python
# ✅ Good: Clear, single responsibility, inheritance
class UserService:
    """Service for user operations."""

    def __init__(self, db: Database, cache: Cache):
        self.db = db
        self.cache = cache

    def get_user(self, user_id: int) -> Optional[User]:
        """Fetch user by ID, checking cache first."""
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        user = self.db.query(User).filter_by(id=user_id).first()
        if user:
            self.cache.set(f"user:{user_id}", user)
        return user
```

### Comments

```python
# ✅ Good: Explains WHY, not WHAT
def calculate_discount(base_price: float, customer_tier: str) -> float:
    # Premium customers get 20% discount; standard get 5%
    # This encourages loyalty and higher spending
    discount_rate = 0.20 if customer_tier == "premium" else 0.05
    return base_price * (1 - discount_rate)
```

```python
# ❌ Bad: Explains WHAT (obvious from code)
def calculate_discount(base_price, customer_tier):
    # Check if customer_tier is premium
    if customer_tier == "premium":
        # Set discount to 20%
        discount = 0.20
    else:
        # Set discount to 5%
        discount = 0.05
    # Return price minus discount
    return base_price * (1 - discount)
```

### Logging

```python
# ✅ Good: Structured, informative
import logging

logger = logging.getLogger(__name__)

logger.info(
    "User login attempt",
    extra={
        "user_id": user_id,
        "timestamp": datetime.now(),
    },
)

logger.error(
    "Database connection failed",
    exc_info=True,
    extra={
        "host": db_host,
        "port": db_port,
    },
)
```

```python
# ❌ Bad: Unstructured, unhelpful
print("User logged in")  # No context
logger.debug("stuff happening")  # Too vague
```

### Testing

See [testing-standards.md](testing-standards.md)

## TypeScript/JavaScript

### Line Length

- **Limit**: 100 characters
- **Exceptions**: URLs, long strings

### Imports

```typescript
// ✅ Good: Grouped, sorted
import { Router } from 'express';
import fs from 'fs';

import { z } from 'zod';
import axios from 'axios';

import { User } from './types';
import { userService } from './services';
```

### Naming

| Type | Style | Example |
|------|-------|---------|
| File | `kebab-case` | `user-service.ts` |
| Class | `PascalCase` | `UserService` |
| Function | `camelCase` | `getUserById()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| React Component | `PascalCase` | `UserProfile` |

### Types & Interfaces

```typescript
// ✅ Good: Explicit types, clear contracts
interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

type Result<T> = { success: true; data: T } | { success: false; error: string };

async function getUser(userId: number): Promise<User | null> {
  const user = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
  return user || null;
}
```

```typescript
// ❌ Bad: `any`, implicit types
async function getUser(userId: any): Promise<any> {
  const user: any = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
  return user;
}
```

### Async/Await

```typescript
// ✅ Good: Proper error handling
async function fetchData(url: string): Promise<void> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    console.log(data);
  } catch (error) {
    logger.error('Failed to fetch data', { url, error });
    throw error;
  }
}
```

```typescript
// ❌ Bad: Swallowing errors, missing types
async function fetchData(url) {
  const response = await fetch(url);
  const data = await response.json();
  return data;
}
```

## Go

### Naming

```go
// ✅ Good: Clear, idiomatic
func GetUserByID(id int) (*User, error)
func (s *UserService) CreateUser(name string) (*User, error)
type UserRepository interface {
    GetByID(ctx context.Context, id int) (*User, error)
}
```

### Errors

```go
// ✅ Good: Explicit error handling
func ProcessUser(userID int) error {
    user, err := repo.GetUser(userID)
    if err != nil {
        return fmt.Errorf("failed to fetch user %d: %w", userID, err)
    }

    return nil
}
```

## Rust

### Naming

```rust
// ✅ Good: Idiomatic Rust
pub struct UserService { }
pub fn get_user_by_id(id: i32) -> Result<User, UserError>
impl UserService {
    pub fn new() -> Self { }
}
```

## File Organization

### Module Structure

```
src/
├── main.rs                      # Entry point
├── lib.rs                       # Library root
├── models/                      # Data structures
│   ├── mod.rs
│   ├── user.rs
│   └── config.rs
├── services/                    # Business logic
│   ├── mod.rs
│   ├── user_service.rs
│   └── config_service.rs
├── infrastructure/              # External adapters
│   ├── mod.rs
│   ├── db.rs
│   └── cache.rs
└── utils/                       # Shared utilities
    ├── mod.rs
    └── helpers.rs
```

### File Size Limits

- **Target**: ≤350 lines per file
- **Hard limit**: ≤500 lines per file
- When approaching limit: split into submodule
- See AGENTS.md § 5 for decomposition patterns

## Documentation

### Docstrings/Comments

All public APIs must have documentation:

```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    years: int,
) -> float:
    """
    Calculate compound interest.

    Compounds annually using the formula: A = P(1 + r)^n

    Args:
        principal: Initial amount in currency units
        rate: Annual interest rate as decimal (0.05 = 5%)
        years: Number of years to compound

    Returns:
        Final amount after compound interest

    Examples:
        >>> calculate_compound_interest(1000, 0.05, 2)
        1102.5

    Raises:
        ValueError: If principal or years is negative
    """
    if principal < 0 or years < 0:
        raise ValueError("principal and years must be non-negative")
    return principal * (1 + rate) ** years
```

### README.md

Every major component should have a README:

- Purpose and scope
- Installation/setup
- Usage examples
- Testing instructions
- Contributing guidelines

## Linting & Formatting

Run these before committing:

```bash
# Python
ruff check . --fix
black . --line-length 100

# TypeScript
eslint . --fix
prettier . --write

# Go
gofmt -w .
golangci-lint run ./...

# Rust
cargo fmt
cargo clippy -- -D warnings
```

## No AI Slop

Avoid:
- Placeholder TODOs: "TODO: implement", "TODO: add"
- Lorem ipsum filler text
- Generic comments: "This function does...", "This is a helper..."
- Placeholder domains in non-test code (example.com, localhost)
- LLM leakage: "As an AI", "I cannot", "I apologize"

## Configuration Files

### pyproject.toml

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "target": "ES2020"
  }
}
```

## Related Documents

- [commit-conventions.md](commit-conventions.md) — Commit message format
- [pr-standards.md](pr-standards.md) — Pull request standards
- [testing-standards.md](testing-standards.md) — Testing requirements
