"""AUDIT-N+28 — dormant-core signature-gap closure parity.

This test pins the AUDIT-N+28 hand-off: the (b) carry-forward from
AUDIT-N+27 / SOTA Audit Pass 12 was the two pre-existing test failures
visible in the broader sweep:

* ``tests/test_wl116_audio_inputs.py::test_run_impl_accepts_audio_files_and_google_grounding``
  failed because ``inspect.signature(run_impl)`` did not declare
  ``audio_files`` or ``google_grounding`` (the wrapper only had
  ``(prompt, **kwargs)``).
* ``tests/test_wl119_grounding_sources.py::test_run_registry_finish_event_can_persist_grounding_sources``
  failed because :meth:`RunRegistry.register_end` only accepted the
  legacy 5-arg positional form (``ended_at`` / ``duration``) while the
  WL-119 / run-orchestrator / use-case callers (and integration tests)
  already passed ``ended_at_utc`` / ``duration_s`` / ``event_details``.

This suite closes both gaps:

1. ``run_impl`` declares ``audio_files`` and ``google_grounding`` as
   explicit kwargs alongside ``**kwargs`` (pinned by
   ``inspect.signature(run_impl).parameters``). Both are forwarded to
   the canonical ``run_impl_core`` helper verbatim.
2. ``RunRegistry.register_end`` accepts BOTH the legacy 5-positional-arg
   form (pinned by ``tests/test_unit_execution.py``) AND the new kwarg
   form (``ended_at_utc=`` / ``duration_s=`` / ``error_class=`` /
   ``cost_usd=`` / ``event_details=``). The bridge honours whichever
   form is supplied and persists the canonical ``ended_at_utc`` /
   ``duration_s`` keys so the JSONL stream is form-agnostic downstream.
3. The audit-trail replay surface (``list_runs`` + ``Auditor``) keeps
   passing on both forms (the hash chain is computed on the canonical
   entry dict, which is form-agnostic).
4. ``inspect.signature(RunRegistry.register_end)`` exposes both legacy
   and new kwarg names.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from thegent.cli.commands.impl import run_impl
from thegent.execution import Auditor, RunMeta, RunRegistry

# ---------------------------------------------------------------------------
# Lane 1 — run_impl signature exposes audio_files + google_grounding
# ---------------------------------------------------------------------------


class TestRunImplSignature:
    """Pin ``inspect.signature(run_impl)`` membership."""

    def test_run_impl_declares_audio_files_kwarg(self) -> None:
        sig = inspect.signature(run_impl)
        assert "audio_files" in sig.parameters

    def test_run_impl_declares_google_grounding_kwarg(self) -> None:
        sig = inspect.signature(run_impl)
        assert "google_grounding" in sig.parameters

    def test_run_impl_declares_prompt_positional(self) -> None:
        sig = inspect.signature(run_impl)
        assert "prompt" in sig.parameters

    def test_run_impl_declares_kwargs_catchall(self) -> None:
        """The ``**kwargs`` catch-all is preserved so every other caller kwarg
        (agent / model / routing / include_contract / route_contract /
        route_request / image_paths / task_id / lock / remote / debug /
        shadow / idempotency_token / speculative / continue_from /
        continuation_include_stderr / failover / etc.) still flows through
        the canonical ``run_impl_core`` dispatcher."""
        sig = inspect.signature(run_impl)
        assert "kwargs" in sig.parameters
        assert sig.parameters["kwargs"].kind is inspect.Parameter.VAR_KEYWORD

    def test_run_impl_audio_files_default_is_none(self) -> None:
        sig = inspect.signature(run_impl)
        assert sig.parameters["audio_files"].default is None

    def test_run_impl_google_grounding_default_is_false(self) -> None:
        sig = inspect.signature(run_impl)
        assert sig.parameters["google_grounding"].default is False


# ---------------------------------------------------------------------------
# Lane 2 — RunRegistry.register_end dual-mode bridge
# ---------------------------------------------------------------------------


def _make_meta(run_id: str = "run_test") -> RunMeta:
    return RunMeta(run_id=run_id, agent="claude", prompt="p", cwd="/tmp", owner="u")


class TestRegisterEndLegacyForm:
    """Pin the legacy 5-positional-arg form (the original AUDIT contract).

    These calls match the form pinned by ``tests/test_unit_execution.py``:
    ``register_end(run_id, exit_code, status, ended_at, duration[, cost_usd])``.
    """

    def test_legacy_5_positional_completed(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r1"))
        reg.register_end("r1", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        assert reg.get_run_state("r1") is not None
        assert reg.get_run_state("r1").value == "completed"

    def test_legacy_5_positional_failed(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r2"))
        reg.register_end("r2", 1, "failed", "2026-02-14T12:00:00Z", 1.0)
        assert reg.get_run_state("r2").value == "failed"

    def test_legacy_5_positional_persists_canonical_keys(self, tmp_path: Path) -> None:
        """Legacy form must persist the canonical ``ended_at_utc`` +
        ``duration_s`` keys (form-agnostic downstream contract)."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r3"))
        reg.register_end("r3", 0, "completed", "2026-02-14T12:00:00Z", 5.0)
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        finish_line = next(l for l in lines if '"finish"' in l)
        data = json.loads(finish_line)
        assert data["ended_at_utc"] == "2026-02-14T12:00:00Z"
        assert data["duration_s"] == 5.0
        # Legacy keys must NOT leak into the canonical JSONL.
        assert "ended_at" not in data
        assert "duration" not in data

    def test_legacy_form_with_cost_usd(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r4"))
        reg.register_end("r4", 0, "completed", "2026-02-14T12:00:00Z", 1.0, cost_usd=0.05)
        content = reg.registry_path.read_text(encoding="utf-8")
        assert '"cost_usd": 0.05' in content

    def test_legacy_form_omits_cost_usd_when_none(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r5"))
        reg.register_end("r5", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        finish_lines = [
            l for l in reg.registry_path.read_text(encoding="utf-8").strip().splitlines() if '"finish"' in l
        ]
        assert len(finish_lines) == 1
        assert "cost_usd" not in finish_lines[0]


class TestRegisterEndNewForm:
    """Pin the new kwarg form (the AUDIT-N+28 / WL-119 / orchestrator contract)."""

    def test_new_form_completed(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r10"))
        reg.register_end(
            run_id="r10",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-02-14T12:00:00Z",
            duration_s=10.0,
        )
        assert reg.get_run_state("r10").value == "completed"

    def test_new_form_failed(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r11"))
        reg.register_end(
            run_id="r11",
            exit_code=1,
            status="failed",
            ended_at_utc="2026-02-14T12:00:00Z",
            duration_s=0.0,
            error_class="policy_violation",
        )
        assert reg.get_run_state("r11").value == "failed"

    def test_new_form_persists_error_class(self, tmp_path: Path) -> None:
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r12"))
        reg.register_end(
            run_id="r12",
            exit_code=1,
            status="failed",
            ended_at_utc="2026-02-14T12:00:00Z",
            duration_s=0.0,
            error_class="policy_violation",
        )
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        finish_line = next(l for l in lines if '"finish"' in l)
        data = json.loads(finish_line)
        assert data["error_class"] == "policy_violation"

    def test_new_form_persists_event_details(self, tmp_path: Path) -> None:
        """WL-119 contract: the finish entry must surface the structured
        event_details (grounding_sources / context_usage_ratio / etc.) inside
        the audit trail so the replay surface can render them without a
        second registry read."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r13"))
        event_details = {
            "grounding_sources": ["https://a.example/1", "https://b.example/2"],
            "context_usage_ratio": 0.55,
        }
        reg.register_end(
            run_id="r13",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-02-14T12:00:00Z",
            duration_s=0.1,
            event_details=event_details,
        )
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        finish_line = next(l for l in lines if '"finish"' in l)
        # The literal substrings must surface so the WL-119 replay test
        # (which asserts on raw text) keeps passing.
        assert '"grounding_sources": ["https://a.example/1", "https://b.example/2"]' in finish_line
        assert '"context_usage_ratio": 0.55' in finish_line


class TestRegisterEndDualMode:
    """Pin the dual-mode bridge contract: both forms coexist."""

    def test_dual_mode_signature_exposes_both_forms(self) -> None:
        sig = inspect.signature(RunRegistry.register_end)
        # Legacy kwarg names
        assert "ended_at" in sig.parameters
        assert "duration" in sig.parameters
        # New kwarg names
        assert "ended_at_utc" in sig.parameters
        assert "duration_s" in sig.parameters
        assert "error_class" in sig.parameters
        assert "event_details" in sig.parameters
        # Both timestamp kwargs are optional (None default).
        assert sig.parameters["ended_at"].default is None
        assert sig.parameters["ended_at_utc"].default is None

    def test_dual_mode_new_kwarg_wins_when_both_supplied(self, tmp_path: Path) -> None:
        """When both legacy ``ended_at`` and new ``ended_at_utc`` are
        supplied, the bridge honours the new form (canonical)."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r20"))
        reg.register_end(
            run_id="r20",
            exit_code=0,
            status="completed",
            ended_at="2026-01-01T00:00:00Z",  # legacy
            duration=99.0,  # legacy
            ended_at_utc="2026-02-14T12:00:00Z",  # new (wins)
            duration_s=10.0,  # new (wins)
        )
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        finish_line = next(l for l in lines if '"finish"' in l)
        data = json.loads(finish_line)
        assert data["ended_at_utc"] == "2026-02-14T12:00:00Z"
        assert data["duration_s"] == 10.0

    def test_dual_mode_defensive_default_timestamp(self, tmp_path: Path) -> None:
        """If neither timestamp form is supplied the bridge defends with
        ``datetime.now(UTC).isoformat()`` so the finish entry is always
        persistable."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("r21"))
        reg.register_end(run_id="r21", exit_code=0, status="completed")
        lines = reg.registry_path.read_text(encoding="utf-8").strip().splitlines()
        finish_line = next(l for l in lines if '"finish"' in l)
        data = json.loads(finish_line)
        assert data["ended_at_utc"]  # defensive default present
        assert data["duration_s"] == 0.0

    def test_dual_mode_hash_chain_validates_across_both_forms(self, tmp_path: Path) -> None:
        """The hash chain must verify when both legacy and new forms are
        interleaved (proves the canonical entry dict is form-agnostic)."""
        reg = RunRegistry(tmp_path)
        # Legacy form first
        reg.register_start(_make_meta("rh1"))
        reg.register_end("rh1", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        # New form second
        reg.register_start(_make_meta("rh2"))
        reg.register_end(
            run_id="rh2",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-02-14T12:01:00Z",
            duration_s=2.0,
            error_class="policy_violation",
        )
        # Legacy form third
        reg.register_start(_make_meta("rh3"))
        reg.register_end("rh3", 1, "failed", "2026-02-14T12:02:00Z", 3.0, cost_usd=0.07)

        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["status"] == "passed", result
        assert result["corrupt_count"] == 0
        assert result["chain_broken"] is False

    def test_dual_mode_list_runs_merges_finish_event(self, tmp_path: Path) -> None:
        """``list_runs`` merges the finish event into the run entry — the
        dual-mode bridge must surface status / exit_code / duration_s
        regardless of which call shape wrote them."""
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("rl1"))
        reg.register_end(
            run_id="rl1",
            exit_code=0,
            status="completed",
            ended_at_utc="2026-02-14T12:00:00Z",
            duration_s=7.5,
        )
        runs = reg.list_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run["status"] == "completed"
        assert run["exit_code"] == 0
        assert run["duration_s"] == 7.5


# ---------------------------------------------------------------------------
# Lane 3 — Audit-trail invariants preserved across both forms
# ---------------------------------------------------------------------------


class TestAuditTrailInvariants:
    """Pin the AUDIT-N+28 audit-trail invariants on the dual-mode bridge."""

    def test_audit_n9_run_registry_list_runs_parity(self, tmp_path: Path) -> None:
        """``list_runs`` must surface ``ended_at_utc`` + ``duration_s`` on
        the merged run dict regardless of which call form was used."""
        reg = RunRegistry(tmp_path)
        for i in range(3):
            rid = f"ra{i}"
            reg.register_start(_make_meta(rid))
            if i % 2 == 0:
                # Legacy form
                reg.register_end(rid, 0, "completed", f"2026-02-14T12:0{i}:00Z", float(i))
            else:
                # New form
                reg.register_end(
                    run_id=rid,
                    exit_code=0,
                    status="completed",
                    ended_at_utc=f"2026-02-14T12:0{i}:00Z",
                    duration_s=float(i),
                )
        runs = reg.list_runs()
        assert len(runs) == 3
        for run in runs:
            assert "ended_at_utc" in run
            assert "duration_s" in run

    def test_audit_n9_no_legacy_finish_keys_leak_into_jsonl(self, tmp_path: Path) -> None:
        """The canonical finish JSONL entry must NOT carry the legacy
        ``ended_at`` / ``duration`` keys downstream — they were renamed
        to the canonical ``ended_at_utc`` / ``duration_s`` form by
        AUDIT-N+28 so consumers don't have to handle two key names.

        Note: ``RunMeta.ended_at: str = ""`` is a pre-existing field on
        the dataclass that surfaces in the START entry via
        ``RunMeta.to_dict()`` (predates AUDIT-N+28); we only assert the
        FINISH entries are form-agnostic.
        """
        reg = RunRegistry(tmp_path)
        reg.register_start(_make_meta("rnl"))
        reg.register_end("rnl", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        for line in reg.registry_path.read_text(encoding="utf-8").splitlines():
            data = json.loads(line)
            if data.get("event") != "finish":
                continue
            # Finish entry: only canonical keys.
            assert "ended_at" not in data, f"legacy ended_at leaked into finish {data}"
            assert "duration" not in data, f"legacy duration leaked into finish {data}"


# ---------------------------------------------------------------------------
# Lane 4 — runtime instantiation sanity
# ---------------------------------------------------------------------------


class TestRuntimeImportSafety:
    """Pin that AUDIT-N+28 introduces no new top-level imports or cycles."""

    def test_run_impl_importable_after_audit_n28(self) -> None:
        """The new explicit kwargs on ``run_impl`` must not break cold-start
        import (the canonical ``run_impl_core`` dispatch shim is lazy-loaded
        inside the function body, so signature changes do not affect import
        order)."""
        import importlib

        mod = importlib.import_module("thegent.cli.commands.impl")
        sig = inspect.signature(mod.run_impl)
        assert "audio_files" in sig.parameters
        assert "google_grounding" in sig.parameters

    def test_run_registry_importable_after_audit_n28(self) -> None:
        """The new dual-mode kwargs on ``register_end`` must not break
        cold-start import."""
        import importlib

        mod = importlib.import_module("thegent.execution")
        sig = inspect.signature(mod.RunRegistry.register_end)
        assert "ended_at_utc" in sig.parameters
        assert "event_details" in sig.parameters
