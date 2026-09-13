# Agent-B Batch Status (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21

## WL-107

- Status: blocked
- Done this pass: wrote implementation-ready plan artifact.
- Files changed:
  - docs/plans/2026-02-21-WL-107-review-read-only-plan.md
- Validation commands run:
  - python -m py_compile src/thegent/agents/base.py src/thegent/agents/direct_agents.py src/thegent/agents/codex_proxy.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py tests/test_wl108_wl114_slices.py

## WL-108

- Status: in-progress
- Done this pass:
  - factored payload context usage into helper (`_append_context_usage`) and wired run payload through helper.
  - added focused helper tests.
- Files changed:
  - src/thegent/cli/commands/impl.py
  - tests/test_wl108_wl114_slices.py
- Validation commands run:
  - python -m py_compile src/thegent/cli/commands/impl.py tests/test_wl108_wl114_slices.py
  - python - <<'PY' ... smoke check for `_append_context_usage` ... PY

## WL-109

- Status: blocked
- Done this pass: wrote implementation-ready MCP LSP tools plan artifact.
- Files changed:
  - docs/plans/2026-02-21-WL-109-mcp-lsp-tools-plan.md
- Validation commands run:
  - python -m py_compile src/thegent/agents/base.py src/thegent/agents/direct_agents.py src/thegent/agents/codex_proxy.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py tests/test_wl108_wl114_slices.py

## WL-110

- Status: blocked
- Done this pass: wrote implementation-ready stable resume API plan artifact.
- Files changed:
  - docs/plans/2026-02-21-WL-110-resume-stable-api-plan.md
- Validation commands run:
  - python -m py_compile src/thegent/agents/base.py src/thegent/agents/direct_agents.py src/thegent/agents/codex_proxy.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py tests/test_wl108_wl114_slices.py

## WL-114

- Status: in-progress
- Done this pass:
  - added repeatable `--image` option to run command surfaces.
  - added image input validation (HTTPS URL or local png/jpg/jpeg/webp/gif).
  - wired codex command forwarding with repeatable `--image` flags in direct/codex-proxy runners.
  - added focused tests and follow-up plan for remaining scope.
- Files changed:
  - src/thegent/agents/base.py
  - src/thegent/agents/direct_agents.py
  - src/thegent/agents/codex_proxy.py
  - src/thegent/cli/apps/run.py
  - src/thegent/cli/commands/cli.py
  - src/thegent/cli/commands/impl.py
  - tests/test_unit_direct_agents.py
  - tests/test_unit_codex_proxy.py
  - tests/test_wl108_wl114_slices.py
  - docs/plans/2026-02-21-WL-114-image-followups-plan.md
- Validation commands run:
  - python -m py_compile src/thegent/agents/base.py src/thegent/agents/direct_agents.py src/thegent/agents/codex_proxy.py src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py tests/test_wl108_wl114_slices.py
  - python - <<'PY' ... smoke check for `_normalize_image_paths` and codex `--image` args ... PY

## Notes

- `pytest` execution is currently blocked in this environment due missing plugin dependency: `pytest_asyncio`.
