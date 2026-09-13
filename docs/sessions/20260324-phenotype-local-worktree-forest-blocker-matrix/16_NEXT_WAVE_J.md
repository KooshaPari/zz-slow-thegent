# 16_NEXT_WAVE_J — next 25 items (Waves 1-8 sequence)

**Follows** `07`–`15`. **Snapshot:** 2026-03-24. **Intent:** Hexagonal Architecture & Polyrepo Migration.

## Slice 1 — Hexagonal Domain Audit (8)

1. **Domains**: Identify core business domains in `heliosApp` (PTY, Bus, Settings).
2. **Ports**: Define `InputPort` interfaces for `LocalBus` events.
3. **Adapters**: Isolate `Bun` or `Node` specific code into `Infrastructure` adapters.
4. **Mocking**: Create `MockAdapters` for all external dependencies for testing.
5. **Logic**: Extract domain logic from UI components in `apps/desktop`.
6. **Persistence**: Define generic `Repository` ports for local storage.
7. **Service**: Encapsulate domain use cases into `DomainServices`.
8. **Dependency**: Verify `Infrastructure -> Domain` dependency rule (no circular).

## Slice 2 — Polyrepo Decomposition (8)

9. **Shared**: Identify candidates for extraction into `phenotype-shared`.
10. **Native**: Split `src/thegent/native` into a standalone polyrepo.
11. **Config**: Extract common CI/CD workflows into `phenotypeActions`.
12. **Protocol**: Isolate `LocalBus` protocol definitions into a library.
13. **UI**: Move generic Solid components into a `ui-kit` library.
14. **Type**: Centralize common `TypeScript` definitions into `types-kit`.
15. **CLI**: Split `heliosCLI` from the monorepo into a sibling repo.
16. **Contracts**: Audit `contracts` repo for reusable schema definitions.

## Slice 3 — Libification & Productization (8)

17. **Generic**: Refactor specific adapters into generic libraries.
18. **Publish**: Prepare `libs/` for private npm registry (e.g., Verdaccio).
19. **Versioning**: Implement `Changesets` or `Lerna` for versioning.
20. **Extensibility**: Add `plugin` hooks to `heliosApp` runtime.
21. **Performance**: Audit lib bundle size and tree-shaking.
22. **Docs**: Generate API docs for all extracted libraries.
23. **Test**: Ensure 100% test coverage for all shared libs.
24. **User**: Verify 'developer satisfaction' with new polyrepo layout.

## Slice 4 — Meta (1)

25. **Task Update**: Record decomposition findings in `05_KNOWN_ISSUES.md`.
