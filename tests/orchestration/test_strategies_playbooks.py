"""Tests for recovery playbook automation (WP-2004, FR-008).

Tests cover get_playbook_for_failure and execute_playbook_step functions.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.strategies.playbooks import (
    execute_playbook_step,
    get_playbook_for_failure,
)


class TestGetPlaybookForFailure:
    """Tests for get_playbook_for_failure function."""

    def test_timeout_playbook(self) -> None:
        """Verify correct playbook for TIMEOUT."""
        result = get_playbook_for_failure("Operation timed out after 30s")

        assert result == ["retry_with_backoff", "increase_timeout", "escalate"]

    def test_rate_limit_playbook(self) -> None:
        """Verify correct playbook for RATE_LIMIT."""
        result = get_playbook_for_failure("Rate limit exceeded: 429 Too Many Requests")

        assert result == ["wait_and_retry", "reduce_concurrency", "escalate"]

    def test_auth_failure_playbook(self) -> None:
        """Verify correct playbook for AUTH_FAILURE."""
        result = get_playbook_for_failure("Authentication failed: invalid token")

        assert result == ["refresh_credentials", "escalate"]

    def test_network_partition_playbook(self) -> None:
        """Verify correct playbook for NETWORK_PARTITION."""
        result = get_playbook_for_failure("Network unreachable: connection refused")

        assert result == ["retry", "failover_provider", "escalate"]

    def test_malformed_response_playbook(self) -> None:
        """Verify correct playbook for MALFORMED_RESPONSE."""
        result = get_playbook_for_failure("Invalid JSON: malformed response")

        assert result == ["log_drift", "fallback_parser", "escalate"]

    def test_state_corruption_playbook(self) -> None:
        """Verify correct playbook for STATE_CORRUPTION."""
        result = get_playbook_for_failure("State corruption detected: checksum mismatch")

        assert result == ["rollback_checkpoint", "escalate"]

    def test_budget_exceeded_playbook(self) -> None:
        """Verify correct playbook for BUDGET_EXCEEDED."""
        result = get_playbook_for_failure("Budget exceeded: daily limit reached")

        assert result == ["pause_non_critical", "escalate"]

    def test_circuit_open_playbook(self) -> None:
        """Verify correct playbook for CIRCUIT_OPEN."""
        result = get_playbook_for_failure("Circuit breaker open: too many failures")

        assert result == ["wait_recovery_window", "half_open_trial", "escalate"]

    def test_policy_deny_playbook(self) -> None:
        """Verify correct playbook for POLICY_DENY."""
        result = get_playbook_for_failure("Policy denied: operation not allowed")

        assert result == ["request_override", "escalate"]

    def test_contract_drift_playbook(self) -> None:
        """Verify correct playbook for CONTRACT_DRIFT."""
        result = get_playbook_for_failure("Contract drift: schema mismatch")

        assert result == ["emit_drift_event", "fallback_contract", "escalate"]

    def test_retry_exhausted_playbook(self) -> None:
        """Verify correct playbook for RETRY_EXHAUSTED."""
        result = get_playbook_for_failure("Retry exhausted: max attempts reached")

        assert result == ["dlq_enqueue", "escalate"]

    def test_checkpoint_failed_playbook(self) -> None:
        """Verify correct playbook for CHECKPOINT_FAILED."""
        result = get_playbook_for_failure("Checkpoint failed: write error")

        assert result == ["retry_checkpoint", "rollback", "escalate"]

    def test_rollback_triggered_playbook(self) -> None:
        """Verify correct playbook for ROLLBACK_TRIGGERED."""
        result = get_playbook_for_failure("Rollback triggered: safety limit exceeded")

        assert result == ["verify_rollback", "resume_or_escalate"]

    def test_unknown_playbook(self) -> None:
        """Verify correct playbook for UNKNOWN."""
        result = get_playbook_for_failure("Some unknown error occurred")

        assert result == ["log", "escalate"]

    def test_empty_error_message(self) -> None:
        """Verify playbook for empty error message."""
        result = get_playbook_for_failure("")

        # Empty should classify as UNKNOWN
        assert result == ["log", "escalate"]


class TestExecutePlaybookStep:
    """Tests for execute_playbook_step function."""

    @pytest.fixture
    def session_dir(self, tmp_path: Path) -> Path:
        """Create a temporary session directory."""
        return tmp_path / "session"

    def test_escalate_step(self, session_dir: Path) -> None:
        """Verify escalate step adds to escalation queue."""
        with patch("thegent.execution.EscalationQueue") as mock_eq:
            mock_instance = MagicMock()
            mock_eq.return_value = mock_instance

            result = execute_playbook_step(
                session_dir=session_dir,
                step="escalate",
                run_id="run-001",
                context={"agent": "test-agent", "reason": "test failure"},
            )

            mock_eq.assert_called_once_with(session_dir)
            mock_instance.add.assert_called_once_with(
                run_id="run-001",
                agent="test-agent",
                reason="test failure",
            )
            assert result == {"step": "escalate", "status": "escalated"}

    def test_escalate_with_empty_context(self, session_dir: Path) -> None:
        """Verify escalate step handles empty context."""
        with patch("thegent.execution.EscalationQueue") as mock_eq:
            mock_instance = MagicMock()
            mock_eq.return_value = mock_instance

            result = execute_playbook_step(
                session_dir=session_dir,
                step="escalate",
                run_id="run-002",
                context=None,
            )

            mock_instance.add.assert_called_once_with(
                run_id="run-002",
                agent="",
                reason="playbook_escalation",
            )
            assert result == {"step": "escalate", "status": "escalated"}

    def test_dlq_enqueue_step(self, session_dir: Path) -> None:
        """Verify dlq_enqueue step adds to dead letter queue."""
        with patch("thegent.execution.DLQManager") as mock_dlq:
            with patch("thegent.execution.RunMeta") as mock_meta:
                mock_instance = MagicMock()
                mock_dlq.return_value = mock_instance

                result = execute_playbook_step(
                    session_dir=session_dir,
                    step="dlq_enqueue",
                    run_id="run-003",
                    context={
                        "agent": "worker-1",
                        "prompt": "test prompt",
                        "cwd": "/workspace",
                        "owner": "user-1",
                        "error": "timeout error",
                    },
                )

                mock_dlq.assert_called_once_with(session_dir)
                mock_meta.assert_called_once_with(
                    run_id="run-003",
                    agent="worker-1",
                    prompt="test prompt",
                    cwd="/workspace",
                    owner="user-1",
                )
                mock_instance.enqueue.assert_called_once()
                assert result == {"step": "dlq_enqueue", "status": "enqueued"}

    def test_dlq_enqueue_with_defaults(self, session_dir: Path) -> None:
        """Verify dlq_enqueue step handles missing context values."""
        with patch("thegent.execution.DLQManager") as mock_dlq:
            with patch("thegent.execution.RunMeta") as mock_meta:
                mock_instance = MagicMock()
                mock_dlq.return_value = mock_instance

                result = execute_playbook_step(
                    session_dir=session_dir,
                    step="dlq_enqueue",
                    run_id="run-004",
                    context={"error": "failed"},  # Minimal context
                )

                mock_meta.assert_called_once_with(
                    run_id="run-004",
                    agent="",
                    prompt="",
                    cwd=".",
                    owner="system",
                )
                assert result == {"step": "dlq_enqueue", "status": "enqueued"}

    def test_unknown_step_returns_pending(self, session_dir: Path) -> None:
        """Verify unknown step returns pending status."""
        result = execute_playbook_step(
            session_dir=session_dir,
            step="unknown_step",
            run_id="run-005",
            context=None,
        )

        assert result["step"] == "unknown_step"
        assert result["status"] == "pending"
        assert "requires manual execution" in result["message"]

    def test_retry_step_pending(self, session_dir: Path) -> None:
        """Verify retry step returns pending."""
        result = execute_playbook_step(
            session_dir=session_dir,
            step="retry",
            run_id="run-006",
        )

        assert result["status"] == "pending"

    def test_wait_and_retry_step_pending(self, session_dir: Path) -> None:
        """Verify wait_and_retry step returns pending."""
        result = execute_playbook_step(
            session_dir=session_dir,
            step="wait_and_retry",
            run_id="run-007",
        )

        assert result["status"] == "pending"

    def test_no_context_parameter(self, session_dir: Path) -> None:
        """Verify step works without context parameter."""
        result = execute_playbook_step(
            session_dir=session_dir,
            step="log",
            run_id="run-008",
        )

        assert result["status"] == "pending"
