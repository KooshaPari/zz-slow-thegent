# Implementation Strategy

Approach:

- Keep the existing repo-specific tasks intact.
- Refine the top-level common tasks so they detect the repo's manifests at runtime.
- Use shell guards so each task is a no-op for unsupported surfaces.

Rationale:

- This repo is polyglot, so a single hardcoded command would be brittle.
- The Taskfile should stay useful as the repo changes over time.
