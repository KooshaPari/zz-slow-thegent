"""AUDIT-N+14 — background session observer canonical home extraction.

Pins the AUDIT-N+14 hand-off:

1. ``_run_background_session_observer`` (the real implementation, taking
   ``(exit_code: int, *, timed_out: bool = False)``) is the canonical
   AUDIT-N+14 home in :mod:`thegent.cli.commands.session_impl`.

2. ``impl._run_background_session_observer`` re-exports the
   session_impl implementation so the legacy ``impl.<x>`` import path
   remains valid and the gaps test in
   :mod:`tests.test_unit_cli_impl_gaps` keeps passing.

3. ``observability_impl._run_background_session_observer`` keeps the
   legacy AUDIT-N+9 stub form (``(session_id, **kwargs) -> None``) so
   any legacy caller that goes through the observability side stays
   green. The stub is now annotated as a thin compatibility shim.

4. The real implementation reads ``THGENT_SESSION_META_PATH`` /
   ``THGENT_SESSION_RC_PATH`` from the environment, updates the meta
   file with status/exit_code/timed_out/duration_seconds, and writes
   the rc file. Missing env vars / missing files / OSError on rc write
   are all no-ops.

5. The session_impl docstring carries the AUDIT-N+14 marker.
"""

from __future__ import annotations

import inspect
import json
import os
import time as _time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.cli.commands import impl, observability_impl, session_impl

# ---------------------------------------------------------------------------
# Module paths. Centralized so a future rename only touches one constant.
# ---------------------------------------------------------------------------

SESSION_IMPL = "thegent.cli.commands.session_impl"
IMPL = "thegent.cli.commands.impl"
OBSERVABILITY_IMPL = "thegent.cli.commands.observability_impl"


# ---------------------------------------------------------------------------
# 1. Canonical home: session_impl owns the real implementation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunBackgroundSessionObserverCanonicalHome:
    """AUDIT-N+14: ``_run_background_session_observer`` is defined in
    :mod:`thegent.cli.commands.session_impl` and carries the real
    ``(exit_code, *, timed_out=False)`` signature."""

    # @trace FR-AUDIT-N+14-001
    def test_session_impl_defines_run_background_session_observer(self) -> None:
        assert hasattr(session_impl, "_run_background_session_observer")
        fn = session_impl._run_background_session_observer
        assert callable(fn)
        # The function is *defined* here, not just re-exported:
        assert fn.__module__ == SESSION_IMPL

    # @trace FR-AUDIT-N+14-002
    def test_real_signature_has_exit_code_positional(self) -> None:
        sig = inspect.signature(session_impl._run_background_session_observer)
        params = list(sig.parameters.keys())
        assert params[0] == "exit_code", (
            f"first positional must be 'exit_code', got {params[0]!r}"
        )

    # @trace FR-AUDIT-N+14-003
    def test_real_signature_has_keyword_only_timed_out(self) -> None:
        sig = inspect.signature(session_impl._run_background_session_observer)
        timed_out_param = sig.parameters["timed_out"]
        assert timed_out_param.kind is inspect.Parameter.KEYWORD_ONLY
        assert timed_out_param.default is False

    # @trace FR-AUDIT-N+14-004
    def test_session_impl_docstring_pins_audit_n14_marker(self) -> None:
        text = session_impl.__doc__ or ""
        assert "AUDIT-N+14" in text or "audit-n+14" in text.lower()


# ---------------------------------------------------------------------------
# 2. impl.py re-export preserves identity
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplReExportIdentity:
    """AUDIT-N+14: ``impl._run_background_session_observer`` resolves to
    the canonical session_impl implementation so legacy call-sites
    continue to work."""

    # @trace FR-AUDIT-N+14-005
    def test_impl_run_background_session_observer_is_session_impl(self) -> None:
        assert (
            impl._run_background_session_observer
            is session_impl._run_background_session_observer
        )

    # @trace FR-AUDIT-N+14-006
    def test_impl_run_background_session_observer_signature_is_real_form(self) -> None:
        sig = inspect.signature(impl._run_background_session_observer)
        params = list(sig.parameters.keys())
        assert params[0] == "exit_code"
        assert "timed_out" in sig.parameters

    # @trace FR-AUDIT-N+14-007
    def test_impl_module_does_not_locally_define_run_background_session_observer(
        self,
    ) -> None:
        """impl.py must NOT define ``_run_background_session_observer`` —
        the canonical home is session_impl and impl is a re-export shim."""
        src = inspect.getsource(impl)
        assert "def _run_background_session_observer(" not in src, (
            "impl.py must not define _run_background_session_observer locally"
        )

    # @trace FR-AUDIT-N+14-008
    def test_impl_re_exports_session_impl_includes_observer(self) -> None:
        """The re-export block must include ``_run_background_session_observer``
        so ``from thegent.cli.commands.session_impl import (...)`` binds
        it to ``impl.__dict__``."""
        src = inspect.getsource(impl)
        # Look for the re-export line that lists all session_impl symbols.
        assert "_run_background_session_observer" in src


# ---------------------------------------------------------------------------
# 3. observability_impl keeps the legacy AUDIT-N+9 form via delegation shim
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObservabilityImplLegacyStub:
    """AUDIT-N+14: the observability_impl surface keeps a delegation shim
    that accepts BOTH the legacy AUDIT-N+9 ``(session_id, **kwargs)`` form
    AND the new AUDIT-N+14 ``(exit_code, *, timed_out=False)`` form,
    routing all of them to the canonical session_impl implementation.
    This preserves backward compat for any caller that goes through the
    observability surface."""

    # @trace FR-AUDIT-N+14-009
    def test_observability_impl_run_background_session_observer_is_callable(
        self,
    ) -> None:
        assert callable(observability_impl._run_background_session_observer)

    # @trace FR-AUDIT-N+14-010
    def test_observability_impl_legacy_session_id_form_is_noop(self) -> None:
        """Legacy AUDIT-N+9 stub form: a session_id positional arg with
        any kwargs returns None (because there's no THGENT_SESSION_META_PATH
        set, so the canonical session_impl observer no-ops)."""
        assert (
            observability_impl._run_background_session_observer("sess-legacy") is None
        )
        assert (
            observability_impl._run_background_session_observer(
                "sess-legacy", debug=True
            )
            is None
        )
        assert (
            observability_impl._run_background_session_observer(
                "sess-legacy", whatever=1
            )
            is None
        )

    # @trace FR-AUDIT-N+14-011
    def test_observability_impl_accepts_new_audit_n14_form(self) -> None:
        """The shim also accepts the new AUDIT-N+14 ``(exit_code, *, timed_out)`` form
        and delegates to session_impl. Without env vars set this no-ops too."""
        assert observability_impl._run_background_session_observer(0) is None
        assert (
            observability_impl._run_background_session_observer(137, timed_out=True)
            is None
        )

    # @trace FR-AUDIT-N+14-012
    def test_observability_impl_does_not_share_identity_with_session_impl(self) -> None:
        """The observability surface is a thin delegation shim, NOT the
        canonical implementation. Identity must not be conflated —
        otherwise the AUDIT-N+9 identity contract (impl.X is obs.X)
        would force the canonical home back to observability_impl and
        invalidate the AUDIT-N+14 move."""
        assert (
            observability_impl._run_background_session_observer
            is not session_impl._run_background_session_observer
        )


# ---------------------------------------------------------------------------
# 4. Real implementation behavior: env-driven meta + rc write
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunBackgroundSessionObserverBehavior:
    """AUDIT-N+14: the real implementation reads
    ``THGENT_SESSION_META_PATH`` / ``THGENT_SESSION_RC_PATH`` and
    updates meta + rc accordingly."""

    # @trace FR-AUDIT-N+14-013
    def test_no_meta_path_env_returns_early(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("THGENT_SESSION_META_PATH", None)
            # Should not raise.
            impl._run_background_session_observer(0)

    # @trace FR-AUDIT-N+14-014
    def test_meta_path_not_exists_returns_early(self, tmp_path: Path) -> None:
        meta = tmp_path / "nonexistent.json"
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            impl._run_background_session_observer(0)

    # @trace FR-AUDIT-N+14-015
    def test_updates_meta_and_rc_on_success(self, tmp_path: Path) -> None:
        meta = tmp_path / "sess.json"
        rc = tmp_path / "sess.rc"
        started = datetime.now(UTC).isoformat()
        meta.write_text(json.dumps({"status": "running", "started_at_utc": started}))
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta),
                "THGENT_SESSION_RC_PATH": str(rc),
            },
        ):
            impl._run_background_session_observer(0, timed_out=False)
        updated = json.loads(meta.read_text())
        assert updated["status"] == "exited"
        assert updated["exit_code"] == 0
        assert updated["timed_out"] is False
        assert "duration_seconds" in updated
        assert "finished_at_utc" in updated
        assert rc.read_text().strip() == "0"

    # @trace FR-AUDIT-N+14-016
    def test_timed_out_flag_preserved(self, tmp_path: Path) -> None:
        meta = tmp_path / "sess2.json"
        meta.write_text(json.dumps({"status": "running"}))
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            impl._run_background_session_observer(137, timed_out=True)
        updated = json.loads(meta.read_text())
        assert updated["timed_out"] is True
        assert updated["exit_code"] == 137

    # @trace FR-AUDIT-N+14-017
    def test_rc_write_oserror_ignored(self, tmp_path: Path) -> None:
        meta = tmp_path / "sess3.json"
        meta.write_text(json.dumps({"status": "running"}))
        # rc_path's parent doesn't exist — write_text would raise.
        rc_path = tmp_path / "readonly_dir" / "sess3.rc"
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta),
                "THGENT_SESSION_RC_PATH": str(rc_path),
            },
        ):
            # Should not raise even though rc_path parent does not exist.
            impl._run_background_session_observer(1)

    # @trace FR-AUDIT-N+14-018
    def test_invalid_meta_json_does_not_raise(self, tmp_path: Path) -> None:
        meta = tmp_path / "bad.json"
        meta.write_text("not-valid-json")
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            # Should treat malformed json as empty dict and continue.
            impl._run_background_session_observer(0)
        # The meta file was overwritten with a fresh dict (not the
        # original garbage) so the next read returns valid json.
        updated = json.loads(meta.read_text())
        assert updated["status"] == "exited"
        assert updated["exit_code"] == 0

    # @trace FR-AUDIT-N+14-019
    def test_duration_seconds_added_when_started_at_present(
        self, tmp_path: Path
    ) -> None:
        meta = tmp_path / "sess4.json"
        # Set started_at_utc in the past so duration > 0.
        started = _time.time() - 5
        meta.write_text(json.dumps({"status": "running", "started_at_utc": started}))
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            impl._run_background_session_observer(0)
        updated = json.loads(meta.read_text())
        assert "duration_seconds" in updated
        assert updated["duration_seconds"] >= 5

    # @trace FR-AUDIT-N+14-020
    def test_no_started_at_no_duration_seconds(self, tmp_path: Path) -> None:
        meta = tmp_path / "sess5.json"
        meta.write_text(json.dumps({"status": "running"}))
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            impl._run_background_session_observer(0)
        updated = json.loads(meta.read_text())
        assert "duration_seconds" not in updated


# ---------------------------------------------------------------------------
# 5. Module graph loads clean
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModuleGraphLoadsClean:
    """AUDIT-N+14: every touched module imports without side-effects."""

    # @trace FR-AUDIT-N+14-021
    def test_session_impl_module_loads(self) -> None:
        assert session_impl.__file__ is not None

    # @trace FR-AUDIT-N+14-022
    def test_impl_module_loads(self) -> None:
        assert impl.__file__ is not None

    # @trace FR-AUDIT-N+14-023
    def test_observability_impl_module_loads(self) -> None:
        assert observability_impl.__file__ is not None

    # @trace FR-AUDIT-N+14-024
    def test_session_impl_does_not_circular_import(self) -> None:
        """No circular import: importing impl re-exports session_impl."""
        assert impl._run_background_session_observer.__module__ == SESSION_IMPL
