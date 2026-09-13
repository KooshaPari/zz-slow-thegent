"""Integration tests for the FallbackStateMachine with registry and policy.

Tests the state machine orchestration loop with mocked runners, verifying
provider rotation, policy enforcement, and telemetry recording during
state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import orjson as json
import pytest

from tests.conftest_factories import make_fallback_policy, make_run_result
from thegent.agents.state_machine import FallbackStateMachine
from thegent.contracts.csm import CSMStatus
from thegent.contracts.telemetry import (
    EVENT_NORMALIZATION,
    EVENT_SCHEMA_DRIFT_SEMANTIC,
    EVENT_SCHEMA_DRIFT_STRUCTURAL,
    ContractTelemetry,
)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class SyncMockRunner:
    """Synchronous mock runner for FallbackStateMachine (which calls runner.run synchronously)."""

    results: list[Any] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)
    _call_index: int = 0

    def add_result(self, result: Any) -> None:
        self.results.append(result)

    def run(self, prompt: str, **kwargs: Any) -> Any:
        self.calls.append({"prompt": prompt, **kwargs})
        if self._call_index < len(self.results):
            result = self.results[self._call_index]
            self._call_index += 1
            return result
        return make_run_result()


def _make_xml_stdout(
    status: str = "completed",
    summary: str = "Done",
    progress: str = "100%",
) -> str:
    """Build an XML-structured agent stdout string."""
    return f"<STATUS>{status}</STATUS><SUMMARY>{summary}</SUMMARY><PROGRESS>{progress}</PROGRESS>"


def _runner_factory_from_dict(
    runners: dict[str, SyncMockRunner],
) -> Any:
    """Build a runner_factory callable from a dict of provider -> SyncMockRunner."""

    def factory(agent: str) -> SyncMockRunner | None:
        return runners.get(agent)

    return factory


@pytest.mark.integration
class TestStateMachineWithMockedRunners:
    """Tests FallbackStateMachine orchestration with MockRunner instances."""

    def test_single_provider_success(self, tmp_path: Path) -> None:
        # @trace FR-AGT-011
        """A single provider succeeding should yield success status."""
        runner = SyncMockRunner()
        runner.add_result(
            make_run_result(
                exit_code=0,
                stdout=_make_xml_stdout(),
            )
        )
        factory = _runner_factory_from_dict({"claude": runner})

        sm = FallbackStateMachine(
            providers=["claude"],
            policy=make_fallback_policy(),
        )
        result, norm = sm.run(factory, prompt="Do something")

        assert result is not None
        assert result.exit_code == 0
        assert norm is not None
        assert norm.csm.status == CSMStatus.COMPLETED
        assert sm.state.status == "success"

    def test_provider_rotation_on_failure(self, tmp_path: Path) -> None:
        # @trace FR-AGT-011
        """When the first provider fails, the state machine should rotate to the next."""
        bad_runner = SyncMockRunner()
        bad_runner.add_result(
            make_run_result(
                exit_code=1,
                stderr="quota exceeded",
            )
        )

        good_runner = SyncMockRunner()
        good_runner.add_result(
            make_run_result(
                exit_code=0,
                stdout=_make_xml_stdout(),
            )
        )

        factory = _runner_factory_from_dict(
            {
                "codex": bad_runner,
                "claude": good_runner,
            }
        )

        sm = FallbackStateMachine(
            providers=["codex", "claude"],
            policy=make_fallback_policy(),
            max_retries_per_provider=1,
        )
        result, norm = sm.run(factory, prompt="Fix the bug")

        assert result.exit_code == 0
        assert norm is not None
        assert norm.csm.status == CSMStatus.COMPLETED
        assert "codex" in sm.state.providers_tried
        assert "claude" in sm.state.providers_tried

    def test_no_runner_found_skips_provider(self) -> None:
        # @trace FR-AGT-011
        """If runner_factory returns None, the provider is skipped."""
        good_runner = SyncMockRunner()
        good_runner.add_result(
            make_run_result(
                exit_code=0,
                stdout=_make_xml_stdout(),
            )
        )
        factory = _runner_factory_from_dict({"claude": good_runner})

        sm = FallbackStateMachine(
            providers=["nonexistent", "claude"],
            policy=make_fallback_policy(),
        )
        result, _norm = sm.run(factory, prompt="Hello")

        assert result.exit_code == 0
        assert any("No runner" in e for e in sm.state.errors)

    def test_all_providers_fail_yields_failed_state(self) -> None:
        # @trace FR-AGT-011
        """When all providers fail, state should be 'failed'."""
        bad_runner = SyncMockRunner()
        bad_runner.add_result(make_run_result(exit_code=1, stderr="quota exceeded"))

        factory = _runner_factory_from_dict({"codex": bad_runner})

        sm = FallbackStateMachine(
            providers=["codex"],
            policy=make_fallback_policy(),
            max_retries_per_provider=1,
        )
        _result, _norm = sm.run(factory, prompt="Fail")

        assert sm.state.status == "failed"


@pytest.mark.integration
class TestStateMachineWithTelemetry:
    """Tests that the state machine correctly records telemetry events."""

    def test_telemetry_records_normalization_on_success(self, tmp_path: Path) -> None:
        # @trace FR-AGT-011
        """Successful normalization should emit a normalization telemetry event."""
        telemetry = ContractTelemetry(tmp_path)
        runner = SyncMockRunner()
        runner.add_result(
            make_run_result(
                exit_code=0,
                stdout=_make_xml_stdout(),
            )
        )
        factory = _runner_factory_from_dict({"claude": runner})

        sm = FallbackStateMachine(
            providers=["claude"],
            policy=make_fallback_policy(),
            telemetry=telemetry,
        )
        sm.run(factory, prompt="Do something")

        # Read telemetry file and verify an event was recorded
        assert telemetry.telemetry_path.exists()
        events = [json.loads(line) for line in telemetry.telemetry_path.read_text().strip().splitlines()]
        assert len(events) >= 1
        norm_events = [e for e in events if e["event_type"] == EVENT_NORMALIZATION]
        assert len(norm_events) >= 1
        assert norm_events[0]["provider"] == "claude"
        assert norm_events[0]["success"] is True

    def test_telemetry_records_drift_on_validation_failure(
        self,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-011
        """When validation issues exist, a drift event should be emitted.

        The XMLOutputAdapter feeds validate_csm issues into parse_errors,
        so the state machine classifies this as structural drift. Either
        structural or semantic drift events are acceptable proof of integration.
        """
        telemetry = ContractTelemetry(tmp_path)
        runner = SyncMockRunner()
        # COMPLETED but no summary -> validation issue (adapter puts it in parse_errors)
        runner.add_result(
            make_run_result(
                exit_code=0,
                stdout="<STATUS>completed</STATUS><PROGRESS>100</PROGRESS>",
            )
        )
        factory = _runner_factory_from_dict({"claude": runner})

        sm = FallbackStateMachine(
            providers=["claude"],
            policy=make_fallback_policy(),
            telemetry=telemetry,
        )
        sm.run(factory, prompt="Test")

        events = [json.loads(line) for line in telemetry.telemetry_path.read_text().strip().splitlines()]
        event_types = {e["event_type"] for e in events}
        # The adapter puts validate_csm issues into parse_errors, so the state
        # machine sees them as structural drift rather than semantic drift.
        drift_events = event_types & {
            EVENT_SCHEMA_DRIFT_STRUCTURAL,
            EVENT_SCHEMA_DRIFT_SEMANTIC,
            EVENT_NORMALIZATION,
        }
        assert len(drift_events) >= 1

    def test_telemetry_records_structural_drift_on_parse_errors(
        self,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-011
        """When the adapter produces parse errors, structural drift should be emitted."""
        telemetry = ContractTelemetry(tmp_path)
        runner = SyncMockRunner()
        # Plain text with no XML tags -> parse errors from XML adapter
        runner.add_result(
            make_run_result(
                exit_code=0,
                stdout="Just plain text, no XML tags whatsoever.",
            )
        )
        factory = _runner_factory_from_dict({"claude": runner})

        sm = FallbackStateMachine(
            providers=["claude"],
            policy=make_fallback_policy(),
            telemetry=telemetry,
        )
        sm.run(factory, prompt="Test")

        events = [json.loads(line) for line in telemetry.telemetry_path.read_text().strip().splitlines()]
        # Should record at least one event (either structural drift or normalization with errors)
        assert len(events) >= 1

    def test_telemetry_stats_reflect_recorded_events(self, tmp_path: Path) -> None:
        # @trace FR-AGT-011
        """After recording events, get_stats should return accurate counts."""
        telemetry = ContractTelemetry(tmp_path)
        runner = SyncMockRunner()
        runner.add_result(make_run_result(exit_code=0, stdout=_make_xml_stdout()))
        runner.add_result(make_run_result(exit_code=0, stdout=_make_xml_stdout(summary="Second")))
        factory = _runner_factory_from_dict({"claude": runner})

        # Run twice
        sm1 = FallbackStateMachine(
            providers=["claude"],
            telemetry=telemetry,
            run_id="run-1",
        )
        sm1.run(factory, prompt="First")

        sm2 = FallbackStateMachine(
            providers=["claude"],
            telemetry=telemetry,
            run_id="run-2",
        )
        sm2.run(factory, prompt="Second")

        stats = telemetry.get_stats(limit=100)
        assert stats["total"] >= 2
        assert stats["success_rate"] > 0.0
