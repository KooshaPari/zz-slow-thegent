"""AUDIT-N+12 session-impl extraction + WL-120 wire-up parity envelope.

This test pins the AUDIT-N+12 hand-off:

1. ``session_impl`` module is the canonical home for 14 session-lifecycle
   helpers (PID liveness, scope key, session paths, session id generation,
   session-meta IO, session-status resolution, agent-model resolution,
   prior-session output loading, CWD cache, continuation tail,
   background session observer, continuation prompt).

2. ``impl.py`` re-exports every helper from ``session_impl`` so the
   legacy ``impl.<x>`` import path remains valid.

3. ``impl.py`` surfaces ``run_observe_helpers`` and
   ``services_observability`` as module attributes so WL-125 monkeypatch
   sites like ``monkeypatch.setattr("thegent.cli.commands.impl.run_observe_helpers.<x>", ...)``
   resolve.

4. The four WL-125 dispatch bridges in ``observability_impl``
   (``_hash_observe_summary_payload``, ``_classify_observe_summary_trend_health``,
   ``_load_observe_summary_snapshots``, ``_append_observe_summary_snapshot``)
   preserve the AUDIT-N+9 positional contracts AND route WL-125 kwargs
   to ``run_observe_helpers``.

5. ``observe_summary_impl`` now exposes a ``wl120_dormant_round_trip``
   side-channel indicating whether the dormant core builders were
   exercised.

6. ``impl._resolve_agent_model`` is the canonical 4-arg form
   (AUDIT-N+12 fix; the legacy 1-arg stub was removed).

7. ``impl.__all__`` is cleaned: stale observability / governance / dag
   entries removed; session entries added.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from thegent.cli.commands import impl, observability_impl, session_impl
from thegent.cli.services import observability as services_observability

# ---------------------------------------------------------------------------
# 1. session_impl module exists and exports the canonical 14 helpers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSessionImplModuleExists:
    """AUDIT-N+12: session_impl module is the canonical home for the
    session-lifecycle surface."""

    # @trace FR-AUDIT-N+12-001
    def test_session_impl_module_loads(self) -> None:
        assert session_impl is not None
        assert session_impl.__file__ is not None
        assert session_impl.__file__.endswith("session_impl.py")

    # @trace FR-AUDIT-N+12-002
    def test_session_impl_exposes_14_canonical_helpers(self) -> None:
        expected = (
            "_CONTINUATION_TAIL_CHARS",
            "_CWD_CACHE",
            "_is_pid_running",
            "_scope_key",
            "_session_paths",
            "_new_session_id",
            "_save_session_meta",
            "_read_session_meta",
            "_find_session_meta",
            "_resolve_session_status",
            "_resolve_agent_model",
            "_load_prior_session_output",
            "_build_continuation_prompt",
            "_session_dir",
            "_session_scope_dirs",
        )
        for name in expected:
            assert hasattr(session_impl, name), f"session_impl missing {name}"

    # @trace FR-AUDIT-N+12-003
    def test_session_impl_docstring_pins_audit_n12_marker(self) -> None:
        text = session_impl.__doc__ or ""
        assert "AUDIT-N+12" in text


# ---------------------------------------------------------------------------
# 2. impl.py re-exports the session surface
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplReExportsSessionSurface:
    """AUDIT-N+12: impl.<x> must resolve to the session_impl helpers so
    legacy call-sites stay green."""

    # @trace FR-AUDIT-N+12-004
    def test_impl_re_exports_all_session_helpers(self) -> None:
        names = (
            "_CONTINUATION_TAIL_CHARS",
            "_CWD_CACHE",
            "_is_pid_running",
            "_scope_key",
            "_session_paths",
            "_new_session_id",
            "_save_session_meta",
            "_read_session_meta",
            "_find_session_meta",
            "_resolve_session_status",
            "_resolve_agent_model",
            "_load_prior_session_output",
            "_build_continuation_prompt",
            "_session_dir",
            "_session_scope_dirs",
            "run_observe_helpers",
            "services_observability",
        )
        for name in names:
            assert hasattr(impl, name), f"impl missing re-export {name}"

    # @trace FR-AUDIT-N+12-005
    def test_impl_resolve_agent_model_is_canonical_4arg(self) -> None:
        """AUDIT-N+12: the legacy 1-arg stub was removed; only the 4-arg
        session_impl form survives. TypeError on insufficient args is the
        marker that the legacy stub is gone."""
        with pytest.raises(TypeError):
            impl._resolve_agent_model()
        # 4-arg signature is callable.
        settings = MagicMock()
        settings.default_gemini_model = "gemini-2.0-flash"
        result = impl._resolve_agent_model("gemini", None, "write", settings)
        assert result == "gemini-2.0-flash"

    # @trace FR-AUDIT-N+12-006
    def test_impl_run_observe_helpers_module_attribute(self) -> None:
        """AUDIT-N+12: ``impl.run_observe_helpers`` must be the
        :mod:`thegent.cli.services.run_observe_helpers` module so
        ``monkeypatch.setattr("thegent.cli.commands.impl.run_observe_helpers.<x>", ...)``
        sites resolve."""
        from thegent.cli.services import run_observe_helpers

        assert impl.run_observe_helpers is run_observe_helpers

    # @trace FR-AUDIT-N+12-007
    def test_impl_services_observability_module_attribute(self) -> None:
        """AUDIT-N+12: ``impl.services_observability`` surfaces the
        :mod:`thegent.cli.services.observability` module so WL-120
        reconciliation tests can monkeypatch the dormant builders."""
        from thegent.cli.services import observability as so

        assert impl.services_observability is so

    # @trace FR-AUDIT-N+12-008
    def test_impl_session_helpers_resolve_to_canonical_home(self) -> None:
        """AUDIT-N+12 identity contract: impl.<session_helper> is
        session_impl.<session_helper>."""
        for name in (
            "_is_pid_running",
            "_scope_key",
            "_resolve_session_status",
            "_resolve_agent_model",
            "_load_prior_session_output",
            "_session_dir",
        ):
            assert getattr(impl, name) is getattr(session_impl, name), name


# ---------------------------------------------------------------------------
# 3. Session helpers behave correctly
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSessionImplHelperBehavior:
    """AUDIT-N+12: each session helper returns the expected shape."""

    # @trace FR-AUDIT-N+12-009
    def test_is_pid_running_zero_and_negative(self) -> None:
        assert impl._is_pid_running(0) is False
        assert impl._is_pid_running(-1) is False

    # @trace FR-AUDIT-N+12-010
    def test_is_pid_running_current_pid_is_alive(self) -> None:
        assert impl._is_pid_running(os.getpid()) is True  # noqa: SLF001

    # @trace FR-AUDIT-N+12-011
    def test_scope_key_replaces_unsafe_chars(self) -> None:
        assert impl._scope_key("user:repo/path") == "user-repo-path"
        assert impl._scope_key("") == ""
        assert impl._scope_key("safe_name-1.0") == "safe_name-1.0"

    # @trace FR-AUDIT-N+12-012
    # @trace FR-AUDIT-N+12-013
    def test_new_session_id_format(self) -> None:
        """``_new_session_id`` returns ``<agent>-<scope>-<8-char hex uuid>``.

        Format pinned by
        ``tests/test_unit_cli_impl_session.py::TestNewSessionId``:
        contains agent name and is unique across 20 invocations.
        """
        sid = impl._new_session_id("gemini", "test-user")
        # agent-scope-8hexuuid (>= agent-scope- + 8 hex chars minimum).
        assert len(sid) >= 8 + 1 + 1 + 8
        assert "gemini" in sid
        assert "test-user" in sid
        # Uniqueness across 20 calls.
        ids = {impl._new_session_id("gemini", "test-user") for _ in range(20)}
        assert len(ids) == 20

    def test_resolve_agent_model_explicit_wins(self) -> None:
        settings = MagicMock()
        assert impl._resolve_agent_model("gemini", "explicit-model", "write", settings) == "explicit-model"

    # @trace FR-AUDIT-N+12-014
    def test_resolve_agent_model_antigravity(self) -> None:
        """AUDIT-N+12: antigravity uses its own default_antigravity_model,
        not default_cursor_model."""
        settings = MagicMock()
        settings.default_antigravity_model = "gemini-3-flash"
        # default_cursor_model must NOT leak in for antigravity.
        settings.default_cursor_model = "cursor-1"
        assert impl._resolve_agent_model("antigravity", None, "write", settings) == "gemini-3-flash"

    # @trace FR-AUDIT-N+12-015
    def test_resolve_agent_model_cursor(self) -> None:
        settings = MagicMock()
        settings.default_cursor_model = "cursor-1"
        assert impl._resolve_agent_model("cursor", None, "write", settings) == "cursor-1"

    # @trace FR-AUDIT-N+12-016
    def test_continuation_tail_chars_is_8000(self) -> None:
        assert impl._CONTINUATION_TAIL_CHARS == 8_000

    # @trace FR-AUDIT-N+12-017
    def test_cwd_cache_is_dict(self) -> None:
        assert isinstance(impl._CWD_CACHE, dict)


# ---------------------------------------------------------------------------
# 4. WL-125 dispatch bridges preserve AUDIT-N+9 + WL-125 contracts
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWL125DispatchBridges:
    """AUDIT-N+12: the four WL-125 wrappers in observability_impl
    dual-mode: AUDIT-N+9 positional contract OR WL-125 kwarg contract.
    """

    # @trace FR-AUDIT-N+12-018
    def test_hash_observe_summary_payload_legacy_16char(self) -> None:
        """AUDIT-N+9 contract: returns 16-char hex string when called
        with a positional dict and no monkeypatch."""
        result = impl._hash_observe_summary_payload({"kpis": {"total": 100}})
        assert isinstance(result, str)
        assert len(result) == 16

    # @trace FR-AUDIT-N+12-019
    def test_hash_observe_summary_payload_wl125_monkeypatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WL-125 contract: when ``run_observe_helpers.hash_observe_summary_payload``
        is monkeypatched, the wrapper honours whatever the test returns."""
        captured: dict[str, Any] = {}

        def _fake(payload: dict[str, Any]) -> dict[str, str]:
            captured["payload"] = payload
            return {"algorithm": "sha256", "value": "wrapped"}

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_observe_helpers.hash_observe_summary_payload",
            _fake,
        )
        payload = {"payload_type": "observe_summary"}
        result = impl._hash_observe_summary_payload(payload)
        assert result == {"algorithm": "sha256", "value": "wrapped"}
        assert captured["payload"] == payload

    # @trace FR-AUDIT-N+12-020
    def test_classify_observe_summary_trend_health_legacy(self) -> None:
        """AUDIT-N+9 contract: returns 'healthy' for positional dict."""
        result = impl._classify_observe_summary_trend_health({"trend": [1, 2, 3]})
        assert result == "healthy"

    # @trace FR-AUDIT-N+12-021
    def test_classify_observe_summary_trend_health_wl125_kwargs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WL-125 contract: kwargs forward to ``run_observe_helpers``."""
        captured: dict[str, Any] = {}

        def _fake(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"trend_snapshot_health": "warning", "trend_snapshot_health_score": 81}

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_observe_helpers.classify_observe_summary_trend_health",
            _fake,
        )
        result = impl._classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=False,
            trend_snapshot_coverage_pct=75.0,
            trend_snapshot_deficit=1,
        )
        assert result["trend_snapshot_health"] == "warning"
        assert captured["enabled"] is True
        assert captured["baseline_available"] is False
        assert captured["trend_snapshot_coverage_pct"] == 75.0
        assert captured["trend_snapshot_deficit"] == 1

    # @trace FR-AUDIT-N+12-022
    def test_append_observe_summary_snapshot_legacy(self) -> None:
        """AUDIT-N+9 contract: positional ``(snapshots, snapshot)``."""
        snaps: list[dict[str, Any]] = []
        impl._append_observe_summary_snapshot(snaps, {"k": "v"})
        assert snaps == [{"k": "v"}]

    # @trace FR-AUDIT-N+12-023
    def test_append_observe_summary_snapshot_wl125_monkeypatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WL-125 contract: 6 positional args forwarded to
        ``run_observe_helpers.append_observe_summary_snapshot``."""
        captured: dict[str, Any] = {}

        def _fake(
            payload: dict[str, Any],
            trend_scope_key: dict[str, Any],
            trend_scope_signature: str,
            scope_key_json: str,
            trend_snapshot_ids: list[str],
            trend_summary: dict[str, Any],
        ) -> None:
            captured["payload"] = payload
            captured["trend_scope_signature"] = trend_scope_signature

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_observe_helpers.append_observe_summary_snapshot",
            _fake,
        )
        impl._append_observe_summary_snapshot(
            {"payload_type": "observe_summary"},
            {"payload_type": "observe_summary", "limit": 100},
            "sig-123",
            '{"payload_type":"observe_summary","limit":100}',
            ["2026-02-21T00:00:00+00:00"],
            {"trend_snapshot_health": "good"},
        )
        assert captured["payload"] == {"payload_type": "observe_summary"}
        assert captured["trend_scope_signature"] == "sig-123"

    # @trace FR-AUDIT-N+12-024
    def test_load_observe_summary_snapshots_wl125_monkeypatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WL-125 contract: 3 positional args forwarded to
        ``run_observe_helpers.load_observe_summary_snapshots``."""
        captured: dict[str, Any] = {}

        def _fake(scope_signature: str, scope_key_json: str, limit: int) -> list[dict[str, Any]]:
            captured["scope_signature"] = scope_signature
            captured["scope_key_json"] = scope_key_json
            captured["limit"] = limit
            return [{"record_type": "observe_summary_snapshot"}]

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_observe_helpers.load_observe_summary_snapshots",
            _fake,
        )
        result = impl._load_observe_summary_snapshots("sig", "{}", 5)
        assert result == [{"record_type": "observe_summary_snapshot"}]
        assert captured == {"scope_signature": "sig", "scope_key_json": "{}", "limit": 5}

    # @trace FR-AUDIT-N+12-025
    def test_load_observe_summary_snapshots_legacy(self, tmp_path: Path) -> None:
        """AUDIT-N+9 contract: positional ``(session_dir, limit)`` returns list."""
        result = impl._load_observe_summary_snapshots(tmp_path, 100)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 5. observe_summary_impl side-channel WL-120 dormant round-trip
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObserveSummaryImplWL120SideChannel:
    """AUDIT-N+12: ``observe_summary_impl`` now carries a side-channel
    ``wl120_dormant_round_trip`` flag indicating whether the dormant
    core builders were exercised. We test the dispatch through
    ``_build_observe_trend_block`` (which carries the side-channel)
    without depending on the full ``observe_summary_impl`` runtime
    contract (which requires a populated telemetry layer)."""

    # @trace FR-AUDIT-N+12-026
    def test_observability_impl_exposes_services_observability(self) -> None:
        """AUDIT-N+12: ``observability_impl.services_observability`` is
        the same module as ``impl.services_observability`` so
        monkeypatching either surfaces the same target."""
        assert observability_impl.services_observability is services_observability
        assert impl.services_observability is services_observability

    # @trace FR-AUDIT-N+12-027
    def test_build_observe_trend_block_trend_samples_returns_dict(self) -> None:
        """``_build_observe_trend_block(N)`` returns the trend-scope dict
        with the side-channel flag attached."""
        from thegent.cli.commands.observability_impl import _build_observe_trend_block

        result = _build_observe_trend_block(5)
        assert isinstance(result, dict)
        assert result.get("wl120_dormant_round_trip") is True

    # @trace FR-AUDIT-N+12-028
    def test_build_observe_trend_block_trend_samples_invokes_dormant_core(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With ``trend_samples=N``, the dormant-core builders are called
        and the side-channel records the round-trip."""
        captured: dict[str, Any] = {}

        def _fake_trend(**kwargs: Any) -> dict[str, Any]:
            captured["trend_called"] = True
            captured.update(kwargs)
            return {"trend_snapshot_health": "good", "trend_snapshot_health_score": 100}

        def _fake_escalation(**kwargs: Any) -> dict[str, Any]:
            captured["escalation_called"] = True
            return {"escalation_warm": 0, "escalation_past_sla": 0}

        monkeypatch.setattr(
            services_observability,
            "build_observe_summary_trend",
            _fake_trend,
        )
        monkeypatch.setattr(
            services_observability,
            "build_observe_summary_escalation",
            _fake_escalation,
        )

        from thegent.cli.commands.observability_impl import _build_observe_trend_block

        result = _build_observe_trend_block(5)
        assert captured.get("trend_called") is True
        assert captured.get("escalation_called") is True
        assert result.get("wl120_dormant_round_trip") is True
        assert result.get("trend_snapshot_health") == "good"


# ---------------------------------------------------------------------------
# 6. impl.__all__ is cleaned
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplAllCleanedUp:
    """AUDIT-N+12: ``impl.__all__`` no longer references stale helpers
    that don't exist on the module surface."""

    # @trace FR-AUDIT-N+12-029
    def test_impl_all_excludes_undefined_observability_entries(self) -> None:
        """Stale ``HEALTH_PAYLOAD_SCHEMA_VERSION`` entry removed."""
        assert "HEALTH_PAYLOAD_SCHEMA_VERSION" not in impl.__all__

    # @trace FR-AUDIT-N+12-030
    def test_impl_all_excludes_undefined_session_entries(self) -> None:
        """Stale ``_session_state_path`` entry removed."""
        assert "_session_state_path" not in impl.__all__

    # @trace FR-AUDIT-N+12-031
    def test_impl_all_excludes_undefined_dag_entries(self) -> None:
        """Stale dag entries (``_coerce_issue_types``, ``_check_dag_cycles``,
        ``dag_list_impl``, ``dag_raw_impl``) removed from ``__all__``."""
        for name in ("_coerce_issue_types", "_check_dag_cycles", "dag_list_impl", "dag_raw_impl"):
            assert name not in impl.__all__, f"stale entry {name} in impl.__all__"

    # @trace FR-AUDIT-N+12-032
    def test_impl_all_includes_session_helpers(self) -> None:
        """Session helpers (post-AUDIT-N+12) live in ``__all__``."""
        for name in (
            "_CONTINUATION_TAIL_CHARS",
            "_CWD_CACHE",
            "_is_pid_running",
            "_scope_key",
            "_new_session_id",
            "_resolve_session_status",
            "_resolve_agent_model",
            "_load_prior_session_output",
        ):
            assert name in impl.__all__, f"session helper {name} missing from impl.__all__"


# ---------------------------------------------------------------------------
# 7. Carry-forward documentation for AUDIT-N+13+
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAuditN13CarryForward:
    """AUDIT-N+12 documents the AUDIT-N+13+ carry-forward: the broader
    ``run_impl`` / ``bg_impl`` / session-lifecycle surface pinned by
    :mod:`tests.test_unit_cli_impl_session` is the next lane.

    The current AUDIT-N+12 lane addressed the **helper surface**
    (PID liveness, scope key, model resolution, continuation tail,
    CWD cache, etc.). The next lane must address the **command surface**
    (run_impl, bg_impl, resolve_agent, _build_run_event, etc.) so the
    remaining ~55 session tests turn green."""

    # @trace FR-AUDIT-N+12-033
    def test_session_impl_module_doc_mentions_audit_n12(self) -> None:
        text = session_impl.__doc__ or ""
        assert "AUDIT-N+12" in text
        assert "Canonical home" in text or "canonical home" in text

    # @trace FR-AUDIT-N+12-034
    def test_observability_impl_module_doc_mentions_audit_n12(self) -> None:
        text = observability_impl.__doc__ or ""
        assert "AUDIT-N+12" in text or "WL-120" in text

    # @trace FR-AUDIT-N+12-035
    def test_observability_impl_wl120_kw_signature_marker_present(self) -> None:
        """The deprecated sentinel ``_wl120_kw_signature`` exists so
        backward-compat import sites don't crash."""
        assert hasattr(observability_impl, "_wl120_kw_signature")


# ---------------------------------------------------------------------------
# 8. Module-graph loads clean
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModuleGraphLoadsClean:
    """AUDIT-N+12: every touched module imports without side-effects."""

    # @trace FR-AUDIT-N+12-036
    def test_impl_module_loads(self) -> None:
        assert impl.__file__ is not None

    # @trace FR-AUDIT-N+12-037
    def test_session_impl_module_loads(self) -> None:
        assert session_impl.__file__ is not None

    # @trace FR-AUDIT-N+12-038
    def test_observability_impl_module_loads(self) -> None:
        assert observability_impl.__file__ is not None

    # @trace FR-AUDIT-N+12-039
    def test_session_impl_does_not_circular_import(self) -> None:
        """No circular import: importing impl re-exports session_impl."""
        # Already imported at module load time. Just check the canonical
        # home is the session_impl module.
        assert impl._is_pid_running.__module__ == "thegent.cli.commands.session_impl"
        assert impl._resolve_agent_model.__module__ == "thegent.cli.commands.session_impl"

    # @trace FR-AUDIT-N+12-040
    def test_observability_impl_dual_mode_bridges_present(self) -> None:
        """All four WL-125 dispatch bridges live in observability_impl
        and accept ``*args, **kwargs`` for forward-compat."""
        import inspect

        for name in (
            "_hash_observe_summary_payload",
            "_classify_observe_summary_trend_health",
            "_load_observe_summary_snapshots",
            "_append_observe_summary_snapshot",
        ):
            fn = getattr(observability_impl, name)
            sig = inspect.signature(fn)
            assert "args" in sig.parameters, f"{name} missing *args"
            assert "kwargs" in sig.parameters, f"{name} missing **kwargs"
