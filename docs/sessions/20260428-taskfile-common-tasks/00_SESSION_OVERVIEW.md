# Session Overview

Goal: normalize the root `Taskfile.yml` so it exposes the common `build`, `test`, `lint`, and `clean`
tasks while detecting the repo's available language surfaces automatically.

Success criteria:

- `task build`, `task test`, `task lint`, and `task clean` are present.
- The tasks run the appropriate commands for Python, Bun/VitePress, and Rust when those manifests exist.
- The branch is pushed and merged through a PR after validation.
