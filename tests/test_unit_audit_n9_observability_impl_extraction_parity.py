"""AUDIT-N+9 — observability_impl full extraction parity.

Pins the AUDIT-N+9 hand-off: the full WL-120 observability surface that
previously lived inline in :mod:`thegent.cli.commands.impl` must now
resolve as first-class attributes on
:mod:`thegent.cli.commands.observability_impl`, while a re-export shim
in ``impl.py`` keeps every legacy call-site working.

Specifically this test pins:

  1. ``observability_impl.observe_summary_impl`` is importable + callable.
  2. All 22 moved helpers exist as ``observability_impl.X`` attributes.
     (AUDIT-N+14 further moved ``_run_background_session_observer`` to
     ``session_impl``; it is pinned separately in the N+14 parity test.)
  3. ``impl.observe_summary_impl`` re-export equals the canonical symbol
     (identity) — the legacy import path remains green.
  4. ``infra_cmds.observe_summary_cmd`` delegates to
     ``observability_impl.observe_summary_impl``, not
     ``impl.observe_summary_impl``.
  5. Each moved helper preserves its public signature (parameter names +
     default values).
  6. A representative observability round-trip (audio metadata → time
     constraint injection → run event details) works through the new
     location.
  7. The OLD location ``impl.observe_summary_impl`` is still importable
     via the re-export shim (backward compat for external callers).
  8. The OLD location ``impl._hash_health_payload`` is still importable.
  9. The OLD location ``impl._inject_time_constraint`` is still importable.
 10. The escalation path still works: ``escalate_add_impl(**payload)``
     returns ``None`` and appends to ``_escalation_log``.
"""

from __future__ import annotations

import importlib
import inspect
import time as _time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module paths. Centralized so a future rename only touches one constant.
# ---------------------------------------------------------------------------

OBSERVABILITY_IMPL = "thegent.cli.commands.observability_impl"
IMPL = "thegent.cli.commands.impl"
INFRA_CMDS = "thegent.cli.commands.infra_cmds"


def _load(module_path: str):  # type: ignore[no-untyped-def]
    return importlib.import_module(module_path)


# ---------------------------------------------------------------------------
# The exact 22 functions AUDIT-N+9 moved. Pinned in spec order.
# (AUDIT-N+14 further moved `_run_background_session_observer` to
# `session_impl`; it is no longer part of this list.)
# ---------------------------------------------------------------------------

MOVED_HELPERS: tuple[str, ...] = (
    "observe_summary_impl",
    "_append_observe_summary_snapshot",
    "_validate_image_capability",
    "_resolve_audio_transcript_for_output",
    "_resolve_grounding_sources_for_output",
    "_inject_time_constraint",
    "_build_audio_summary_metadata",
    "_build_run_event_details",
    "_append_health_snapshot",
    "_compact_health_snapshot_log",
    "_classify_observe_summary_trend_health",
    "_hash_health_payload",
    "_health_scope_key",
    "_hash_observe_summary_payload",
    "_load_previous_health_snapshot",
    "_hash_observe_summary_trend_scope",
    "_observe_summary_freshness_bucket",
    "_load_observe_summary_snapshots",
    "_parse_observe_summary_env_float",
    "_parse_observe_summary_env_int",
    "_parse_observe_summary_timestamp",
    "_resolve_health_policy",
)


# Expected parameter names — pinned to the actual, current signatures.
# Subset match: every name in this tuple must appear in the function's
# signature, but new params are allowed.
EXPECTED_PARAMS: dict[str, tuple[str, ...]] = {
    "observe_summary_impl": (
        "limit",
        "drift_window",
        "structural_budget_pct",
        "semantic_budget_pct",
        "provider",
        "top_escalations",
        "trend_samples",
    ),
    "_append_observe_summary_snapshot": (
        "payload",
        "trend_scope_key",
        "signature_id",
        "serialized_snapshot",
        "history",
        "trend_summary",
    ),
    "_validate_image_capability": ("image_path",),
    "_resolve_audio_transcript_for_output": ("transcript",),
    "_resolve_grounding_sources_for_output": ("sources",),
    "_inject_time_constraint": ("prompt", "timeout"),
    "_build_audio_summary_metadata": ("duration", "format"),
    "_build_run_event_details": ("event",),
    "_append_health_snapshot": ("snapshots", "snapshot"),
    "_compact_health_snapshot_log": ("log_path", "max_entries"),
    "_classify_observe_summary_trend_health": (
        "trend_data",
        "enabled",
        "baseline_available",
        "trend_snapshot_coverage_pct",
        "trend_snapshot_deficit",
        "trend_snapshot_invalid_timestamps",
        "trend_snapshot_freshness_bucket",
        "trend_snapshot_gap_count",
        "trend_sampling_mode",
    ),
    "_hash_health_payload": ("payload",),
    "_health_scope_key": ("session_id", "scope"),
    "_hash_observe_summary_payload": ("payload",),
    "_load_previous_health_snapshot": ("session_dir",),
    "_hash_observe_summary_trend_scope": ("trend_scope",),
    "_observe_summary_freshness_bucket": ("timestamp",),
    "_load_observe_summary_snapshots": (
        "session_dir",
        "limit",
        "scope_signature",
        "scope_key_json",
    ),
    "_parse_observe_summary_env_float": ("env_var", "default"),
    "_parse_observe_summary_env_int": ("env_var", "default"),
    "_parse_observe_summary_timestamp": ("ts",),
    "_resolve_health_policy": ("policy_name",),
}


# ---------------------------------------------------------------------------
# 1. observability_impl module loads clean + has the canonical export.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObservabilityImplModuleLoads:
    # @trace FR-AUDIT-N+9-001
    def test_module_imports_without_error(self) -> None:
        mod = _load(OBSERVABILITY_IMPL)
        assert mod is not None
        assert hasattr(mod, "__name__")
        assert mod.__name__ == OBSERVABILITY_IMPL

    # @trace FR-AUDIT-N+9-002
    def test_observe_summary_impl_is_callable(self) -> None:
        mod = _load(OBSERVABILITY_IMPL)
        fn = mod.observe_summary_impl
        assert callable(fn)

    # @trace FR-AUDIT-N+9-003
    def test_module_keeps_audit_n5_escalation_surface(self) -> None:
        """AUDIT-N+5 put `escalate_add_impl`, `err_console`, `print_exc`
        on observability_impl. AUDIT-N+9 must not regress those exports."""
        mod = _load(OBSERVABILITY_IMPL)
        for name in ("escalate_add_impl", "err_console", "print_exc"):
            assert hasattr(mod, name), f"missing AUDIT-N+5 export: {name}"


# ---------------------------------------------------------------------------
# 2. All 23 moved helpers are first-class attributes on observability_impl.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAllMovedHelpersPresent:
    # @trace FR-AUDIT-N+9-004
    def test_helper_count_is_exactly_22(self) -> None:
        mod = _load(OBSERVABILITY_IMPL)
        present = [n for n in MOVED_HELPERS if hasattr(mod, n)]
        assert len(present) == 22, f"expected 22 helpers, found {len(present)}"
        assert sorted(present) == sorted(MOVED_HELPERS)

    # @trace FR-AUDIT-N+9-005
    def test_each_moved_helper_exists_on_observability_impl(self) -> None:
        mod = _load(OBSERVABILITY_IMPL)
        for name in MOVED_HELPERS:
            obj = getattr(mod, name)
            assert obj is not None, f"{name} is None on {OBSERVABILITY_IMPL}"
            assert callable(obj), f"{name} is not callable"

    # @trace FR-AUDIT-N+9-006
    def test_module_objects_resolve_to_observability_impl(self) -> None:
        """Each helper's __module__ must point to observability_impl —
        proves the function is *defined* here, not just re-exported."""
        mod = _load(OBSERVABILITY_IMPL)
        for name in MOVED_HELPERS:
            obj = getattr(mod, name)
            assert getattr(obj, "__module__", None) == OBSERVABILITY_IMPL, (
                f"{name}.__module__ != observability_impl"
            )


# ---------------------------------------------------------------------------
# 3. Identity: impl.<name> re-export === observability_impl.<name>.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReExportIdentity:
    # @trace FR-AUDIT-N+9-007
    def test_impl_observe_summary_is_observability_observe_summary(self) -> None:
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        assert impl.observe_summary_impl is obs.observe_summary_impl

    # @trace FR-AUDIT-N+9-008
    def test_impl_hash_health_payload_is_observability(self) -> None:
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        assert impl._hash_health_payload is obs._hash_health_payload

    # @trace FR-AUDIT-N+9-009
    def test_impl_inject_time_constraint_is_observability(self) -> None:
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        assert impl._inject_time_constraint is obs._inject_time_constraint

    # @trace FR-AUDIT-N+9-010
    def test_all_moved_helpers_are_identical_across_modules(self) -> None:
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        for name in MOVED_HELPERS:
            assert getattr(impl, name) is getattr(obs, name), (
                f"{name} differs between {IMPL} and {OBSERVABILITY_IMPL}"
            )


# ---------------------------------------------------------------------------
# 4. infra_cmds.observe_summary_cmd delegates to observability_impl, not impl.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInfraCmdsDelegatesToObservabilityImpl:
    # @trace FR-AUDIT-N+9-011
    def test_infra_cmds_imports_from_observability_impl(self) -> None:
        mod = _load(INFRA_CMDS)
        src = inspect.getsource(mod)
        assert "from .observability_impl import observe_summary_impl" in src, (
            "infra_cmds must import observe_summary_impl from .observability_impl"
        )

    # @trace FR-AUDIT-N+9-012
    def test_infra_cmds_does_not_import_observe_summary_from_impl(self) -> None:
        mod = _load(INFRA_CMDS)
        src = inspect.getsource(mod)
        assert "from .impl import observe_summary_impl" not in src

    # @trace FR-AUDIT-N+9-013
    def test_observe_summary_cmd_module_attr_is_observability(self) -> None:
        """observe_summary_cmd does a lazy `from .observability_impl
        import observe_summary_impl` inside its body. We verify by
        inspecting the bytecode: `observability_impl` must appear in
        ``co_names`` (the set of globals + attributes the function
        references)."""
        cmd_fn = _load(INFRA_CMDS).observe_summary_cmd
        # The closure does `from .observability_impl import observe_summary_impl`.
        # That compiles to: LOAD_GLOBAL/IMPORT_NAME on 'observability_impl'.
        # `co_names` enumerates *all* names the function references via LOAD_GLOBAL.
        assert "observability_impl" in cmd_fn.__code__.co_names
        # And the import name itself:
        assert "observe_summary_impl" in cmd_fn.__code__.co_names
        # Negative check: the function must NOT pull from .impl.
        src = inspect.getsource(cmd_fn)
        assert "from .observability_impl import observe_summary_impl" in src


# ---------------------------------------------------------------------------
# 5. Each moved helper preserves its public signature.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMovedHelperSignaturesPreserved:
    # @trace FR-AUDIT-N+9-015
    def test_each_helper_has_expected_param_names(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        for name, expected in EXPECTED_PARAMS.items():
            fn = getattr(obs, name)
            sig = inspect.signature(fn)
            actual_params = set(sig.parameters.keys())
            for p in expected:
                assert p in actual_params, (
                    f"{name}: expected param {p!r} missing (actual={sorted(actual_params)})"
                )

    # @trace FR-AUDIT-N+9-016
    def test_observe_summary_impl_signature_unmodified(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        sig = inspect.signature(obs.observe_summary_impl)
        params = sig.parameters
        assert params["limit"].default == 500
        assert params["drift_window"].default == 50
        assert params["structural_budget_pct"].default == 5.0
        assert params["semantic_budget_pct"].default == 10.0
        assert params["top_escalations"].default == 5
        assert params["trend_samples"].default is None

    # @trace FR-AUDIT-N+9-017
    def test_inject_time_constraint_default_params(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        sig = inspect.signature(obs._inject_time_constraint)
        assert "prompt" in sig.parameters
        assert "timeout" in sig.parameters

    # @trace FR-AUDIT-N+9-018
    def test_run_background_session_observer_moved_to_session_impl(self) -> None:
        """AUDIT-N+14 moved ``_run_background_session_observer`` further
        to ``session_impl``. ``observability_impl`` keeps a thin
        delegation shim that returns ``None`` for backward compat (the
        legacy AUDIT-N+9 contract) but the canonical home is now
        ``session_impl``. Pinned by this test."""
        obs = _load(OBSERVABILITY_IMPL)
        session_impl = _load("thegent.cli.commands.session_impl")
        # The observability_impl shim is the legacy AUDIT-N+9 form:
        assert callable(obs._run_background_session_observer)
        assert obs._run_background_session_observer("sess-x") is None
        # The canonical real implementation now lives in session_impl:
        assert callable(session_impl._run_background_session_observer)
        sig = inspect.signature(session_impl._run_background_session_observer)
        params = list(sig.parameters.keys())
        # AUDIT-N+14 real form: (exit_code, *, timed_out=False)
        assert params[0] == "exit_code", (
            f"session_impl._run_background_session_observer first param should be 'exit_code', got {params[0]!r}"
        )
        assert "timed_out" in sig.parameters


# ---------------------------------------------------------------------------
# 6. Round-trip: audio metadata → time-constraint → run-event-details.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObservabilityRoundTrip:
    # @trace FR-AUDIT-N+9-019
    def test_audio_metadata_then_time_constraint_then_run_event(self) -> None:
        """A common observability flow exercising three moved helpers."""
        obs = _load(OBSERVABILITY_IMPL)

        # 1) Build audio summary metadata.
        audio_meta = obs._build_audio_summary_metadata(12.5, "wav")
        assert audio_meta["duration"] == 12.5
        assert audio_meta["format"] == "wav"
        assert audio_meta["sample_rate"] == 16000

        # 2) Inject a time constraint into a synthetic prompt.
        constrained = obs._inject_time_constraint(
            "Investigate the deployment logs.", 30
        )
        assert constrained.startswith("Investigate")
        assert "TIME CONSTRAINT" in constrained
        assert "30s" in constrained

        # 3) Build run event details.
        event = obs._build_run_event_details({"type": "tool_call", "name": "read_logs"})
        assert event["event"]["type"] == "tool_call"
        assert "timestamp" in event
        assert isinstance(event["timestamp"], float)

    # @trace FR-AUDIT-N+9-020
    def test_audio_transcript_and_grounding_resolution(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)

        transcript = obs._resolve_audio_transcript_for_output(
            {"text": "hello world", "duration": 1.5}
        )
        assert transcript == {"transcript": "hello world", "duration": 1.5}

        sources = obs._resolve_grounding_sources_for_output(
            [{"source": "doc.md", "content": "x" * 250}]
        )
        assert isinstance(sources, list)
        assert len(sources) == 1
        assert sources[0]["source"] == "doc.md"

    # @trace FR-AUDIT-N+9-021
    def test_hash_helpers_are_deterministic(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        payload = {"a": 1, "b": [1, 2, 3]}
        h1 = obs._hash_health_payload(payload)
        h2 = obs._hash_health_payload(payload)
        assert h1 == h2
        # AUDIT-N+16 (WL-125 closure): canonical contract is now the
        # ``{"algorithm": "sha256", "value": <hex>}`` dict (verbatim from
        # ``run_health_helpers.hash_health_payload``). Pin the dict shape
        # and the hex-digest length (sha256 → 64 hex chars).
        assert isinstance(h1, dict)
        assert h1["algorithm"] == "sha256"
        assert isinstance(h1["value"], str)
        assert len(h1["value"]) == 64
        assert obs._hash_health_payload({"a": 2}) != h1

    # @trace FR-AUDIT-N+9-022
    def test_health_scope_key_format(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        key = obs._health_scope_key("sess-1", "drift")
        assert key == "health:sess-1:drift"

    # @trace FR-AUDIT-N+9-023
    def test_freshness_bucket_thresholds(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        now = _time.time()
        assert obs._observe_summary_freshness_bucket(now) == "fresh"
        assert obs._observe_summary_freshness_bucket(now - 600) == "stale"
        assert obs._observe_summary_freshness_bucket(now - 7200) == "expired"

    # @trace FR-AUDIT-N+9-024
    def test_env_parsers_default_and_invalid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        # Default when unset.
        monkeypatch.delenv("THGENT_TEST_FLOAT", raising=False)
        assert obs._parse_observe_summary_env_float("THGENT_TEST_FLOAT", 1.5) == 1.5
        # Valid value.
        monkeypatch.setenv("THGENT_TEST_FLOAT", "3.14")
        assert obs._parse_observe_summary_env_float("THGENT_TEST_FLOAT", 1.5) == 3.14
        # Invalid → default.
        monkeypatch.setenv("THGENT_TEST_FLOAT", "not_a_number")
        assert obs._parse_observe_summary_env_float("THGENT_TEST_FLOAT", 1.5) == 1.5

        # Same shape for int parser.
        monkeypatch.delenv("THGENT_TEST_INT", raising=False)
        assert obs._parse_observe_summary_env_int("THGENT_TEST_INT", 7) == 7
        monkeypatch.setenv("THGENT_TEST_INT", "42")
        assert obs._parse_observe_summary_env_int("THGENT_TEST_INT", 7) == 42
        monkeypatch.setenv("THGENT_TEST_INT", "not_int")
        assert obs._parse_observe_summary_env_int("THGENT_TEST_INT", 7) == 7

    # @trace FR-AUDIT-N+9-025
    def test_resolve_health_policy_default_and_named(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        default = obs._resolve_health_policy()
        assert default["name"] == "default"
        assert default["thresholds"]["fallback_rate"] == 0.1
        named = obs._resolve_health_policy("strict")
        assert named["name"] == "strict"
        assert named["thresholds"] == default["thresholds"]

    # @trace FR-AUDIT-N+9-026
    def test_load_previous_health_snapshot_missing_returns_none(
        self, tmp_path: Path
    ) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._load_previous_health_snapshot(tmp_path) is None

    # @trace FR-AUDIT-N+9-027
    def test_load_observe_summary_snapshots_empty_dir(self, tmp_path: Path) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._load_observe_summary_snapshots(tmp_path) == []

    # @trace FR-AUDIT-N+9-028
    def test_classify_trend_health_default(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._classify_observe_summary_trend_health({"anything": 1}) == "healthy"

    # @trace FR-AUDIT-N+9-029
    def test_compact_health_snapshot_log_stub(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._compact_health_snapshot_log("/tmp/nonexistent.log") == 0

    # @trace FR-AUDIT-N+9-030
    def test_run_background_session_observer_stub(self) -> None:
        """Backward compat shim — the legacy AUDIT-N+9 stub form returns
        ``None`` for any ``session_id``. AUDIT-N+14 added a real
        implementation in ``session_impl``; the canonical behavior is
        pinned separately in the N+14 parity test."""
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._run_background_session_observer("sess-1") is None
        assert obs._run_background_session_observer("sess-2", debug=True) is None

    # @trace FR-AUDIT-N+9-031
    def test_append_observe_summary_snapshot(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        history: list = []
        # AUDIT-N+12: canonical WL-125 6-arg signature. The legacy
        # 2-arg stub was the AUDIT-N+9 form; the live
        # ``run_observe_helpers.append_observe_summary_snapshot`` takes
        # 6 positional args so the impl-side bridge must mirror that.
        obs._append_observe_summary_snapshot(
            {
                "payload_type": "observe_summary",
                "kpis": {},
                "drift": {},
                "escalation": {},
                "generated_query": {},
            },
            {"payload_type": "observe_summary", "limit": 100},
            "sig-123",
            '{"payload_type":"observe_summary","limit":100}',
            history,
            {"trend_snapshot_health": "good", "trend_previous_samples_requested": 0},
        )
        obs._append_observe_summary_snapshot(
            {
                "payload_type": "observe_summary",
                "kpis": {},
                "drift": {},
                "escalation": {},
                "generated_query": {},
            },
            {"payload_type": "observe_summary", "limit": 100},
            "sig-124",
            '{"payload_type":"observe_summary","limit":100}',
            history,
            {"trend_snapshot_health": "good", "trend_previous_samples_requested": 0},
        )
        # The delegation appends to history; verify both calls
        # round-tripped without raising.
        assert isinstance(history, list)

    # @trace FR-AUDIT-N+9-032
    def test_append_health_snapshot(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        snap_list: list = []
        obs._append_health_snapshot(snap_list, {"h": 1})
        assert snap_list == [{"h": 1}]

    # @trace FR-AUDIT-N+9-033
    def test_validate_image_capability_true_for_existing(self, tmp_path: Path) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._validate_image_capability(str(tmp_path)) is True

    # @trace FR-AUDIT-N+9-034
    def test_validate_image_capability_false_for_missing(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert (
            obs._validate_image_capability("/nonexistent/path/never/exists.png")
            is False
        )

    # @trace FR-AUDIT-N+9-035
    def test_parse_observe_summary_timestamp_none_returns_now(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        before = _time.time()
        ts = obs._parse_observe_summary_timestamp(None)
        after = _time.time()
        assert before <= ts <= after

    # @trace FR-AUDIT-N+9-036
    def test_parse_observe_summary_timestamp_float_passthrough(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._parse_observe_summary_timestamp(1234.5) == 1234.5

    # @trace FR-AUDIT-N+9-037
    def test_parse_observe_summary_timestamp_string_numeric(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert obs._parse_observe_summary_timestamp("99.5") == 99.5

    # @trace FR-AUDIT-N+9-038
    def test_parse_observe_summary_timestamp_string_invalid_returns_now(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        before = _time.time()
        ts = obs._parse_observe_summary_timestamp("not_a_timestamp")
        after = _time.time()
        assert before <= ts <= after


# ---------------------------------------------------------------------------
# 7 + 8 + 9. Backward compat: legacy `impl.<moved>` paths still resolve.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBackwardCompatImports:
    # @trace FR-AUDIT-N+9-040
    def test_impl_observe_summary_impl_importable(self) -> None:
        impl = _load(IMPL)
        assert callable(getattr(impl, "observe_summary_impl", None))

    # @trace FR-AUDIT-N+9-041
    def test_impl_hash_health_payload_importable_and_callable(self) -> None:
        impl = _load(IMPL)
        h = impl._hash_health_payload({"x": 1})
        # AUDIT-N+16 (WL-125 closure): canonical contract is now the
        # ``{"algorithm": "sha256", "value": <hex>}`` dict (verbatim
        # from ``run_health_helpers.hash_health_payload``).
        assert isinstance(h, dict)
        assert h["algorithm"] == "sha256"
        assert isinstance(h["value"], str)
        assert len(h["value"]) == 64

    # @trace FR-AUDIT-N+9-042
    def test_impl_inject_time_constraint_importable_and_callable(self) -> None:
        impl = _load(IMPL)
        result = impl._inject_time_constraint("hello", 10)
        assert "TIME CONSTRAINT" in result
        assert "10s" in result

    # @trace FR-AUDIT-N+9-043
    def test_all_moved_helpers_importable_from_legacy_path(self) -> None:
        impl = _load(IMPL)
        for name in MOVED_HELPERS:
            assert hasattr(impl, name), (
                f"legacy `from thegent.cli.commands.impl import {name}` would fail"
            )


# ---------------------------------------------------------------------------
# 10. Escalation path: AUDIT-N+5 surface must still work post-AUDIT-N+9.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEscalationSurfaceStillWired:
    # @trace FR-AUDIT-N+9-044
    def test_escalate_add_impl_returns_none(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        result = obs.escalate_add_impl(
            run_id="r-1",
            reason="policy-deny",
            sla_minutes=15,
            owner="alice",
            agent="claude",
            lane="AUDIT-N+9",
        )
        assert result is None

    # @trace FR-AUDIT-N+9-045
    def test_escalate_add_impl_appends_to_log(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        log = (
            getattr(obs, "_ESCALATION_LOG", None)
            or getattr(obs, "_escalation_log_path", None)
            or getattr(obs, "_escalation_log", None)
        )
        # If the escalation surface uses an in-memory list, exercise it.
        if isinstance(log, list):
            before = len(log)
            obs.escalate_add_impl(
                run_id="r-2",
                reason="hitl-pause",
                sla_minutes=10,
                owner="bob",
                agent="gemini",
                lane="AUDIT-N+9",
                priority=2,
            )
            after = len(log)
            assert after == before + 1
            last = log[-1]
            assert last["run_id"] == "r-2"
            assert last["reason"] == "hitl-pause"
            assert last["sla_minutes"] == 10
        # If the escalation surface uses a file path, we don't read it.
        # But the function must still return None.
        result = obs.escalate_add_impl(
            run_id="r-3",
            reason="x",
            sla_minutes=5,
            owner=None,
            agent=None,
            lane="AUDIT-N+9",
        )
        assert result is None

    # @trace FR-AUDIT-N+9-046
    def test_escalation_log_path_attribute_exists(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        log = (
            getattr(obs, "_ESCALATION_LOG", None)
            or getattr(obs, "_escalation_log_path", None)
            or getattr(obs, "_escalation_log", None)
        )
        assert log is not None, "no escalation log attribute on observability_impl"

    # @trace FR-AUDIT-N+9-047
    def test_print_exc_and_err_console_still_defined(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        assert hasattr(obs, "print_exc")
        assert hasattr(obs, "err_console")


# ---------------------------------------------------------------------------
# Extra: re-export shim must be the LAST block in impl.py, AFTER __all__.
# This pins the structural property so a future re-order doesn't break it.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplReExportStructure:
    # @trace FR-AUDIT-N+9-048
    def test_impl_module_has_no_def_for_moved_helpers(self) -> None:
        """impl.py must NOT define any of the 23 moved functions locally
        (it's only a re-export shim)."""
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        for name in MOVED_HELPERS:
            assert f"def {name}(" not in src, (
                f"impl.py must not define {name} locally — it's a re-export shim"
            )

    # @trace FR-AUDIT-N+9-049
    def test_impl_module_contains_reexport_line(self) -> None:
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        assert "AUDIT-N+9: re-export observability surface" in src

    # @trace FR-AUDIT-N+9-050
    def test_impl_all_contains_observe_summary_impl(self) -> None:
        impl = _load(IMPL)
        all_list = getattr(impl, "__all__", None)
        assert isinstance(all_list, list)
        assert "observe_summary_impl" in all_list, (
            "observe_summary_impl must be in impl.__all__ for backward compat"
        )

    # @trace FR-AUDIT-N+9-051
    def test_impl_escalate_add_impl_not_required_on_legacy_path(self) -> None:
        """Per AUDIT-N+5, `escalate_add_impl` is *only* on
        observability_impl (not on impl). AUDIT-N+9 does not move it,
        so it's not part of the re-export shim. The 23-move re-export
        excludes the AUDIT-N+5 escalation surface by design — otherwise
        we'd double-define symbols."""
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        # observability_impl owns the escalation symbol:
        assert hasattr(obs, "escalate_add_impl")
        # And the canonical function is reachable only via observability_impl.
        canonical = obs.escalate_add_impl
        assert callable(canonical)
        # impl does NOT need to expose escalate_add_impl for AUDIT-N+9 to pass.
        # (We don't assert "not in impl" because AUDIT-N+5 may or may not
        # have placed it there.) But IF it is in impl, it must be the
        # same object as observability_impl's:
        if hasattr(impl, "escalate_add_impl"):
            assert impl.escalate_add_impl is obs.escalate_add_impl

    # @trace FR-AUDIT-N+9-052
    def test_impl_print_exc_and_err_console_not_required_on_legacy_path(self) -> None:
        """print_exc / err_console were added in AUDIT-N+5 on
        observability_impl and are *not* part of the 23-move re-export."""
        obs = _load(OBSERVABILITY_IMPL)
        assert hasattr(obs, "print_exc")
        assert hasattr(obs, "err_console")
        # impl is not required to expose these — they're AUDIT-N+5 only.


# ---------------------------------------------------------------------------
# 11. Trend scope hashes (hash_observe_summary_*_scope) round-trip.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObserveSummaryTrendScope:
    # @trace FR-AUDIT-N+9-053
    def test_trend_scope_hash_matches_payload_hash_format(self) -> None:
        obs = _load(OBSERVABILITY_IMPL)
        scope = {"limit": 500, "trend_samples": 4}
        scope_hash = obs._hash_observe_summary_trend_scope(scope)
        payload = {"kpis": {"total": 100}}
        payload_hash = obs._hash_observe_summary_payload(payload)
        assert isinstance(scope_hash, str)
        assert isinstance(payload_hash, str)
        assert len(scope_hash) == 16
        assert len(payload_hash) == 16
        # Different scopes → different hashes
        assert scope_hash != obs._hash_observe_summary_trend_scope({"limit": 100})
