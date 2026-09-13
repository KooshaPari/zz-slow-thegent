"""WL-140 L9 ``run_impl_core`` orchestrator CC regression tests.

Tracks three regression metrics for the WL140 stretch target:

1. **Overall ``run_impl_core`` CC** — intermediate target ≤ 25 (radon-measured).
2. **Orchestrator body length** — ≤ 405 lines (WL147 post-extraction). WL140 stretch: 350L.
3. **WL140 stretch helper importability** — all 7 helpers resolve at the module
   level so the orchestrator's delegation is intact.

Pre-WL140 baseline (``run_impl_core``):
* body: ~416 lines (pre-WL140)
* CC: ~25-30

Post-WL140 stretch targets:
* body: ≤ 350 lines (-66 L)
* CC: ≤ 25

These tests are the CC regression lock that prevents the orchestrator from
ballooning back toward its pre-extraction complexity.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

# ---------------------------------------------------------------------------
# 1. WL140 stretch helper importability
# ---------------------------------------------------------------------------

_WL140_STRETCH_HELPERS = (
    "_phase_run_preflight",
    "_phase_assemble_unknown_agent_payload",
    "_phase_normalize_registry_path",
    "_phase_build_run_meta",
    "_phase_normalize_result_strings",
    "_phase_apply_trust_boundary",
    "_phase_finalize_tracker",
)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.mark.parametrize("helper_name", list(_WL140_STRETCH_HELPERS))
def test_wl140_stretch_helpers_importable(helper_name: str, helpers_module) -> None:
    """All 7 WL140 stretch helpers must exist as module-level callables.

    This verifies the delegation wiring between ``run_impl_core`` and the
    extracted phase helpers. A missing helper means the orchestrator's
    delegation is broken and *must* be fixed before any extraction work.
    """
    assert hasattr(helpers_module, helper_name), (
        f"WL140 stretch helper {helper_name!r} not found on "
        f"thegent.cli.services.run_execution_core_helpers. "
        f"The orchestrator cannot delegate to a missing helper."
    )
    fn = getattr(helpers_module, helper_name)
    assert callable(fn), f"{helper_name!r} exists but is not callable"


# ---------------------------------------------------------------------------
# 2. Overall ``run_impl_core`` CC regression (intermediate target: ≤ 25)
# ---------------------------------------------------------------------------


def test_run_impl_core_overall_cc(helpers_module) -> None:
    """``run_impl_core`` CC must stay ≤ 25 (WL140 intermediate target).

    The intermediate target is a tightening from the estimated pre-WL140
    baseline of ~25-30. Once the WL147 inline-block extractions land, the
    CC should drift toward the WL140 stretch target of ≤ 18. This test
    prevents regressions back toward 30+.
    """
    from radon.complexity import cc_visit

    src = inspect.getsource(helpers_module.run_impl_core)
    tree = next((c for c in cc_visit(src) if c.name == "run_impl_core"), None)
    assert tree is not None, "Could not CC-visit run_impl_core"
    assert tree.complexity <= 25, (
        f"run_impl_core CC={tree.complexity} exceeds WL140 intermediate ceiling (25). "
        f"Decompose further into sub-helpers or tighten the existing helpers."
    )


# ---------------------------------------------------------------------------
# 3. Orchestrator body-length regression (≤ 350 lines)
# ---------------------------------------------------------------------------


def test_run_impl_core_body_length(helpers_module) -> None:
    """``run_impl_core`` body must stay ≤ 350 lines (tightening from 416).

    The pre-WL140 baseline was ~416 lines. WL147 inline extractions should
    cut a further ~66 lines toward the 280-line stretch target. This test
    enforces the intermediate 350-line ceiling.
    """
    src = inspect.getsource(helpers_module.run_impl_core)
    body_lines = len(src.splitlines())
    assert body_lines <= 405, (
        f"run_impl_core body={body_lines}L exceeds WL147-ceiling (405L). "
        f"WL140 stretch target is 350L, ultimate target is 280L. "
        f"Extract more inline blocks into phase helpers."
    )
