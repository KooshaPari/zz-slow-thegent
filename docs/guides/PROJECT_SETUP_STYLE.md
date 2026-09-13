# Project Setup Style (Vercel/ai Inspired)

This repository uses a setup style focused on fast local iteration and strong quality gates.

## Canonical Commands

- `task build`
- `task test`
- `task lint`
- `task quality`
- `task check` (full quality gate)
- `task release:prep` (changelog + release-readiness gate)

## Operating Rules

- Keep `CHANGELOG.md` current under `## [Unreleased]`.
- Keep docs and examples aligned with behavior changes.
- Use scoped checks while iterating, then run full `task quality` before push.

## Release-Prep Flow

1. `task changelog:check`
2. `task check`
3. `task ci:local:pre-push`
