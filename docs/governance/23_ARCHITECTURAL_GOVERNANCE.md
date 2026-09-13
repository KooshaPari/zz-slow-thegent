# Architectural Governance & Modernization

**Snapshot:** 2026-03-24. **Policy:** Mandatory for all Phenotype repositories.

## 1. Hexagonal Architecture (Ports & Adapters)

- **Domain-First**: Core business logic must be isolated from external concerns (frameworks, databases, APIs).
- **Ports**: Use interfaces to define required external capabilities (Repository, Bus, FileSystem).
- **Adapters**: Implement ports using specific technologies (Bun.SQLite, Vite, LocalBus).
- **Dependency Rule**: Dependencies must point inward towards the Domain. Infrastructure and UI depend on Domain; Domain depends on nothing but itself.

## 2. Polyrepo Decomposition & Libification

- **Modularization**: Identify and extract reusable logic into shared libraries.
- **Micro-repos**: Favor smaller, focused repositories over large monolithic structures.
- **Productization**: Shared libraries must be treated as products (stable APIs, docs, versioning, tests).
- **Extensibility**: Design for genericism. A library built for `heliosApp` should be intuitively usable by `thegent` or `AgilePlus`.

## 3. Full XDD Mastery (TDD / SDD / BDD)

- **TDD (Test-Driven)**: Write failing unit tests before implementation. Refactor only with green tests.
- **SDD (Schema-Driven)**: Define data contracts (OpenAPI, Zod, Protobuf) before implementation. Generate clients/types from source-of-truth schemas.
- **BDD (Behavior-Driven)**: Define user-facing features using 'Given-When-Then' scenarios. Automate acceptance tests using Playwright/Cucumber.

## 4. Modern Engineering Standards

- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
- **KISS**: Keep It Simple, Stupid. Avoid over-engineering.
- **DRY**: Don't Repeat Yourself. Use libification for reuse.
- **CLEAN**: Clean code, clear naming, explicit error handling, and minimal side effects.
- **Performance**: P50/P95 latency targets are part of the Definition of Done.

## 5. Microservices & Distributed Design

- **Autonomy**: Services must be independently deployable and scalable.
- **Communication**: Favor asynchronous message-passing (`LocalBus`) over synchronous RPC where possible.
- **Resilience**: Implement circuit breakers, retries, and fallbacks for all service-to-service calls.
