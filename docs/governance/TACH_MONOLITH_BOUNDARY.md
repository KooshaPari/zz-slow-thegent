# Tach: monolith boundary (thegent)

## Current state

- **Single Tach module:** `thegent` (`src/thegent/`), `depends_on = []`.
- **`forbid_circular_dependencies = true`** applies only **between** Tach modules. Internal Python import cycles inside `thegent` are **not** split into separate Tach boundaries until the hex extraction work breaks those cycles for real.

## Why not per-layer modules?

Earlier `tach.toml` listed `thegent.cli`, `thegent.routing`, `thegent.models`, etc. The live import graph still has **strongly connected** components across those subtrees, so Tach correctly reported circular dependencies. Declaring layers in config without matching acyclic imports produced a permanently red gate.

## Follow-up (hex program)

When a subtree becomes import-acyclic (or is moved to its own package), add a `[[modules]]` entry and narrow `depends_on` edges. Prefer **extracting** shared types to leaf packages over turning off `forbid_circular_dependencies`.

## `tach check` note

With only one module, `tach check` may print **“No first-party imports were found.”** That is expected: there are no _cross-module_ internal edges until a second package (for example a split-out library) appears under `source_roots`.

## Related

- Architectural target: [`23_ARCHITECTURAL_GOVERNANCE.md`](23_ARCHITECTURAL_GOVERNANCE.md).
- Invariant docs / Vale: [`../research/LANGUAGE_INVARIANTS_AND_VALE_2026-03.md`](../research/LANGUAGE_INVARIANTS_AND_VALE_2026-03.md).
