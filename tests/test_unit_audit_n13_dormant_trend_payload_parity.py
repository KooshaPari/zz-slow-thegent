"""AUDIT-N+13 dormant-core trend payload wire-up parity envelope.

This test pins the AUDIT-N+13 hand-off:

1. ``observability_impl`` exposes ``_build_observe_trend_payload`` as
   the canonical home for the WL-120 dormant-core trend payload
   (separate from the inner ``_build_observe_trend_block`` that
   AUDIT-N+12 introduced for the side-channel flag).

2. ``_build_observe_trend_payload`` returns the documented outer
   envelope keys: ``trend_summary`` (dormant block),
   ``escalation_breakdown``, ``trend_scope_signature``,
   ``trend_scope_key``, ``trend_snapshot_ids``, and the side-channel
   ``wl120_dormant_round_trip``.

3. When ``trend_samples <= 0`` the function returns the legacy
   disabled-mode stub under ``trend_summary`` and
   ``wl120_dormant_round_trip`` is False (no dormant call).

4. When ``trend_samples > 0`` the function delegates to
   ``thegent.cli.services.observability.build_observe_summary_trend``
   AND ``build_observe_summary_escalation`` and surfaces the dormant
   payload under the documented keys.

5. When the dormant-core callables raise, the function returns a
   payload with ``wl120_dormant_round_trip=False`` and safe defaults
   rather than propagating the exception.

6. ``observe_summary_impl`` now threads the dormant-core payload
   through the outer return contract under the documented keys:
   ``trend_payload`` (full envelope), ``escalation_breakdown``
   (mirrored), ``trend_scope_signature`` (mirrored), and
   ``wl120_dormant_round_trip`` (mirrored at outer level when the
   dormant round-trip succeeds). The legacy AUDIT-N+9 5-key stub
   block continues to live under ``trend_summary`` so the AUDIT-N+12
   parity suite stays green.

7. ``impl._build_observe_trend_payload`` is the same function as
   ``observability_impl._build_observe_trend_payload`` (re-export
   contract).
"""

from __future__ import annotations

from typing import Any

import pytest

from thegent.cli.commands import impl, observability_impl
from thegent.cli.services import observability as services_observability

# ---------------------------------------------------------------------------
# 1. observability_impl exposes _build_observe_trend_payload as the canonical
#    home for the WL-120 dormant-core trend payload.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildObserveTrendPayloadExists:
    """AUDIT-N+13: ``_build_observe_trend_payload`` is the canonical
    dormant-core trend payload builder."""

    # @trace FR-AUDIT-N+13-001
    def test_build_observe_trend_payload_is_callable(self) -> None:
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        assert callable(_build_observe_trend_payload)

    # @trace FR-AUDIT-N+13-002
    def test_build_observe_trend_payload_in_observability_impl_all(self) -> None:
        """The new helper is exported from ``observability_impl.__all__``."""
        assert "_build_observe_trend_payload" in observability_impl.__all__

    # @trace FR-AUDIT-N+13-003
    def test_build_observe_trend_payload_re_exported_by_impl(self) -> None:
        """``impl._build_observe_trend_payload`` is the same function as
        ``observability_impl._build_observe_trend_payload``."""
        assert impl._build_observe_trend_payload is observability_impl._build_observe_trend_payload

    # @trace FR-AUDIT-N+13-004
    def test_build_observe_trend_payload_in_impl_all(self) -> None:
        """The new helper is exported from ``impl.__all__``."""
        assert "_build_observe_trend_payload" in impl.__all__

    # @trace FR-AUDIT-N+13-005
    def test_build_observe_trend_block_also_in_impl_all(self) -> None:
        """AUDIT-N+12's ``_build_observe_trend_block`` is preserved in
        ``impl.__all__`` so legacy call-sites stay green."""
        assert "_build_observe_trend_block" in impl.__all__


# ---------------------------------------------------------------------------
# 2. _build_observe_trend_payload returns the documented outer envelope keys.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildObserveTrendPayloadShape:
    """AUDIT-N+13: the outer envelope has the documented keys."""

    # @trace FR-AUDIT-N+13-006
    def test_disabled_mode_returns_legacy_stub(self) -> None:
        """When ``trend_samples <= 0`` the dormant core is skipped and
        the returned payload is the legacy disabled-mode stub under
        ``trend_summary``."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(0)
        assert isinstance(result, dict)
        assert result["wl120_dormant_round_trip"] is False
        assert result["trend_summary"] == {
            "enabled": False,
            "trend_sampling_mode": "disabled",
            "trend_samples_requested": 0,
            "trend_effective_samples": 0,
        }
        # Other outer keys are present with safe defaults.
        assert result["escalation_breakdown"] == {}
        assert result["trend_scope_signature"] == ""
        assert result["trend_scope_key"] == {}
        assert result["trend_snapshot_ids"] == []

    # @trace FR-AUDIT-N+13-007
    def test_negative_trend_samples_returns_legacy_stub(self) -> None:
        """Negative ``trend_samples`` is treated the same as 0 (legacy
        disabled-mode stub)."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(-1)
        assert result["wl120_dormant_round_trip"] is False
        assert result["trend_summary"]["enabled"] is False

    # @trace FR-AUDIT-N+13-008
    def test_outer_envelope_has_all_documented_keys(self) -> None:
        """Whether dormant succeeds or fails, the outer payload has the
        six documented keys."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(5)
        expected_keys = {
            "trend_summary",
            "escalation_breakdown",
            "trend_scope_signature",
            "trend_scope_key",
            "trend_snapshot_ids",
            "wl120_dormant_round_trip",
        }
        assert expected_keys.issubset(result.keys())

    # @trace FR-AUDIT-N+13-009
    def test_trend_snapshot_ids_is_list(self) -> None:
        """``trend_snapshot_ids`` is always a list (never None / str)."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        for trend_samples in (0, -1, 1, 5):
            result = _build_observe_trend_payload(trend_samples)
            assert isinstance(result["trend_snapshot_ids"], list)


# ---------------------------------------------------------------------------
# 3. Dormant-core monkeypatch — the canonical wire-up contract.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildObserveTrendPayloadDormantWire:
    """AUDIT-N+13: when ``trend_samples > 0`` the dormant-core callables
    are invoked with the correct kwargs and their return value is
    surfaced through the outer envelope."""

    # @trace FR-AUDIT-N+13-010
    def test_trend_callable_invoked_with_kwargs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``build_observe_summary_trend`` is called with the kwargs
        forwarded through ``_build_observe_trend_payload``."""
        captured: dict[str, Any] = {}

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {
                "trend_summary": {"enabled": True, "trend_snapshot_health": "good"},
                "trend_scope_key": {"provider": kwargs.get("provider")},
                "trend_scope_signature": "abc123",
                "trend_snapshot_ids": ["2026-02-21T00:00:00+00:00"],
                "trend_samples_requested": 5,
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            return {"escalation_rows": [], "top_rows": [], "past_sla_count": 0}

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)

        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(
            5,
            provider="gemini",
            drift_window=20,
            structural_budget_pct=4.0,
            semantic_budget_pct=8.0,
            top_escalations=3,
        )
        # Outer envelope is populated from the dormant return value.
        assert captured["trend_samples"] == 5
        assert captured["provider"] == "gemini"
        assert captured["drift_window"] == 20
        assert captured["structural_budget_pct"] == 4.0
        assert captured["semantic_budget_pct"] == 8.0
        assert captured["top_escalations"] == 3
        assert result["trend_scope_signature"] == "abc123"
        assert result["trend_snapshot_ids"] == ["2026-02-21T00:00:00+00:00"]
        assert result["wl120_dormant_round_trip"] is True

    # @trace FR-AUDIT-N+13-011
    def test_escalation_block_surfaced(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``build_observe_summary_escalation`` is invoked and its
        return value is surfaced under ``escalation_breakdown``."""

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {},
                "trend_scope_signature": "sig",
                "trend_snapshot_ids": [],
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            return {
                "escalation_rows": [{"run_id": "r1", "priority": 7}],
                "top_rows": [{"run_id": "r1"}],
                "past_sla_count": 1,
            }

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)

        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(5, pending=[{"a": 1}], past_sla=[{"b": 2}])
        assert result["escalation_breakdown"]["past_sla_count"] == 1
        assert result["escalation_breakdown"]["top_rows"] == [{"run_id": "r1"}]
        assert result["wl120_dormant_round_trip"] is True

    # @trace FR-AUDIT-N+13-012
    def test_pending_and_past_sla_forwarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pending and past-SLA lists are forwarded to the dormant
        escalation builder."""
        captured: dict[str, Any] = {}

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {},
                "trend_scope_signature": "s",
                "trend_snapshot_ids": [],
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            captured["pending"] = kwargs.get("pending")
            captured["past_sla"] = kwargs.get("past_sla")
            return {"escalation_rows": [], "top_rows": [], "past_sla_count": 0}

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)

        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        _build_observe_trend_payload(
            5,
            pending=[{"run_id": "p1"}],
            past_sla=[{"run_id": "ps1"}],
        )
        assert captured["pending"] == [{"run_id": "p1"}]
        assert captured["past_sla"] == [{"run_id": "ps1"}]


# ---------------------------------------------------------------------------
# 4. Resilience — dormant-core failures don't propagate.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildObserveTrendPayloadResilience:
    """AUDIT-N+13: a failed dormant-core round-trip returns a payload
    with ``wl120_dormant_round_trip=False`` and safe defaults."""

    # @trace FR-AUDIT-N+13-013
    def test_trend_callable_raises_returns_safe_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If ``build_observe_summary_trend`` raises, the function
        returns safe defaults without propagating."""

        def _raise(**_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("dormant-core exploded")

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _raise)

        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(5)
        assert result["wl120_dormant_round_trip"] is False
        assert result["trend_summary"] == {}
        assert result["trend_scope_signature"] == ""
        assert result["trend_snapshot_ids"] == []

    # @trace FR-AUDIT-N+13-014
    def test_escalation_callable_raises_returns_safe_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If ``build_observe_summary_escalation`` raises, the
        function returns safe defaults without propagating."""

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {},
                "trend_scope_signature": "sig",
                "trend_snapshot_ids": [],
            }

        def _raise(**_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("dormant-core exploded")

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _raise)

        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        result = _build_observe_trend_payload(5)
        # Trend succeeded but escalation failed → flag is False.
        assert result["wl120_dormant_round_trip"] is False
        assert result["escalation_breakdown"] == {}


# ---------------------------------------------------------------------------
# 5. observe_summary_impl threads the dormant payload through the outer
#    return contract under the documented keys.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObserveSummaryImplWL120DormantWire:
    """AUDIT-N+13: ``observe_summary_impl`` now attaches the dormant-core
    trend payload under documented keys in its outer return contract.

    These tests monkeypatch the dormant builders AND the inner
    observability helpers (``_collect_observe_kpis`` etc.) so the full
    ``observe_summary_impl`` function can be exercised without
    requiring a populated telemetry layer."""

    def _stub_inner_helpers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace the inner telemetry-dependent helpers with safe
        no-op stubs so ``observe_summary_impl`` runs end-to-end
        without touching the real ContractTelemetry."""
        monkeypatch.setattr(
            observability_impl,
            "_collect_observe_kpis",
            lambda *_a, **_kw: {
                "total": 0,
                "fallback_rate": 0.0,
                "success_rate": 1.0,
                "avg_confidence": 1.0,
            },
        )
        monkeypatch.setattr(
            observability_impl,
            "_collect_observe_drift",
            lambda *_a, **_kw: {
                "within_budget": True,
                "structural_rate_pct": 0.0,
                "semantic_rate_pct": 0.0,
            },
        )
        monkeypatch.setattr(
            observability_impl,
            "_count_pending_with_cap",
            lambda *_a, **_kw: ([], []),
        )

    # @trace FR-AUDIT-N+13-015
    def test_outer_contract_has_trend_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``observe_summary_impl(trend_samples=N)`` returns a dict
        with ``trend_payload`` carrying the dormant envelope."""

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {"enabled": True, "trend_snapshot_health": "good"},
                "trend_scope_key": {"provider": "claude"},
                "trend_scope_signature": "outer-sig",
                "trend_snapshot_ids": ["2026-02-21T00:00:00+00:00"],
                "trend_samples_requested": 5,
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            return {"escalation_rows": [], "top_rows": [], "past_sla_count": 0}

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)
        self._stub_inner_helpers(monkeypatch)

        from thegent.cli.commands.observability_impl import observe_summary_impl

        result = observe_summary_impl(trend_samples=5)
        assert "trend_payload" in result
        payload = result["trend_payload"]
        assert payload["trend_scope_signature"] == "outer-sig"
        assert payload["wl120_dormant_round_trip"] is True
        # Outer mirrored keys are present.
        assert result["escalation_breakdown"] == {
            "escalation_rows": [],
            "top_rows": [],
            "past_sla_count": 0,
        }
        assert result["trend_scope_signature"] == "outer-sig"
        # Outer wl120_dormant_round_trip mirrors the dormant flag.
        assert result["wl120_dormant_round_trip"] is True

    # @trace FR-AUDIT-N+13-016
    def test_legacy_trend_summary_block_preserved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The legacy AUDIT-N+9 5-key stub block lives under
        ``result["trend_summary"]`` (AUDIT-N+12 backward compat) so
        the existing parity suite stays green."""

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {},
                "trend_scope_signature": "s",
                "trend_snapshot_ids": [],
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            return {"escalation_rows": [], "top_rows": [], "past_sla_count": 0}

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)
        self._stub_inner_helpers(monkeypatch)

        from thegent.cli.commands.observability_impl import observe_summary_impl

        result = observe_summary_impl(trend_samples=5)
        # Legacy stub block has the AUDIT-N+9 5-key shape + AUDIT-N+12
        # side-channel flag.
        stub = result["trend_summary"]
        assert stub["enabled"] is True
        assert stub["trend_samples_requested"] == 5
        assert stub["trend_effective_samples"] == 5
        assert stub["history_sample_count"] == 0
        assert stub["trend_snapshot_health"] == "good"
        assert stub.get("wl120_dormant_round_trip") is True

    # @trace FR-AUDIT-N+13-017
    def test_trend_samples_none_skips_dormant(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``trend_samples=None`` the dormant-core wire-up is
        skipped and the outer contract has none of the AUDIT-N+13
        keys (only the legacy keys)."""
        self._stub_inner_helpers(monkeypatch)

        from thegent.cli.commands.observability_impl import observe_summary_impl

        result = observe_summary_impl(trend_samples=None)
        # Legacy keys absent.
        assert "trend_summary" not in result
        assert "trend_payload" not in result
        assert "escalation_breakdown" not in result
        assert "trend_scope_signature" not in result
        assert "wl120_dormant_round_trip" not in result

    # @trace FR-AUDIT-N+13-018
    def test_outer_generated_query_pinned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``generated_query`` is pinned for traceability of the
        ``trend_samples`` arg under the AUDIT-N+13 wire-up."""

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            return {
                "trend_summary": {},
                "trend_scope_signature": "s",
                "trend_snapshot_ids": [],
            }

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            return {"escalation_rows": [], "top_rows": [], "past_sla_count": 0}

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _fake_trend)
        monkeypatch.setattr(services_observability, "build_observe_summary_escalation", _fake_escalation)
        self._stub_inner_helpers(monkeypatch)

        from thegent.cli.commands.observability_impl import observe_summary_impl

        result = observe_summary_impl(trend_samples=7)
        # AUDIT-N+16 added top_escalations to the generated_query
        # contract alongside trend_samples.
        assert result["generated_query"]["trend_samples"] == 7
        assert "top_escalations" in result["generated_query"]

    # @trace FR-AUDIT-N+13-024
    def test_dormant_failure_keeps_legacy_stub(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If the dormant-core callables raise, ``observe_summary_impl``
        still returns the legacy stub block under ``trend_summary``
        with ``wl120_dormant_round_trip=False`` and a safe-default
        envelope under ``trend_payload``."""

        def _raise_trend(**_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("dormant-core exploded")

        def _raise_escalation(**_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("dormant-core exploded")

        monkeypatch.setattr(services_observability, "build_observe_summary_trend", _raise_trend)
        monkeypatch.setattr(
            services_observability,
            "build_observe_summary_escalation",
            _raise_escalation,
        )
        self._stub_inner_helpers(monkeypatch)

        from thegent.cli.commands.observability_impl import observe_summary_impl

        result = observe_summary_impl(trend_samples=5)
        # Legacy stub block is still present.
        stub = result["trend_summary"]
        assert stub["enabled"] is True
        # Outer wl120_dormant_round_trip is False (dormant failed).
        assert result.get("wl120_dormant_round_trip") is False
        # Outer trend_payload is the safe-default envelope.
        assert result["trend_payload"]["wl120_dormant_round_trip"] is False
        assert result["trend_payload"]["trend_scope_signature"] == ""


# ---------------------------------------------------------------------------
# 6. observability_impl module doc pins AUDIT-N+13 marker.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObservabilityImplDocstringAuditN13:
    """AUDIT-N+13: the observability_impl module docstring carries the
    AUDIT-N+13 marker."""

    # @trace FR-AUDIT-N+13-019
    def test_observability_impl_doc_mentions_audit_n13(self) -> None:
        text = observability_impl.__doc__ or ""
        assert "AUDIT-N+13" in text
        assert "_build_observe_trend_payload" in text

    # @trace FR-AUDIT-N+13-020
    def test_observability_impl_doc_mentions_dormant_keys(self) -> None:
        """The module doc enumerates the AUDIT-N+13 outer envelope keys."""
        text = observability_impl.__doc__ or ""
        for key in ("trend_payload", "escalation_breakdown", "trend_scope_signature"):
            assert key in text, f"AUDIT-N+13 doc missing key {key}"


# ---------------------------------------------------------------------------
# 7. Module graph loads clean (no circular imports / syntax errors).
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAuditN13ModuleGraphLoadsClean:
    """AUDIT-N+13: every touched module imports without side-effects."""

    # @trace FR-AUDIT-N+13-021
    def test_impl_module_loads(self) -> None:
        assert impl.__file__ is not None

    # @trace FR-AUDIT-N+13-022
    def test_observability_impl_module_loads(self) -> None:
        assert observability_impl.__file__ is not None

    # @trace FR-AUDIT-N+13-023
    def test_build_observe_trend_payload_defined_in_observability_impl(self) -> None:
        """``_build_observe_trend_payload`` is defined in
        ``observability_impl`` (the canonical home), not ``impl``."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_payload

        assert _build_observe_trend_payload.__module__ == "thegent.cli.commands.observability_impl"
