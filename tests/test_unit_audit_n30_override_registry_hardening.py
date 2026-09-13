"""AUDIT-N+30 — dormant-core OverrideRegistry hardening parity.

SOTA Pass-14 audit over the ``OverrideRegistry`` surface surfaced in
the same module as AUDIT-N+29 hardened ``RunRegistry`` identified 6
hardening items:

* NEW-1 — per-instance ``RLock`` so concurrent ``record`` callers
  cannot corrupt the JSONL stream.
* NEW-2 — ``try/except OSError`` around ``_save`` so a partial-write
  IO failure surfaces cleanly without desyncing the in-memory list.
* NEW-3 — defensive input validation: ``owner`` must be a non-empty
  string, ``reason`` must be a string, ``ttl_seconds`` must be a
  non-negative ``int`` (no ``bool``, no ``float``).
* NEW-4 — ``has_unexpired`` no longer trails into dead unreachable
  code (the pre-hardening surface had an orphan docstring +
  ``cls._overrides.clear()`` + ``return None`` block after the
  ``return False``).
* NEW-5 — explicit ``clear()`` method that resets the in-memory list
  AND truncates the on-disk JSONL.
* NEW-6 — malformed ``expires_at_utc`` strings surface a structured
  ``logger.warning`` instead of being silently skipped, so a buggy
  upstream writer is observable in operational logs.

This suite pins all six items.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

import pytest

from thegent.execution import OverrideRegistry

# ---------------------------------------------------------------------------
# Lane 1 — NEW-1: per-instance RLock + concurrency safety
# ---------------------------------------------------------------------------


class TestOverrideRegistryConcurrency:
    """Pin the AUDIT-N+30 NEW-1 per-instance ``_append_lock``."""

    def test_append_lock_is_reentrant(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        assert hasattr(oreg, "_append_lock"), (
            "OverrideRegistry must carry _append_lock (NEW-1)"
        )
        # Verify the re-entrant flavour: a thread that holds the lock
        # can re-acquire it without deadlocking. ``threading.RLock`` is
        # a factory in modern Python, so we exercise the behaviour
        # rather than relying on ``isinstance``.
        lock = oreg._append_lock
        assert lock.acquire(blocking=False) is True
        try:
            # Re-entrant acquire: a plain ``Lock`` would return False
            # here, an ``RLock`` returns True.
            assert lock.acquire(blocking=False) is True, (
                "_append_lock must be re-entrant (RLock)"
            )
        finally:
            lock.release()
            lock.release()

    def test_concurrent_record_threads_safe(self, tmp_path: Path) -> None:
        """50 threads each calling ``record`` produce 50 on-disk entries."""
        oreg = OverrideRegistry(tmp_path)

        def writer(i: int) -> None:
            oreg.record(f"owner-{i}", f"reason-{i}", ttl_seconds=3600)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(oreg._records) == 50

        # Every entry must be on disk exactly once.
        on_disk = oreg.registry_path.read_text(encoding="utf-8").splitlines()
        assert len(on_disk) == 50
        # No torn writes: each line must be valid JSON.
        for line in on_disk:
            payload = json.loads(line)
            assert payload["owner"].startswith("owner-")


# ---------------------------------------------------------------------------
# Lane 2 — NEW-2: IO error resilience
# ---------------------------------------------------------------------------


class TestOverrideRegistryIOResilience:
    """Pin the AUDIT-N+30 NEW-2 ``_save`` try/except contract."""

    def test_save_raises_on_open_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ``PermissionError`` on ``open`` propagates and the in-memory
        list remains the canonical truth (no torn on-disk state, no
        rollback mutation)."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("seed", "seed-reason", ttl_seconds=3600)
        baseline_count = len(oreg._records)

        def _raise_oserror(*_args: object, **_kwargs: object) -> None:
            raise PermissionError(13, "Permission denied", str(oreg.registry_path))

        monkeypatch.setattr("builtins.open", _raise_oserror)
        with pytest.raises(PermissionError):
            oreg.record("post-failure", "should-not-be-persisted", ttl_seconds=3600)

        # The failed record must NOT have been appended to the
        # canonical in-memory list (the rollback semantics).
        assert len(oreg._records) == baseline_count
        assert all(r.get("owner") != "post-failure" for r in oreg._records)

    def test_save_partial_write_recovers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A first save that fails does not prevent subsequent successful saves."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("first", "first-reason", ttl_seconds=3600)
        assert oreg.has_unexpired("first") is True

        original_open = open

        def _flaky_open(file, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            mode = args[0] if args else kwargs.get("mode", "")
            if str(file) == str(oreg.registry_path) and "w" in str(mode):
                raise PermissionError(13, "Permission denied", str(oreg.registry_path))
            return original_open(file, *args, **kwargs)  # type: ignore[call-arg]

        monkeypatch.setattr("builtins.open", _flaky_open)

        # The first record inside the patched window fails.
        with pytest.raises(PermissionError):
            oreg.record("blocked", "blocked-reason", ttl_seconds=3600)
        assert len(oreg._records) == 1  # baseline preserved
        assert all(r.get("owner") != "blocked" for r in oreg._records)

        monkeypatch.undo()

        # After restoring the original open, subsequent writes succeed.
        oreg.record("after-recovery", "after-recovery-reason", ttl_seconds=3600)
        assert oreg.has_unexpired("after-recovery") is True
        on_disk = oreg.registry_path.read_text(encoding="utf-8").splitlines()
        assert len(on_disk) == 2


# ---------------------------------------------------------------------------
# Lane 3 — NEW-3: defensive input validation
# ---------------------------------------------------------------------------


class TestOverrideRegistryValidation:
    """Pin the AUDIT-N+30 NEW-3 input-validation contract."""

    def test_empty_owner_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="owner must be a non-empty string"):
            oreg.record("", "reason", ttl_seconds=3600)

    def test_non_string_owner_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="owner must be a string"):
            oreg.record(123, "reason", ttl_seconds=3600)  # type: ignore[arg-type]

    def test_none_owner_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="owner must be a string"):
            oreg.record(None, "reason", ttl_seconds=3600)  # type: ignore[arg-type]

    def test_non_string_reason_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="reason must be a string"):
            oreg.record("owner", 456, ttl_seconds=3600)  # type: ignore[arg-type]

    def test_negative_ttl_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="ttl_seconds must be non-negative"):
            oreg.record("owner", "reason", ttl_seconds=-1)

    def test_float_ttl_raises_value_error(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="ttl_seconds must be int"):
            oreg.record("owner", "reason", ttl_seconds=1.5)  # type: ignore[arg-type]

    def test_bool_ttl_raises_value_error(self, tmp_path: Path) -> None:
        """``bool`` is an ``int`` subclass in Python but never a meaningful TTL."""
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError, match="ttl_seconds must be int"):
            oreg.record("owner", "reason", ttl_seconds=True)  # type: ignore[arg-type]

    def test_validation_runs_before_state_mutation(self, tmp_path: Path) -> None:
        """A failing validation must NOT leave a half-written record."""
        oreg = OverrideRegistry(tmp_path)
        with pytest.raises(ValueError):
            oreg.record("", "reason", ttl_seconds=3600)
        # No on-disk entry should exist after the rejected call.
        assert not oreg.registry_path.exists()
        assert oreg._records == []

    def test_valid_record_returns_record_dict(self, tmp_path: Path) -> None:
        """A successful ``record`` returns the persisted record dict."""
        oreg = OverrideRegistry(tmp_path)
        result = oreg.record("owner", "reason", ttl_seconds=3600)
        assert result["owner"] == "owner"
        assert result["reason"] == "reason"
        assert result["status"] == "active"
        assert "timestamp" in result
        assert "expires_at_utc" in result


# ---------------------------------------------------------------------------
# Lane 4 — NEW-4: has_unexpired no longer has dead unreachable code
# ---------------------------------------------------------------------------


class TestOverrideRegistryHasUnexpiredClean:
    """Pin the AUDIT-N+30 NEW-4 contract: ``has_unexpired`` returns cleanly."""

    def test_has_unexpired_returns_bool(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        result = oreg.has_unexpired("nobody")
        assert isinstance(result, bool)
        assert result is False

    def test_has_unexpired_true_after_record(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("owner", "reason", ttl_seconds=3600)
        assert oreg.has_unexpired("owner") is True

    def test_has_unexpired_false_for_different_owner(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("owner", "reason", ttl_seconds=3600)
        assert oreg.has_unexpired("other-owner") is False


# ---------------------------------------------------------------------------
# Lane 5 — NEW-5: clear() method
# ---------------------------------------------------------------------------


class TestOverrideRegistryClear:
    """Pin the AUDIT-N+30 NEW-5 ``clear()`` method."""

    def test_clear_returns_count(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("a", "r", ttl_seconds=3600)
        oreg.record("b", "r", ttl_seconds=3600)
        cleared = oreg.clear()
        assert cleared == 2

    def test_clear_empties_in_memory_list(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("a", "r", ttl_seconds=3600)
        oreg.clear()
        assert oreg._records == []
        assert oreg.has_unexpired("a") is False

    def test_clear_truncates_on_disk_jsonl(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("a", "r", ttl_seconds=3600)
        oreg.record("b", "r", ttl_seconds=3600)
        assert oreg.registry_path.exists()
        oreg.clear()
        # The file may be empty (size 0) or absent; either way no
        # record entries must remain.
        if oreg.registry_path.exists():
            on_disk = oreg.registry_path.read_text(encoding="utf-8").strip()
            assert on_disk == ""

    def test_clear_on_empty_registry_returns_zero(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        assert oreg.clear() == 0

    def test_clear_method_exists(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        assert hasattr(oreg, "clear"), "OverrideRegistry must expose clear() (NEW-5)"
        assert callable(oreg.clear)


# ---------------------------------------------------------------------------
# Lane 6 — NEW-6: malformed-timestamp observability
# ---------------------------------------------------------------------------


class TestOverrideRegistryMalformedTimestamps:
    """Pin the AUDIT-N+30 NEW-6 ``logger.warning`` contract."""

    def test_malformed_expires_at_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        oreg = OverrideRegistry(tmp_path)
        # Manually craft a record with a malformed timestamp.
        oreg._records.append({"owner": "broken-owner", "expires_at_utc": "not-a-date"})
        with caplog.at_level(logging.WARNING, logger="thegent.execution"):
            result = oreg.has_unexpired("broken-owner")
        assert result is False
        # At least one warning must have been emitted.
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("malformed expires_at_utc" in r.getMessage() for r in warnings)

    def test_valid_timestamp_does_not_log_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("ok-owner", "ok-reason", ttl_seconds=3600)
        with caplog.at_level(logging.WARNING, logger="thegent.execution"):
            result = oreg.has_unexpired("ok-owner")
        assert result is True
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert all("malformed expires_at_utc" not in r.getMessage() for r in warnings)


# ---------------------------------------------------------------------------
# Lane 7 — Cross-cutting: load → save round-trip preserves records
# ---------------------------------------------------------------------------


class TestOverrideRegistryRoundTrip:
    """Sanity check that hardening did not break the load/save round-trip."""

    def test_record_survives_reload(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("persist-owner", "persist-reason", ttl_seconds=3600)
        # Construct a fresh registry pointed at the same dir.
        oreg2 = OverrideRegistry(tmp_path)
        assert len(oreg2._records) == 1
        assert oreg2._records[0]["owner"] == "persist-owner"
        assert oreg2.has_unexpired("persist-owner") is True

    def test_clear_survives_reload(self, tmp_path: Path) -> None:
        oreg = OverrideRegistry(tmp_path)
        oreg.record("a", "r", ttl_seconds=3600)
        oreg.clear()
        oreg2 = OverrideRegistry(tmp_path)
        assert oreg2._records == []
        assert oreg2.has_unexpired("a") is False

    def test_malformed_jsonl_line_does_not_break_load(self, tmp_path: Path) -> None:
        """Pre-existing contracts: corrupt lines are skipped on load."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("good", "good-reason", ttl_seconds=3600)
        # Append a corrupt line directly to the JSONL file.
        with open(oreg.registry_path, "a", encoding="utf-8") as fh:
            fh.write("{this is not valid json\n")
        # Reload should not raise.
        oreg2 = OverrideRegistry(tmp_path)
        # The valid record should still be present; the corrupt line is skipped.
        assert any(r.get("owner") == "good" for r in oreg2._records)
