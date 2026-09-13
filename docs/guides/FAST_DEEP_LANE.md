# Fast/Deep/Gate Test Lanes

<!-- @trace WL-134 B90-W3-C2 -->

## Overview

Tests are organized into three lanes: fast, deep, and gate. This separation ensures the
default development loop stays under 30 seconds while allowing comprehensive integration
and E2E tests to run on demand or in nightly CI.

## Fast Lane (default)

Runs automatically. Excludes `@pytest.mark.deep` and `@pytest.mark.slow` tests.
Target: < 30s total.
Command: `uv run pytest` or `task test:`
Config: `pytest-fast.ini` — `addopts = -m "not slow and not integration and not e2e and not load" --exitfirst -q`

The fast lane is the default developer feedback loop. All tests NOT marked with slow,
integration, e2e, or load markers run here.

## Deep Lane

Opt-in. Runs integration/E2E tests marked with `@pytest.mark.deep`.
Command: `task test:deep` or `uv run pytest -m deep`

Deep tests may require external services, databases, or long-running computation. They
are not expected to complete within the 30-second fast-lane budget.

## Gate Lane

Pre-promotion gate. Runs tests marked `@pytest.mark.gate`.
Command: `task test:gate`

The gate lane runs fast lane first, then deep lane. A failure in the fast lane aborts
before the deep lane executes.

## Opt-in Patterns

```bash
# Run everything including deep
PYTEST_ADDOPTS="-m 'not slow'" uv run pytest

# Run only fast tests explicitly
uv run pytest -m fast

# Run deep + gate only
uv run pytest -m "deep or gate"

# Run the fast-lane config explicitly (fail-fast enabled)
uv run pytest -c pytest-fast.ini
```

## Marking Tests

```python
import pytest


@pytest.mark.fast
def test_unit_thing(): ...


@pytest.mark.deep
def test_integration_thing(): ...


@pytest.mark.gate
def test_gate_thing(): ...


@pytest.mark.slow
def test_expensive_computation(): ...
```

## Configuration Files

- `pytest-fast.ini` — fast lane config with `addopts = -m "not slow and not integration and not e2e and not load" --exitfirst -q`
- `pyproject.toml` — canonical marker definitions under `[tool.pytest.ini_options]`
- `Taskfile.yml` — `test:fast-lane`, `test:deep`, `test:gate`, `test:nightly-lane` tasks

## Lane Summary

| Lane | Trigger | Markers included | Target time |
|------|---------|-----------------|-------------|
| fast | Default / CI fast | not slow, not integration, not e2e, not load | < 30s |
| deep | On demand / nightly | `@pytest.mark.deep` | < 5 min |
| gate | Pre-promotion | fast then deep | < 6 min |
| nightly | Nightly CI | slow or integration or e2e or load | Unrestricted |
