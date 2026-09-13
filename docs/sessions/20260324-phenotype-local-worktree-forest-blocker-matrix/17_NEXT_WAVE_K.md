# 17_NEXT_WAVE_K — next 25 items (Waves 1-8 sequence)

**Follows** `07`–`16`. **Snapshot:** 2026-03-24. **Intent:** Full XDD Mastery (TDD/SDD/BDD).

## Slice 1 — TDD & Unit Testing (8)

1. **Red**: Write failing tests for `ModelSelector.tsx` updates.
2. **Green**: Implement the minimal fix to pass tests.
3. **Refactor**: Clean up the code while keeping tests green.
4. **Coverage**: Ensure `vitest` coverage >= 90% for all units.
5. **Fast**: Optimize test execution time (< 100ms per test).
6. **Isolated**: Audit tests for global state pollution.
7. **Mock**: Use `msw` to mock all external API calls.
8. **Assert**: Standardize `expect` assertions across the org.

## Slice 2 — SDD & Schema-Driven (8)

9. **OpenAPI**: Standardize `openapi.json` for all internal services.
10. **Zod**: Create `Zod` schemas for all incoming `LocalBus` events.
11. **Client**: Generate `TypeScript` clients from `OpenAPI` specs.
12. **Contract**: Verify `LocalBusEnvelope` against the schema.
13. **API**: Verify API responses match the published schema.
14. **Database**: Audit `Drizzle` schemas for field consistency.
15. **Proto**: Audit `Protobuf` definitions for `gRPC` services.
16. **Version**: Implement schema versioning and migration rules.

## Slice 3 — BDD & User-Centric (8)

17. **Feature**: Create `gherkin` style feature files for `heliosApp`.
18. **Scenarios**: Define 'Given-When-Then' scenarios for `Lane` creation.
19. **Playwright**: Implement `BDD` tests using `Cucumber` or `Playwright`.
20. **Storybook**: Document UI components with user-stories.
21. **A11y**: Verify accessibility for all user-centric scenarios.
22. **User**: Verify 'user satisfaction' with new UI behavior.
23. **UAT**: Define 'Acceptance Criteria' for all PRs.
24. **Metrics**: Track 'Time to First Interaction' for all features.

## Slice 4 — Meta (1)

25. **Task Update**: Record XDD progress in `ACTIVE_BACKLOG.md`.
