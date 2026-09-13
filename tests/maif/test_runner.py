"""Unit tests for MAIFRunner.

Tests cover:
- MAIFRunner disabled by default (THGENT_MAIF_ENABLED not set)
- MAIFRunner enabled via env var
- record_run_start returns artifact ID when enabled
- record_run_end records the completion
- Errors don't propagate (non-blocking guarantee)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from thegent.maif.runner import MAIFRunner

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def disabled_runner(monkeypatch: pytest.MonkeyPatch) -> MAIFRunner:
    """MAIFRunner with THGENT_MAIF_ENABLED unset (disabled)."""
    monkeypatch.delenv("THGENT_MAIF_ENABLED", raising=False)
    return MAIFRunner()


@pytest.fixture
def enabled_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> MAIFRunner:
    """MAIFRunner with THGENT_MAIF_ENABLED=1 and a temp DB path."""
    monkeypatch.setenv("THGENT_MAIF_ENABLED", "1")
    monkeypatch.setenv("THGENT_MAIF_DB_PATH", str(tmp_path / "artifacts.db"))
    return MAIFRunner()


# ---------------------------------------------------------------------------
# Disabled-by-default tests
# ---------------------------------------------------------------------------


class TestMAIFRunnerDisabled:
    """MAIFRunner is disabled when THGENT_MAIF_ENABLED is absent or 0."""

    def test_disabled_when_env_unset(self, disabled_runner: MAIFRunner) -> None:
        assert disabled_runner._enabled is False  # noqa: SLF001 -- white-box test of gate flag

    def test_record_run_start_returns_none_when_disabled(
        self, disabled_runner: MAIFRunner
    ) -> None:
        result = disabled_runner.record_run_start(
            run_id="run_test001",
            owner="alice",
            prompt="Do something",
            agent="claude",
        )
        assert result is None

    def test_record_run_end_returns_none_when_disabled(
        self, disabled_runner: MAIFRunner
    ) -> None:
        result = disabled_runner.record_run_end(
            run_id="run_test001",
            status="completed",
            output_summary="Done.",
        )
        assert result is None

    def test_disabled_when_env_is_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_MAIF_ENABLED", "0")
        runner = MAIFRunner()
        assert runner._enabled is False  # noqa: SLF001


# ---------------------------------------------------------------------------
# Enabled tests (mocked store to avoid real SQLite)
# ---------------------------------------------------------------------------


class TestMAIFRunnerEnabled:
    """MAIFRunner records artifacts when THGENT_MAIF_ENABLED=1."""

    def test_enabled_when_env_is_one(self, enabled_runner: MAIFRunner) -> None:
        assert enabled_runner._enabled is True  # noqa: SLF001

    def test_record_run_start_returns_artifact_id(
        self, enabled_runner: MAIFRunner
    ) -> None:
        """record_run_start returns a non-None artifact ID (hex string)."""
        with patch.object(enabled_runner, "_store_artifact"):
            result = enabled_runner.record_run_start(
                run_id="run_abc001",
                owner="bob",
                prompt="Write a poem",
                agent="antigravity",
            )
        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 32  # UUID hex is 32 chars

    def test_record_run_end_returns_artifact_id(
        self, enabled_runner: MAIFRunner
    ) -> None:
        """record_run_end returns a non-None artifact ID (hex string)."""
        with patch.object(enabled_runner, "_store_artifact"):
            result = enabled_runner.record_run_end(
                run_id="run_abc001",
                status="completed",
                output_summary="The poem is done.",
            )
        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 32

    def test_record_run_start_metadata_contains_event(
        self, enabled_runner: MAIFRunner
    ) -> None:
        """The artifact produced by record_run_start has event='run_start' in metadata."""
        captured: list[Any] = []

        def capture(artifact: Any) -> None:
            captured.append(artifact)

        with patch.object(enabled_runner, "_store_artifact", side_effect=capture):
            enabled_runner.record_run_start(
                run_id="run_meta_test",
                owner="carol",
                prompt="Hello world",
                agent="gemini",
            )

        assert len(captured) == 1
        artifact = captured[0]
        assert artifact.metadata.get("event") == "run_start"
        assert artifact.metadata.get("run_id") == "run_meta_test"
        assert artifact.metadata.get("agent") == "gemini"

    def test_record_run_end_metadata_contains_event(
        self, enabled_runner: MAIFRunner
    ) -> None:
        """The artifact produced by record_run_end has event='run_end' in metadata."""
        captured: list[Any] = []

        def capture(artifact: Any) -> None:
            captured.append(artifact)

        with patch.object(enabled_runner, "_store_artifact", side_effect=capture):
            enabled_runner.record_run_end(
                run_id="run_meta_test",
                status="failed",
                output_summary="Something went wrong",
            )

        assert len(captured) == 1
        artifact = captured[0]
        assert artifact.metadata.get("event") == "run_end"
        assert artifact.metadata.get("status") == "failed"

    def test_prompt_truncated_to_200_chars(self, enabled_runner: MAIFRunner) -> None:
        """Long prompts are truncated to 200 chars in the artifact metadata."""
        long_prompt = "x" * 500
        captured: list[Any] = []

        with patch.object(
            enabled_runner, "_store_artifact", side_effect=captured.append
        ):
            enabled_runner.record_run_start(
                run_id="run_trunc",
                owner="dave",
                prompt=long_prompt,
                agent="claude",
            )

        artifact = captured[0]
        assert len(artifact.metadata["prompt_preview"]) <= 200


# ---------------------------------------------------------------------------
# Error non-propagation tests
# ---------------------------------------------------------------------------


class TestMAIFRunnerErrorHandling:
    """Errors inside MAIFRunner must never propagate to the caller."""

    def test_record_run_start_swallows_generator_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the artifact generator raises, record_run_start returns None silently."""
        monkeypatch.setenv("THGENT_MAIF_ENABLED", "1")
        runner = MAIFRunner()

        with patch.object(runner, "_get_generator", side_effect=RuntimeError("boom")):
            result = runner.record_run_start(
                run_id="run_err",
                owner="eve",
                prompt="Crash",
                agent="codex",
            )
        assert result is None

    def test_record_run_end_swallows_store_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the store raises, record_run_end returns None silently."""
        monkeypatch.setenv("THGENT_MAIF_ENABLED", "1")
        runner = MAIFRunner()

        with patch.object(runner, "_store_artifact", side_effect=OSError("disk full")):
            result = runner.record_run_end(
                run_id="run_err2",
                status="completed",
                output_summary="ok",
            )
        # Should return an ID from create_artifact even though store failed, OR None.
        # Either way, no exception should escape.
        assert result is None or isinstance(result, str)

    def test_record_run_start_swallows_import_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If MAIF module imports fail, record_run_start returns None silently."""
        monkeypatch.setenv("THGENT_MAIF_ENABLED", "1")
        runner = MAIFRunner()

        with patch.object(runner, "_get_generator", return_value=None):
            result = runner.record_run_start(
                run_id="run_import_err",
                owner="frank",
                prompt="Test",
                agent="cursor",
            )
        assert result is None
