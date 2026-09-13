"""Unit tests for FallbackStateMachine and OrchestrationState."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest_factories import (
    make_adapter_result,
    make_csm,
    make_fallback_policy,
    make_run_result,
)
from thegent.agents.state_machine import FallbackStateMachine, OrchestrationState
from thegent.contracts.policy import FallbackPolicy
from thegent.contracts.telemetry import ContractTelemetry

if TYPE_CHECKING:
    from pathlib import Path

    from thegent.agents.base import RunResult
    from thegent.contracts.adapters import AdapterResult
    from thegent.contracts.csm import CanonicalStructuredMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _good_csm() -> CanonicalStructuredMessage:
    """CSM that passes semantic validation (COMPLETED + progress=1.0 + summary)."""
    return make_csm(
        status="COMPLETED",
        progress=1.0,
        summary="All done",
    )


def _good_adapter(csm: CanonicalStructuredMessage | None = None) -> AdapterResult:
    """AdapterResult that passes all policy checks."""
    return make_adapter_result(
        csm=csm or _good_csm(),
        confidence=0.95,
        parse_errors=[],
        source_provider="test",
    )


def _make_sync_runner(result: RunResult) -> MagicMock:
    """Create a mock runner whose .run() returns *result*."""
    runner = MagicMock()
    runner.run.return_value = result
    return runner


def _factory_returning(runners: dict[str, MagicMock | None]):
    """Return a runner_factory callable keyed by provider name."""

    def factory(name: str):
        return runners.get(name)

    return factory


# ---------------------------------------------------------------------------
# OrchestrationState
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestOrchestrationState:
    """Tests for OrchestrationState dataclass."""

    def test_default_construction(self) -> None:
        # @trace FR-AGT-011
        state = OrchestrationState(agent="claude", run_id="r1")
        assert state.agent == "claude"
        assert state.run_id == "r1"
        assert state.status == "pending"
        assert state.attempt == 0
        assert state.provider_index == 0
        assert state.providers_tried == []
        assert state.errors == []
        assert state.last_result is None
        assert state.last_normalization is None
        assert state.policy_issues == []
        assert state.semantic_issues == []

    def test_fields_are_mutable(self) -> None:
        # @trace FR-AGT-011
        state = OrchestrationState(agent="a", run_id="r")
        state.status = "running"
        state.attempt = 2
        state.errors.append("boom")
        assert state.status == "running"
        assert state.attempt == 2
        assert state.errors == ["boom"]


# ---------------------------------------------------------------------------
# FallbackStateMachine construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFallbackStateMachineInit:
    def test_default_construction(self) -> None:
        # @trace FR-AGT-011
        fsm = FallbackStateMachine(providers=["claude", "codex"])
        assert fsm.providers == ["claude", "codex"]
        assert fsm.run_id.startswith("run_")
        assert fsm.max_retries == 3
        assert fsm.retry_delay == 2.0
        assert isinstance(fsm.policy, FallbackPolicy)
        assert fsm.telemetry is None
        assert fsm.state.agent == "claude"
        assert fsm.state.status == "pending"

    def test_custom_run_id(self) -> None:
        # @trace FR-AGT-011
        fsm = FallbackStateMachine(providers=["a"], run_id="custom-123")
        assert fsm.run_id == "custom-123"
        assert fsm.state.run_id == "custom-123"

    def test_custom_policy(self) -> None:
        # @trace FR-AGT-011
        policy = make_fallback_policy(min_confidence_threshold=0.9)
        fsm = FallbackStateMachine(providers=["a"], policy=policy)
        assert fsm.policy.min_confidence_threshold == 0.9

    def test_empty_providers_sets_unknown_agent(self) -> None:
        # @trace FR-AGT-011
        fsm = FallbackStateMachine(providers=[])
        assert fsm.state.agent == "unknown"


# ---------------------------------------------------------------------------
# FallbackStateMachine.run -- happy path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFallbackStateMachineRun:
    def test_no_providers_raises(self) -> None:
        # @trace FR-AGT-011
        fsm = FallbackStateMachine(providers=[])
        with pytest.raises(ValueError, match="No providers"):
            fsm.run(runner_factory=lambda n: None, prompt="hi")

    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback", return_value=[])
    @patch("thegent.agents.state_machine.classify_failure")
    def test_success_on_first_attempt(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_normalize,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN
        good_result = make_run_result(exit_code=0, stdout="done")
        adapter_res = _good_adapter()
        adapter_res.csm.source_contract = "xml-tags"
        mock_normalize.return_value = adapter_res

        runner = _make_sync_runner(good_result)
        factory = _factory_returning({"claude": runner})

        fsm = FallbackStateMachine(providers=["claude"])
        result, norm = fsm.run(runner_factory=factory, prompt="do it")

        assert result.exit_code == 0
        assert norm is not None
        assert fsm.state.status == "success"
        assert fsm.state.providers_tried == ["claude"]
        runner.run.assert_called_once()

    def test_runner_factory_returns_none_moves_to_next_provider(self) -> None:
        # @trace FR-AGT-008
        """When runner_factory returns None, state machine skips to next provider."""
        good_result = make_run_result(exit_code=0, stdout="ok")
        runner_b = _make_sync_runner(good_result)

        factory = _factory_returning({"a": None, "b": runner_b})

        with (
            patch("thegent.agents.state_machine.normalize_output") as mock_norm,
            patch("thegent.agents.state_machine.validate_csm", return_value=[]),
            patch("thegent.agents.state_machine.evaluate_fallback", return_value=[]),
            patch("thegent.agents.state_machine.classify_failure") as mock_classify,
        ):
            from thegent.agents.resilience import FailureKind

            mock_classify.return_value = FailureKind.UNKNOWN
            adapter_res = _good_adapter()
            adapter_res.csm.source_contract = "xml-tags"
            mock_norm.return_value = adapter_res

            fsm = FallbackStateMachine(providers=["a", "b"])
            result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert result.exit_code == 0
        assert "a" in fsm.state.providers_tried
        assert "b" in fsm.state.providers_tried
        assert any("No runner for a" in e for e in fsm.state.errors)

    @patch("thegent.agents.state_machine.classify_failure")
    def test_runner_exception_records_error_and_moves_on(self, mock_classify) -> None:
        # @trace FR-AGT-010
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        boom_runner = MagicMock()
        boom_runner.run.side_effect = RuntimeError("kaboom")

        ok_result = make_run_result(exit_code=0, stdout="ok")
        ok_runner = _make_sync_runner(ok_result)

        factory = _factory_returning({"a": boom_runner, "b": ok_runner})

        with (
            patch("thegent.agents.state_machine.normalize_output") as mock_norm,
            patch("thegent.agents.state_machine.validate_csm", return_value=[]),
            patch("thegent.agents.state_machine.evaluate_fallback", return_value=[]),
        ):
            adapter_res = _good_adapter()
            adapter_res.csm.source_contract = "xml-tags"
            mock_norm.return_value = adapter_res

            fsm = FallbackStateMachine(providers=["a", "b"])
            result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert result.exit_code == 0
        assert any("Execution error" in e and "kaboom" in e for e in fsm.state.errors)


# ---------------------------------------------------------------------------
# Provider rotation and retry logic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProviderRotation:
    @patch("thegent.agents.state_machine.classify_failure")
    def test_usage_limit_skips_to_next_provider(self, mock_classify) -> None:
        # @trace FR-AGT-008
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.USAGE_LIMIT
        fail_result = make_run_result(exit_code=1, stderr="quota exceeded")
        ok_result = make_run_result(exit_code=0, stdout="ok")

        runner_a = _make_sync_runner(fail_result)
        runner_b = _make_sync_runner(ok_result)
        factory = _factory_returning({"a": runner_a, "b": runner_b})

        with (
            patch("thegent.agents.state_machine.normalize_output") as mock_norm,
            patch("thegent.agents.state_machine.validate_csm", return_value=[]),
            patch("thegent.agents.state_machine.evaluate_fallback", return_value=[]),
        ):
            adapter_res = _good_adapter()
            adapter_res.csm.source_contract = "xml-tags"
            mock_norm.return_value = adapter_res

            # Reset classify to return UNKNOWN for 2nd provider
            mock_classify.side_effect = [FailureKind.USAGE_LIMIT, FailureKind.UNKNOWN]

            fsm = FallbackStateMachine(providers=["a", "b"])
            result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert result.exit_code == 0
        assert any("Usage limit" in e for e in fsm.state.errors)

    @patch("thegent.agents.state_machine.time.sleep")
    @patch("thegent.agents.state_machine.classify_failure")
    def test_transient_failure_retries_same_provider(self, mock_classify, mock_sleep) -> None:
        # @trace FR-AGT-009
        from thegent.agents.resilience import FailureKind

        fail_result = make_run_result(exit_code=1, stderr="502 bad gateway")
        ok_result = make_run_result(exit_code=0, stdout="ok")

        runner = MagicMock()
        runner.run.side_effect = [fail_result, ok_result]
        factory = _factory_returning({"a": runner})

        mock_classify.side_effect = [FailureKind.TRANSIENT, FailureKind.UNKNOWN]

        with (
            patch("thegent.agents.state_machine.normalize_output") as mock_norm,
            patch("thegent.agents.state_machine.validate_csm", return_value=[]),
            patch("thegent.agents.state_machine.evaluate_fallback", return_value=[]),
        ):
            adapter_res = _good_adapter()
            adapter_res.csm.source_contract = "xml-tags"
            mock_norm.return_value = adapter_res

            fsm = FallbackStateMachine(providers=["a"], max_retries_per_provider=3)
            result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert result.exit_code == 0
        assert runner.run.call_count == 2
        mock_sleep.assert_called_once()

    @patch("thegent.agents.state_machine.time.sleep")
    @patch("thegent.agents.state_machine.classify_failure")
    def test_max_retries_exhausted_moves_to_next_provider(self, mock_classify, mock_sleep) -> None:
        # @trace FR-AGT-009
        from thegent.agents.resilience import FailureKind

        fail_result = make_run_result(exit_code=1, stderr="503")

        runner_a = MagicMock()
        runner_a.run.return_value = fail_result
        ok_result = make_run_result(exit_code=0, stdout="ok")
        runner_b = _make_sync_runner(ok_result)

        factory = _factory_returning({"a": runner_a, "b": runner_b})

        # All attempts on 'a' are transient, then 'b' succeeds
        mock_classify.side_effect = [
            FailureKind.TRANSIENT,
            FailureKind.TRANSIENT,
            FailureKind.TRANSIENT,  # 3 retries on a
            FailureKind.UNKNOWN,  # b succeeds
        ]

        with (
            patch("thegent.agents.state_machine.normalize_output") as mock_norm,
            patch("thegent.agents.state_machine.validate_csm", return_value=[]),
            patch("thegent.agents.state_machine.evaluate_fallback", return_value=[]),
        ):
            adapter_res = _good_adapter()
            adapter_res.csm.source_contract = "xml-tags"
            mock_norm.return_value = adapter_res

            fsm = FallbackStateMachine(
                providers=["a", "b"],
                max_retries_per_provider=3,
            )
            result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        # On the last retry attempt (attempt==max_retries), the transient failure
        # doesn't trigger continue (only if attempt < max_retries), so it breaks.
        # Then provider_index increments and b succeeds.
        assert result.exit_code == 0
        assert fsm.state.status == "success"


# ---------------------------------------------------------------------------
# Max retries enforcement
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMaxRetries:
    def test_max_retries_default_is_three(self) -> None:
        # @trace FR-AGT-009
        fsm = FallbackStateMachine(providers=["a"])
        assert fsm.max_retries == 3

    def test_custom_max_retries(self) -> None:
        # @trace FR-AGT-009
        fsm = FallbackStateMachine(providers=["a"], max_retries_per_provider=5)
        assert fsm.max_retries == 5


# ---------------------------------------------------------------------------
# Policy integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPolicyIntegration:
    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback")
    @patch("thegent.agents.state_machine.classify_failure")
    def test_policy_violation_triggers_fallback_to_next(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        result_a = make_run_result(exit_code=0, stdout="a output")
        result_b = make_run_result(exit_code=0, stdout="b output")
        runner_a = _make_sync_runner(result_a)
        runner_b = _make_sync_runner(result_b)
        factory = _factory_returning({"a": runner_a, "b": runner_b})

        adapter_a = _good_adapter()
        adapter_a.csm.source_contract = "xml-tags"
        adapter_b = _good_adapter()
        adapter_b.csm.source_contract = "xml-tags"
        mock_norm.side_effect = [adapter_a, adapter_b]

        # a has violations, b is clean
        mock_eval.side_effect = [["confidence too low"], []]

        fsm = FallbackStateMachine(providers=["a", "b"])
        result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert result.exit_code == 0
        assert fsm.state.status == "success"
        assert "b" in fsm.state.providers_tried

    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback")
    @patch("thegent.agents.state_machine.classify_failure")
    def test_hard_block_policy_fails_when_last_provider(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        result_a = make_run_result(exit_code=0, stdout="a output")
        runner_a = _make_sync_runner(result_a)
        factory = _factory_returning({"a": runner_a})

        adapter_a = _good_adapter()
        adapter_a.csm.source_contract = "fallback-plain"
        mock_norm.return_value = adapter_a

        # Hard block: contains "disabled"
        mock_eval.return_value = ["Plain text fallback is disabled by policy."]

        fsm = FallbackStateMachine(providers=["a"])
        _result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert fsm.state.status == "failed"
        assert any("Policy blocked" in e for e in fsm.state.errors)

    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback")
    @patch("thegent.agents.state_machine.classify_failure")
    def test_soft_violation_accepted_when_last_provider(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
    ) -> None:
        # @trace FR-AGT-011
        """Non-hard-block violations on the last provider are accepted."""
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        result_a = make_run_result(exit_code=0, stdout="ok")
        runner_a = _make_sync_runner(result_a)
        factory = _factory_returning({"a": runner_a})

        adapter_a = _good_adapter()
        adapter_a.csm.source_contract = "xml-tags"
        mock_norm.return_value = adapter_a

        # Soft violation: no "disabled" or "strict" keyword
        mock_eval.return_value = ["confidence too low"]

        fsm = FallbackStateMachine(providers=["a"])
        _result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert fsm.state.status == "success"


# ---------------------------------------------------------------------------
# Telemetry recording
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTelemetryRecording:
    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback", return_value=[])
    @patch("thegent.agents.state_machine.classify_failure")
    def test_telemetry_record_normalization_called_on_success(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        good_result = make_run_result(exit_code=0, stdout="done")
        adapter_res = _good_adapter()
        adapter_res.csm.source_contract = "xml-tags"
        mock_norm.return_value = adapter_res

        runner = _make_sync_runner(good_result)
        factory = _factory_returning({"claude": runner})

        telemetry = MagicMock(spec=ContractTelemetry)
        telemetry.get_stats.return_value = None

        fsm = FallbackStateMachine(
            providers=["claude"],
            telemetry=telemetry,
        )
        fsm.run(runner_factory=factory, prompt="hi")

        telemetry.record_normalization.assert_called_once()
        call_kwargs = telemetry.record_normalization.call_args
        assert call_kwargs.kwargs["success"] is True
        assert call_kwargs.kwargs["event_type"] == "normalization"

    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm")
    @patch("thegent.agents.state_machine.evaluate_fallback", return_value=[])
    @patch("thegent.agents.state_machine.classify_failure")
    def test_telemetry_emits_semantic_drift_event(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        good_result = make_run_result(exit_code=0, stdout="done")
        adapter_res = _good_adapter()
        adapter_res.csm.source_contract = "xml-tags"
        adapter_res.parse_errors = []
        mock_norm.return_value = adapter_res

        # Semantic issues present
        mock_validate.return_value = ["Status is COMPLETED but summary is empty"]

        runner = _make_sync_runner(good_result)
        factory = _factory_returning({"claude": runner})

        telemetry = MagicMock(spec=ContractTelemetry)
        telemetry.get_stats.return_value = None

        fsm = FallbackStateMachine(providers=["claude"], telemetry=telemetry)
        fsm.run(runner_factory=factory, prompt="hi")

        telemetry.emit_drift_event.assert_called_once()
        drift_call = telemetry.emit_drift_event.call_args
        assert drift_call.args[3] == "semantic"

    @patch("thegent.agents.state_machine.normalize_output")
    @patch("thegent.agents.state_machine.validate_csm", return_value=[])
    @patch("thegent.agents.state_machine.evaluate_fallback", return_value=[])
    @patch("thegent.agents.state_machine.classify_failure")
    def test_telemetry_emits_structural_drift_on_parse_errors(
        self,
        mock_classify,
        mock_eval,
        mock_validate,
        mock_norm,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-011
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        good_result = make_run_result(exit_code=0, stdout="done")
        adapter_res = _good_adapter()
        adapter_res.csm.source_contract = "xml-tags"
        adapter_res.parse_errors = ["no_xml_tags_detected"]
        mock_norm.return_value = adapter_res

        runner = _make_sync_runner(good_result)
        factory = _factory_returning({"claude": runner})

        telemetry = MagicMock(spec=ContractTelemetry)
        telemetry.get_stats.return_value = None

        fsm = FallbackStateMachine(providers=["claude"], telemetry=telemetry)
        fsm.run(runner_factory=factory, prompt="hi")

        telemetry.emit_drift_event.assert_called_once()
        drift_call = telemetry.emit_drift_event.call_args
        assert drift_call.args[3] == "structural"
        call_kwargs = telemetry.record_normalization.call_args
        assert call_kwargs.kwargs["event_type"] == "schema.drift.structural"


# ---------------------------------------------------------------------------
# All providers exhausted
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAllProvidersExhausted:
    @patch("thegent.agents.state_machine.classify_failure")
    def test_all_providers_fail_returns_last_result(self, mock_classify) -> None:
        # @trace FR-AGT-008
        from thegent.agents.resilience import FailureKind

        mock_classify.return_value = FailureKind.UNKNOWN

        fail_result = make_run_result(exit_code=1, stderr="bad")
        runner_a = _make_sync_runner(fail_result)
        runner_b = _make_sync_runner(fail_result)
        factory = _factory_returning({"a": runner_a, "b": runner_b})

        fsm = FallbackStateMachine(providers=["a", "b"])
        result, _norm = fsm.run(runner_factory=factory, prompt="hi")

        assert fsm.state.status == "failed"
        assert result is not None
        assert result.exit_code == 1
