"""AUDIT-N+11 parity test — observability drift closure.

Pins the AUDIT-N+11 lane closure: the WL-125 ``summary_mode`` contract on
:func:`thegent.cli.commands.observability_impl._inject_time_constraint` is
restored (the function previously accepted only ``(prompt, timeout)``, which
caused live ``TypeError`` on every ``run_impl_core`` /
``bg_impl_core`` invocation through
:func:`thegent.cli.services.run_execution_core_helpers._inject_time_constraint_local`),
and :func:`_build_observe_summary_trend_scope` is moved out of
``thegent.cli.commands.impl`` into the canonical
:mod:`thegent.cli.commands.observability_impl` surface so the legacy
``__all__`` entry is no longer a phantom local definition.

The lane was scoped from the AUDIT-N+9 → AUDIT-N+10 drift scan that
flagged three residual drift surfaces:
  1. Live TypeError on ``_inject_time_constraint(summary_mode=...)``
     (Finding 2 — CRITICAL).
  2. ``_build_observe_summary_trend_scope`` inline at ``impl.py:508``
     (Finding 1 — HIGH).
  3. A 4-symbol stale observability core in
     ``services/observability.py`` / ``services/run_observe_helpers.py``
     that is dormant (Finding 3 — HIGH, carried forward as AUDIT-N+12
     candidate).

This test class covers the two surfaces that AUDIT-N+11 closed (1 and 2),
pins them against regression, and documents the carried-forward Finding 3
work.
"""

from __future__ import annotations

import inspect
import re

import pytest

from thegent.cli.commands import impl as cli_impl
from thegent.cli.commands import observability_impl
from thegent.cli.services import run_execution_core_helpers


# ---------------------------------------------------------------------------
# AUDIT-N+11 surface contract — `_inject_time_constraint` WL-125 signature
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInjectTimeConstraintSignatureRestored:
    """Pin that ``_inject_time_constraint`` now accepts the WL-125 kwargs."""

    def test_signature_accepts_summary_mode_kwarg(self) -> None:
        # @trace AUDIT-N+11-001
        sig = inspect.signature(cli_impl._inject_time_constraint)
        assert "summary_mode" in sig.parameters
        assert sig.parameters["summary_mode"].default is False
        assert sig.parameters["summary_mode"].kind is inspect.Parameter.KEYWORD_ONLY

    def test_signature_accepts_seconds_per_tool_call_kwarg(self) -> None:
        # @trace AUDIT-N+11-002
        sig = inspect.signature(cli_impl._inject_time_constraint)
        assert "seconds_per_tool_call" in sig.parameters
        assert sig.parameters["seconds_per_tool_call"].default == 2.3
        assert sig.parameters["seconds_per_tool_call"].kind is inspect.Parameter.KEYWORD_ONLY

    def test_signature_prompt_and_timeout_remain_positional(self) -> None:
        # @trace AUDIT-N+11-003
        sig = inspect.signature(cli_impl._inject_time_constraint)
        params = sig.parameters
        assert params["prompt"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert params["timeout"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD

    def test_impl_resolves_to_observability_impl_canonical(self) -> None:
        # @trace AUDIT-N+11-004
        # AUDIT-N+9 contract preserved: identity holds across impl.
        assert cli_impl._inject_time_constraint is observability_impl._inject_time_constraint


# ---------------------------------------------------------------------------
# AUDIT-N+11 surface contract — round-trip behavior on summary_mode
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInjectTimeConstraintRoundTrip:
    """Pin that the WL-125 contract round-trips end-to-end."""

    def test_plain_call_appends_time_constraint_only(self) -> None:
        # @trace AUDIT-N+11-005
        result = cli_impl._inject_time_constraint("do stuff", 90)
        assert "do stuff" in result
        assert "TIME CONSTRAINT" in result
        assert "OUTPUT FORMAT" not in result

    def test_summary_mode_true_appends_output_format_block(self) -> None:
        # @trace AUDIT-N+11-006
        result = cli_impl._inject_time_constraint("task", 60, summary_mode=True)
        assert "TIME CONSTRAINT" in result
        assert "OUTPUT FORMAT" in result
        assert "Summary" in result

    def test_summary_mode_false_omits_output_format_block(self) -> None:
        # @trace AUDIT-N+11-007
        result = cli_impl._inject_time_constraint("task", 60, summary_mode=False)
        assert "TIME CONSTRAINT" in result
        assert "OUTPUT FORMAT" not in result

    def test_tool_calls_bounded_above_zero(self) -> None:
        # @trace AUDIT-N+11-008
        result = cli_impl._inject_time_constraint("p", 1)
        # 1 / 2.3 < 1, but max(1, ...) clamps
        assert "1 tool calls" in result or "2 tool calls" in result

    def test_seconds_per_tool_call_changes_budget(self) -> None:
        # @trace AUDIT-N+11-009
        r_default = cli_impl._inject_time_constraint("p", 60)
        r_slower = cli_impl._inject_time_constraint("p", 60, seconds_per_tool_call=10.0)
        # Slower per-call → fewer tool calls in budget.
        m_default = re.search(r"approximately (\d+) tool calls", r_default)
        m_slower = re.search(r"approximately (\d+) tool calls", r_slower)
        assert m_default is not None and m_slower is not None
        assert int(m_slower.group(1)) < int(m_default.group(1))

    def test_live_run_execution_core_path_no_longer_raises(self) -> None:
        # @trace AUDIT-N+11-010 — the critical live-breakage closure.
        # The function that ``run_impl_core`` / ``bg_impl_core`` invoke on
        # every prompt before sending to the agent. Before AUDIT-N+11
        # this raised ``TypeError: _inject_time_constraint() got an
        # unexpected keyword argument 'summary_mode'`` on every call.
        result = run_execution_core_helpers._inject_time_constraint_local("hello", 30, summary_mode=True)
        assert isinstance(result, str)
        assert "hello" in result
        assert "TIME CONSTRAINT" in result
        assert "OUTPUT FORMAT" in result


# ---------------------------------------------------------------------------
# AUDIT-N+11 surface contract — `_build_observe_summary_trend_scope` move
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildObserveSummaryTrendScopeMoved:
    """Pin that the trend-scope helper lives in observability_impl only."""

    def test_canonical_home_is_observability_impl(self) -> None:
        # @trace AUDIT-N+11-011
        assert hasattr(observability_impl, "_build_observe_summary_trend_scope")
        assert observability_impl._build_observe_summary_trend_scope.__module__ == (
            "thegent.cli.commands.observability_impl"
        )

    def test_impl_re_exports_from_canonical(self) -> None:
        # @trace AUDIT-N+11-012
        # AUDIT-N+9 re-export contract holds: legacy path resolves.
        assert hasattr(cli_impl, "_build_observe_summary_trend_scope")
        assert cli_impl._build_observe_summary_trend_scope is observability_impl._build_observe_summary_trend_scope

    def test_impl_no_longer_defines_inline(self) -> None:
        # @trace AUDIT-N+11-013
        src = inspect.getsource(cli_impl)
        assert "def _build_observe_summary_trend_scope" not in src, (
            "AUDIT-N+11: _build_observe_summary_trend_scope must be canonical "
            "in observability_impl, not inline in impl.py"
        )

    def test_observability_impl_all_lists_trend_scope(self) -> None:
        # @trace AUDIT-N+11-014
        assert "_build_observe_summary_trend_scope" in observability_impl.__all__

    def test_trend_scope_with_samples_enabled(self) -> None:
        # @trace AUDIT-N+11-015
        result = cli_impl._build_observe_summary_trend_scope(trend_samples=5)
        assert result == {"trend_samples": 5, "limit": 500, "enabled": True}

    def test_trend_scope_none_disabled(self) -> None:
        # @trace AUDIT-N+11-016
        result = cli_impl._build_observe_summary_trend_scope()
        assert result == {"trend_samples": None, "limit": 500, "enabled": False}

    def test_trend_scope_custom_limit(self) -> None:
        # @trace AUDIT-N+11-017
        result = cli_impl._build_observe_summary_trend_scope(trend_samples=10, limit=100)
        assert result == {"trend_samples": 10, "limit": 100, "enabled": True}


# ---------------------------------------------------------------------------
# AUDIT-N+11 re-export surface contract — observability surface intact
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObservabilityImplSurfaceIntact:
    """Pin that AUDIT-N+9 re-export surface still resolves through impl."""

    def test_observability_impl_module_loads(self) -> None:
        # @trace AUDIT-N+11-018
        assert hasattr(observability_impl, "observe_summary_impl")
        assert hasattr(observability_impl, "escalate_add_impl")
        assert hasattr(observability_impl, "err_console")

    def test_audit_n11_marker_present(self) -> None:
        # @trace AUDIT-N+11-019
        src = inspect.getsource(observability_impl)
        assert "AUDIT-N+11" in src, (
            "AUDIT-N+11 marker must be present in observability_impl.py to document the WL-125 signature restoration"
        )

    def test_audit_n9_marker_still_present(self) -> None:
        # @trace AUDIT-N+11-020 — regression guard against accidentally
        # removing the AUDIT-N+9 surface canonicalization marker.
        src = inspect.getsource(observability_impl)
        assert "AUDIT-N+9" in src

    def test_impl_audit_n9_reexport_block_includes_trend_scope(self) -> None:
        # @trace AUDIT-N+11-021
        src = inspect.getsource(cli_impl)
        assert "_build_observe_summary_trend_scope" in src
        assert "AUDIT-N+9: re-export observability surface" in src

    def test_impl_audit_n10_governance_reexport_block_intact(self) -> None:
        # @trace AUDIT-N+11-022 — AUDIT-N+10 governance surface preserved.
        assert hasattr(cli_impl, "escalate_add_impl")
        assert hasattr(cli_impl, "get_data_protection_status_impl")
        assert cli_impl.escalate_add_impl is observability_impl.escalate_add_impl


# ---------------------------------------------------------------------------
# AUDIT-N+11 carry-forward documentation (informational; no behavior pin)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAuditN11CarryForwardDocumented:
    """Document the post-N+11 carry-forward surfaces (no behavior pin).

    AUDIT-N+11 closed Findings 1 and 2 (Finding 3 in the drift report).
    Finding 3 (the dormant services/observability.py + run_observe_helpers.py
    parallel WL-120 core) is intentionally out-of-scope for N+11 and is
    documented as the AUDIT-N+12 candidate lane.
    """

    def test_services_observability_dormant_signal_present(self) -> None:
        # @trace AUDIT-N+11-023
        # The services observability module exists but is not wired through
        # observe_summary_impl — AUDIT-N+12 candidate.
        from thegent.cli.services import observability as services_observability

        assert hasattr(services_observability, "build_observe_summary_trend")
        assert hasattr(services_observability, "build_observe_summary_escalation")

    def test_run_observe_helpers_overlap_documented(self) -> None:
        # @trace AUDIT-N+11-024
        # The 11-function overlap between observability_impl (N+9 stubs) and
        # services/run_observe_helpers.py (real WL-120 implementations) is
        # the AUDIT-N+12 reconciliation scope.
        from thegent.cli.services import run_observe_helpers

        # AUDIT-N+12 candidates — names that exist on both modules
        # (N+9 module prefixes with ``_``; services module omits the
        # prefix). At least one of the (N+9 form, real form) pair must
        # exist on run_observe_helpers for each overlap row.
        overlap_pairs = [
            ("_hash_observe_summary_payload", "hash_observe_summary_payload"),
            ("_hash_health_payload", "hash_health_payload"),
            ("_observe_summary_freshness_bucket", "observe_summary_freshness_bucket"),
            (
                "_classify_observe_summary_trend_health",
                "classify_observe_summary_trend_health",
            ),
            ("_load_observe_summary_snapshots", "load_observe_summary_snapshots"),
            ("_load_previous_health_snapshot", "load_previous_health_snapshot"),
            ("_append_health_snapshot", "append_health_snapshot"),
            ("_append_observe_summary_snapshot", "append_observe_summary_snapshot"),
            ("_compact_health_snapshot_log", "compact_health_snapshot_log"),
        ]
        for n9_name, real_name in overlap_pairs:
            assert hasattr(run_observe_helpers, real_name) or hasattr(run_observe_helpers, n9_name), (
                f"run_observe_helpers.{{{n9_name}, {real_name}}} missing — overlap surface drifted"
            )


# ---------------------------------------------------------------------------
# Module import smoke (informational)
# ---------------------------------------------------------------------------
def test_audit_n11_module_loads_clean() -> None:
    """Smoke test that all pinned modules import without error."""
    # If any of these fail, the whole module graph is broken.
    assert cli_impl is not None
    assert observability_impl is not None
    assert run_execution_core_helpers is not None
