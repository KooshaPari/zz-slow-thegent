"""Spec-only hardening tests for the dormant Orchestration Playbooks cluster (SOTA pass-24).

Covers a single dormant orchestration/strategies module that has never
been audited in the dormant-core chain:

  * ``thegent.orchestration.strategies.playbooks``
    — ``get_playbook_for_failure`` failure-classifier returning an
    ordered ``list[str]`` of playbook-step names, and
    ``execute_playbook_step(session_dir, step, run_id, context)``
    dispatcher that fans out to ``EscalationQueue`` /
    ``DLQManager`` / ``RunMeta`` for the canonical escalation +
    dead-letter steps and returns a ``{"step": ..., "status": ...}``
    envelope for unknown / manual steps (WP-2004, FR-008).

This file is the AUDIT-N+40 contract spec (SOTA pass-24).  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37 / N+38 / N+39) so the next step is to make every
assertion here pass without breaking the dormant corridor
(``tests/orchestration/test_strategies_playbooks.py``) or any other
SOTA audit-N+ invariant cluster.

@trace FR-ORC-PB-001 -- ``get_playbook_for_failure(failure_type)``
                       classifies a free-text failure description
                       into one of fourteen canonical failure
                       categories by reason-keyword matching and
                       returns an ordered ``list[str]`` of playbook
                       step names so the orchestrator can iterate the
                       steps deterministically.
@trace FR-ORC-PB-002 -- ``get_playbook_for_failure`` classifies any
                       message containing the ``timeout`` keyword
                       (``Operation timed out after 30s``) as
                       ``TIMEOUT`` and returns
                       ``["retry_with_backoff", "increase_timeout",
                       "escalate"]`` so the canonical timeout-retry
                       ladder always wins over less-specific matches.
@trace FR-ORC-PB-003 -- ``get_playbook_for_failure`` classifies any
                       message containing the ``rate limit`` /
                       ``429`` keywords as ``RATE_LIMIT`` and
                       returns ``["wait_and_retry",
                       "reduce_concurrency", "escalate"]`` so the
                       orchestrator backs off before retrying.
@trace FR-ORC-PB-004 -- ``get_playbook_for_failure`` classifies any
                       message containing the ``authentication``
                       keyword as ``AUTH_FAILURE`` and returns
                       ``["refresh_credentials", "escalate"]`` so a
                       stale token is refreshed before the run is
                       escalated.
@trace FR-ORC-PB-005 -- ``get_playbook_for_failure`` classifies any
                       message containing the ``network`` /
                       ``connection refused`` keywords as
                       ``NETWORK_PARTITION`` and returns
                       ``["retry", "failover_provider", "escalate"]``
                       so the orchestrator fails over before
                       escalating.
@trace FR-ORC-PB-006 -- ``get_playbook_for_failure`` classifies
                       ``MALFORMED_RESPONSE`` (the ``Invalid JSON``
                       / ``malformed response`` keywords) and
                       ``CONTRACT_DRIFT`` (the ``contract drift`` /
                       ``schema mismatch`` keywords) into their
                       distinct ordered step lists
                       (``MALFORMED_RESPONSE`` →
                       ``["log_drift", "fallback_parser",
                       "escalate"]``;
                       ``CONTRACT_DRIFT`` →
                       ``["emit_drift_event", "fallback_contract",
                       "escalate"]``) so observability events
                       precede the fallback contract switch.
@trace FR-ORC-PB-007 -- ``get_playbook_for_failure`` classifies the
                       remaining six failure categories
                       (``STATE_CORRUPTION``, ``BUDGET_EXCEEDED``,
                       ``CIRCUIT_OPEN``, ``POLICY_DENY``,
                       ``RETRY_EXHAUSTED``, ``CHECKPOINT_FAILED``)
                       into distinct ordered step lists, each
                       terminating in the ``escalate`` sentinel so
                       the human escalation queue always receives
                       the run after the remediation ladder has
                       run.
@trace FR-ORC-PB-008 -- ``get_playbook_for_failure`` classifies any
                       message containing the ``rollback``
                       keyword as ``ROLLBACK_TRIGGERED`` and
                       returns ``["verify_rollback",
                       "resume_or_escalate"]`` (terminating in the
                       ``resume_or_escalate`` sentinel, not the
                       bare ``escalate`` token) so a verified
                       rollback can resume the run without
                       re-escalating.
@trace FR-ORC-PB-009 -- ``get_playbook_for_failure`` falls back to
                       ``["log", "escalate"]`` for any message that
                       matches no category AND for the empty-string
                       message so unknown failures still terminate
                       in the escalation queue.
@trace FR-ORC-PB-010 -- Every ``get_playbook_for_failure`` output
                       list is non-empty and terminates in either
                       the ``escalate`` sentinel step or the
                       ``resume_or_escalate`` sentinel step so the
                       orchestrator always has a final-step
                       fallback into the human queue.
@trace FR-ORC-PB-011 -- ``execute_playbook_step(session_dir, step,
                       run_id, context=None)`` accepts exactly the
                       four-parameter signature ``session_dir`` /
                       ``step`` / ``run_id`` / ``context`` (the
                       latter defaulting to ``None``) so dormant
                       callers that omit ``context`` do not raise
                       ``TypeError: ... got an unexpected keyword
                       argument``.
@trace FR-ORC-PB-012 -- ``execute_playbook_step(..., step=
                       "escalate", context=...)`` constructs an
                       ``EscalationQueue(session_dir)`` and calls
                       ``.add(run_id=..., agent=..., reason=...)``
                       with the ``agent`` and ``reason`` fields
                       lifted from ``context`` (defaulting to
                       ``""`` and ``"playbook_escalation"``
                       respectively when ``context`` is ``None``
                       or missing the relevant keys), returning
                       ``{"step": "escalate", "status":
                       "escalated"}``.
@trace FR-ORC-PB-013 -- ``execute_playbook_step(..., step=
                       "escalate", context=None)`` still routes to
                       ``EscalationQueue.add`` with the safe
                       fallback ``agent=""`` /
                       ``reason="playbook_escalation"`` so the
                       sentinel ``escalate`` step never raises when
                       the orchestrator forgets to pass context.
@trace FR-ORC-PB-014 -- ``execute_playbook_step(..., step=
                       "dlq_enqueue", context=...)`` constructs a
                       ``RunMeta(run_id=..., agent=..., prompt=...,
                       cwd=..., owner=...)`` from ``context`` (with
                       safe defaults ``agent=""``, ``prompt=""``,
                       ``cwd="."``, ``owner="system"`` for missing
                       keys) and calls ``DLQManager(session_dir)
                       .enqueue(...)``, returning
                       ``{"step": "dlq_enqueue", "status":
                       "enqueued"}``.
@trace FR-ORC-PB-015 -- ``execute_playbook_step`` returns the
                       envelope ``{"step": <step>, "status":
                       "pending", "message": "...requires manual
                       execution..."}`` for any step that is not
                       ``escalate`` or ``dlq_enqueue`` (including
                       ``retry``, ``wait_and_retry``, ``log``, and
                       any unknown step name), and ``thegent.
                       orchestration.strategies.playbooks.__all__``
                       exposes the canonical public surface
                       (``execute_playbook_step``,
                       ``get_playbook_for_failure``, ``Playbook``)
                       so callers and dormant tests can rely on a
                       stable import surface.
"""

from __future__ import annotations

from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.strategies import playbooks as _mod
from thegent.orchestration.strategies.playbooks import (
    Playbook,
    execute_playbook_step,
    get_playbook_for_failure,
)

# ---------------------------------------------------------------------------
# Helpers — canonical step lists mirrored from the dormant
# ``test_strategies_playbooks.py`` so the spec is hermetic and never
# reaches into the production source for ground truth.
# ---------------------------------------------------------------------------


_TIMEOUT_STEPS: tuple[str, ...] = ("retry_with_backoff", "increase_timeout", "escalate")
_RATE_LIMIT_STEPS: tuple[str, ...] = (
    "wait_and_retry",
    "reduce_concurrency",
    "escalate",
)
_AUTH_FAILURE_STEPS: tuple[str, ...] = ("refresh_credentials", "escalate")
_NETWORK_PARTITION_STEPS: tuple[str, ...] = ("retry", "failover_provider", "escalate")
_MALFORMED_RESPONSE_STEPS: tuple[str, ...] = (
    "log_drift",
    "fallback_parser",
    "escalate",
)
_STATE_CORRUPTION_STEPS: tuple[str, ...] = ("rollback_checkpoint", "escalate")
_BUDGET_EXCEEDED_STEPS: tuple[str, ...] = ("pause_non_critical", "escalate")
_CIRCUIT_OPEN_STEPS: tuple[str, ...] = (
    "wait_recovery_window",
    "half_open_trial",
    "escalate",
)
_POLICY_DENY_STEPS: tuple[str, ...] = ("request_override", "escalate")
_CONTRACT_DRIFT_STEPS: tuple[str, ...] = (
    "emit_drift_event",
    "fallback_contract",
    "escalate",
)
_RETRY_EXHAUSTED_STEPS: tuple[str, ...] = ("dlq_enqueue", "escalate")
_CHECKPOINT_FAILED_STEPS: tuple[str, ...] = ("retry_checkpoint", "rollback", "escalate")
_ROLLBACK_TRIGGERED_STEPS: tuple[str, ...] = ("verify_rollback", "resume_or_escalate")
_UNKNOWN_STEPS: tuple[str, ...] = ("log", "escalate")


# ---------------------------------------------------------------------------
# FR-ORC-PB-001 -- get_playbook_for_failure return contract
# ---------------------------------------------------------------------------


class TestGetPlaybookForFailureContract:
    """@trace FR-ORC-PB-001"""

    def test_returns_list_of_strings(self) -> None:
        """The return type is a non-empty ``list[str]``."""
        result = get_playbook_for_failure("Operation timed out after 30s")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(step, str) for step in result)

    def test_classifies_timeout_keyword(self) -> None:
        """The ``timeout`` keyword routes to ``TIMEOUT`` playbook."""
        result = get_playbook_for_failure("Operation timed out after 30s")
        assert result == list(_TIMEOUT_STEPS)

    def test_classifies_rate_limit_keyword(self) -> None:
        """The ``rate limit`` / ``429`` keywords route to ``RATE_LIMIT``."""
        result = get_playbook_for_failure("Rate limit exceeded: 429 Too Many Requests")
        assert result == list(_RATE_LIMIT_STEPS)

    def test_classifies_authentication_keyword(self) -> None:
        """The ``authentication`` keyword routes to ``AUTH_FAILURE``."""
        result = get_playbook_for_failure("Authentication failed: invalid token")
        assert result == list(_AUTH_FAILURE_STEPS)

    def test_classifies_network_keyword(self) -> None:
        """The ``network`` keyword routes to ``NETWORK_PARTITION``."""
        result = get_playbook_for_failure("Network unreachable: connection refused")
        assert result == list(_NETWORK_PARTITION_STEPS)


# ---------------------------------------------------------------------------
# FR-ORC-PB-002 / FR-ORC-PB-003 -- TIMEOUT + RATE_LIMIT playbooks
# ---------------------------------------------------------------------------


class TestTimeoutAndRateLimitPlaybooks:
    """@trace FR-ORC-PB-002 / FR-ORC-PB-003"""

    def test_timeout_playbook_is_canonical_ladder(self) -> None:
        result = get_playbook_for_failure("Operation timed out after 30s")
        assert result == ["retry_with_backoff", "increase_timeout", "escalate"]

    def test_timeout_playbook_ends_with_escalate(self) -> None:
        result = get_playbook_for_failure("Connection timed out after 60s")
        assert result[-1] == "escalate"

    def test_rate_limit_playbook_is_canonical_ladder(self) -> None:
        result = get_playbook_for_failure("Rate limit exceeded: 429 Too Many Requests")
        assert result == ["wait_and_retry", "reduce_concurrency", "escalate"]

    def test_rate_limit_playbook_backs_off_before_escalate(self) -> None:
        result = get_playbook_for_failure("API rate limit hit")
        assert result[0] == "wait_and_retry"
        assert result[-1] == "escalate"


# ---------------------------------------------------------------------------
# FR-ORC-PB-004 / FR-ORC-PB-005 -- AUTH_FAILURE + NETWORK_PARTITION
# ---------------------------------------------------------------------------


class TestAuthAndNetworkPlaybooks:
    """@trace FR-ORC-PB-004 / FR-ORC-PB-005"""

    def test_auth_failure_playbook(self) -> None:
        result = get_playbook_for_failure("Authentication failed: invalid token")
        assert result == ["refresh_credentials", "escalate"]

    def test_auth_failure_terminates_in_escalate(self) -> None:
        result = get_playbook_for_failure("Authentication expired")
        assert result[-1] == "escalate"

    def test_network_partition_playbook(self) -> None:
        result = get_playbook_for_failure("Network unreachable: connection refused")
        assert result == ["retry", "failover_provider", "escalate"]

    def test_network_partition_fails_over_before_escalate(self) -> None:
        result = get_playbook_for_failure("Network partition detected")
        assert result[1] == "failover_provider"
        assert result[-1] == "escalate"


# ---------------------------------------------------------------------------
# FR-ORC-PB-006 -- MALFORMED_RESPONSE + CONTRACT_DRIFT
# ---------------------------------------------------------------------------


class TestMalformedAndContractDriftPlaybooks:
    """@trace FR-ORC-PB-006"""

    def test_malformed_response_playbook(self) -> None:
        result = get_playbook_for_failure("Invalid JSON: malformed response")
        assert result == ["log_drift", "fallback_parser", "escalate"]

    def test_malformed_response_observes_drift_before_fallback(self) -> None:
        result = get_playbook_for_failure("Server returned a malformed response body")
        assert result[0] == "log_drift"
        assert result[1] == "fallback_parser"

    def test_contract_drift_playbook(self) -> None:
        result = get_playbook_for_failure("Contract drift: schema mismatch")
        assert result == ["emit_drift_event", "fallback_contract", "escalate"]

    def test_contract_drift_emits_event_before_fallback(self) -> None:
        result = get_playbook_for_failure("Schema drift detected")
        assert result[0] == "emit_drift_event"
        assert result[1] == "fallback_contract"


# ---------------------------------------------------------------------------
# FR-ORC-PB-007 -- the six remaining canonical playbooks
# ---------------------------------------------------------------------------


class TestCanonicalLadderPlaybooks:
    """@trace FR-ORC-PB-007"""

    def test_state_corruption_playbook(self) -> None:
        result = get_playbook_for_failure("State corruption detected: checksum mismatch")
        assert result == ["rollback_checkpoint", "escalate"]

    def test_budget_exceeded_playbook(self) -> None:
        result = get_playbook_for_failure("Budget exceeded: daily limit reached")
        assert result == ["pause_non_critical", "escalate"]

    def test_circuit_open_playbook(self) -> None:
        result = get_playbook_for_failure("Circuit breaker open: too many failures")
        assert result == ["wait_recovery_window", "half_open_trial", "escalate"]

    def test_policy_deny_playbook(self) -> None:
        result = get_playbook_for_failure("Policy denied: operation not allowed")
        assert result == ["request_override", "escalate"]

    def test_retry_exhausted_playbook(self) -> None:
        result = get_playbook_for_failure("Retry exhausted: max attempts reached")
        assert result == ["dlq_enqueue", "escalate"]

    def test_checkpoint_failed_playbook(self) -> None:
        result = get_playbook_for_failure("Checkpoint failed: write error")
        assert result == ["retry_checkpoint", "rollback", "escalate"]

    def test_all_six_terminate_with_escalate(self) -> None:
        cases = [
            "State corruption detected",
            "Budget exceeded",
            "Circuit breaker open",
            "Policy denied",
            "Retry exhausted",
            "Checkpoint failed",
        ]
        for message in cases:
            result = get_playbook_for_failure(message)
            assert result[-1] == "escalate", f"{message!r} → {result}"


# ---------------------------------------------------------------------------
# FR-ORC-PB-008 / FR-ORC-PB-009 -- ROLLBACK_TRIGGERED + UNKNOWN
# ---------------------------------------------------------------------------


class TestRollbackAndUnknownPlaybooks:
    """@trace FR-ORC-PB-008 / FR-ORC-PB-009"""

    def test_rollback_triggered_playbook(self) -> None:
        result = get_playbook_for_failure("Rollback triggered: safety limit exceeded")
        assert result == ["verify_rollback", "resume_or_escalate"]

    def test_rollback_triggered_ends_with_resume_or_escalate(self) -> None:
        result = get_playbook_for_failure("Rollback triggered automatically")
        assert result[-1] == "resume_or_escalate"

    def test_unknown_message_playbook(self) -> None:
        result = get_playbook_for_failure("Some unknown error occurred")
        assert result == ["log", "escalate"]

    def test_empty_message_playbook(self) -> None:
        result = get_playbook_for_failure("")
        assert result == ["log", "escalate"]


# ---------------------------------------------------------------------------
# FR-ORC-PB-010 -- every playbook terminates in an escalation sentinel
# ---------------------------------------------------------------------------


class TestEveryPlaybookEndsWithEscalationSentinel:
    """@trace FR-ORC-PB-010"""

    # Categorical coverage: one message per canonical category plus
    # the sentinel fallback, plus the rollback exception. The
    # fixture mirrors the dormant ``test_strategies_playbooks.py``
    # corpus so the sentinel contract is verified end-to-end.
    _ESCALATION_CASES: ClassVar[tuple[tuple[str, tuple[str, ...]], ...]] = (
        ("Operation timed out after 30s", _TIMEOUT_STEPS),
        ("Rate limit exceeded: 429 Too Many Requests", _RATE_LIMIT_STEPS),
        ("Authentication failed: invalid token", _AUTH_FAILURE_STEPS),
        ("Network unreachable: connection refused", _NETWORK_PARTITION_STEPS),
        ("Invalid JSON: malformed response", _MALFORMED_RESPONSE_STEPS),
        ("State corruption detected: checksum mismatch", _STATE_CORRUPTION_STEPS),
        ("Budget exceeded: daily limit reached", _BUDGET_EXCEEDED_STEPS),
        ("Circuit breaker open: too many failures", _CIRCUIT_OPEN_STEPS),
        ("Policy denied: operation not allowed", _POLICY_DENY_STEPS),
        ("Contract drift: schema mismatch", _CONTRACT_DRIFT_STEPS),
        ("Retry exhausted: max attempts reached", _RETRY_EXHAUSTED_STEPS),
        ("Checkpoint failed: write error", _CHECKPOINT_FAILED_STEPS),
        ("Rollback triggered: safety limit exceeded", _ROLLBACK_TRIGGERED_STEPS),
        ("Some unknown error occurred", _UNKNOWN_STEPS),
        ("", _UNKNOWN_STEPS),
    )

    def test_every_result_is_non_empty(self) -> None:
        for message, _expected in self._ESCALATION_CASES:
            result = get_playbook_for_failure(message)
            assert len(result) > 0, f"{message!r} returned empty list"

    def test_every_result_terminates_in_sentinel(self) -> None:
        for message, _expected in self._ESCALATION_CASES:
            result = get_playbook_for_failure(message)
            assert result[-1] in {"escalate", "resume_or_escalate"}, (
                f"{message!r} → {result!r} does not end with an escalation sentinel"
            )

    def test_every_result_matches_dormant_corpus(self) -> None:
        for message, expected in self._ESCALATION_CASES:
            result = get_playbook_for_failure(message)
            assert tuple(result) == expected, f"{message!r} → {result!r} != {expected!r}"


# ---------------------------------------------------------------------------
# FR-ORC-PB-011 -- execute_playbook_step signature contract
# ---------------------------------------------------------------------------


class TestExecutePlaybookStepSignature:
    """@trace FR-ORC-PB-011"""

    def test_accepts_four_parameter_signature(self, tmp_path: Any) -> None:
        """``execute_playbook_step`` accepts ``session_dir``, ``step``,
        ``run_id``, ``context`` (the latter defaulting to ``None``).
        """
        session_dir = tmp_path / "session"
        # No ``context`` kwarg supplied — must default to None.
        result = execute_playbook_step(
            session_dir=session_dir,
            step="log",
            run_id="run-sig-001",
        )
        assert result["step"] == "log"
        assert result["status"] == "pending"

    def test_accepts_explicit_none_context(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        result = execute_playbook_step(
            session_dir=session_dir,
            step="retry",
            run_id="run-sig-002",
            context=None,
        )
        assert result["status"] == "pending"

    def test_rejects_unknown_kwarg(self, tmp_path: Any) -> None:
        """Calling with an unsupported kwarg must raise ``TypeError``."""
        session_dir = tmp_path / "session"
        with pytest.raises(TypeError):
            execute_playbook_step(
                session_dir=session_dir,
                step="log",
                run_id="run-sig-003",
                unknown_kwarg="boom",
            )


# ---------------------------------------------------------------------------
# FR-ORC-PB-012 / FR-ORC-PB-013 -- escalate step EscalationQueue fan-out
# ---------------------------------------------------------------------------


class TestExecutePlaybookStepEscalate:
    """@trace FR-ORC-PB-012 / FR-ORC-PB-013"""

    def test_escalate_step_calls_escalation_queue_with_context(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
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

    def test_escalate_step_with_none_context_falls_back_to_safe_defaults(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
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

    def test_escalate_step_with_partial_context(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        with patch("thegent.execution.EscalationQueue") as mock_eq:
            mock_instance = MagicMock()
            mock_eq.return_value = mock_instance

            result = execute_playbook_step(
                session_dir=session_dir,
                step="escalate",
                run_id="run-003",
                context={"agent": "worker-7"},
            )

            mock_instance.add.assert_called_once_with(
                run_id="run-003",
                agent="worker-7",
                reason="playbook_escalation",
            )
            assert result == {"step": "escalate", "status": "escalated"}


# ---------------------------------------------------------------------------
# FR-ORC-PB-014 -- dlq_enqueue step DLQManager + RunMeta fan-out
# ---------------------------------------------------------------------------


class TestExecutePlaybookStepDlqEnqueue:
    """@trace FR-ORC-PB-014"""

    def test_dlq_enqueue_constructs_run_meta_and_enqueues(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
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

    def test_dlq_enqueue_uses_safe_defaults_for_missing_context(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        with patch("thegent.execution.DLQManager") as mock_dlq:
            with patch("thegent.execution.RunMeta") as mock_meta:
                mock_instance = MagicMock()
                mock_dlq.return_value = mock_instance

                result = execute_playbook_step(
                    session_dir=session_dir,
                    step="dlq_enqueue",
                    run_id="run-004",
                    context={"error": "failed"},
                )

                mock_meta.assert_called_once_with(
                    run_id="run-004",
                    agent="",
                    prompt="",
                    cwd=".",
                    owner="system",
                )
                assert result == {"step": "dlq_enqueue", "status": "enqueued"}

    def test_dlq_enqueue_with_none_context_uses_safe_defaults(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        with patch("thegent.execution.DLQManager") as mock_dlq:
            with patch("thegent.execution.RunMeta") as mock_meta:
                mock_instance = MagicMock()
                mock_dlq.return_value = mock_instance

                result = execute_playbook_step(
                    session_dir=session_dir,
                    step="dlq_enqueue",
                    run_id="run-005",
                    context=None,
                )

                mock_meta.assert_called_once_with(
                    run_id="run-005",
                    agent="",
                    prompt="",
                    cwd=".",
                    owner="system",
                )
                assert result == {"step": "dlq_enqueue", "status": "enqueued"}


# ---------------------------------------------------------------------------
# FR-ORC-PB-015 -- pending-step envelope + canonical __all__ surface
# ---------------------------------------------------------------------------


class TestExecutePlaybookStepPendingAndAll:
    """@trace FR-ORC-PB-015"""

    def test_unknown_step_returns_pending_envelope(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        result = execute_playbook_step(
            session_dir=session_dir,
            step="unknown_step",
            run_id="run-006",
            context=None,
        )

        assert result["step"] == "unknown_step"
        assert result["status"] == "pending"
        assert "requires manual execution" in result["message"]

    def test_retry_step_returns_pending(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        result = execute_playbook_step(
            session_dir=session_dir,
            step="retry",
            run_id="run-007",
        )

        assert result["status"] == "pending"
        assert result["step"] == "retry"

    def test_wait_and_retry_step_returns_pending(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        result = execute_playbook_step(
            session_dir=session_dir,
            step="wait_and_retry",
            run_id="run-008",
        )

        assert result["status"] == "pending"

    def test_log_step_without_context_returns_pending(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        result = execute_playbook_step(
            session_dir=session_dir,
            step="log",
            run_id="run-009",
        )

        assert result["status"] == "pending"

    def test_pending_step_does_not_touch_escalation_queue(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        with patch("thegent.execution.EscalationQueue") as mock_eq:
            execute_playbook_step(
                session_dir=session_dir,
                step="retry",
                run_id="run-010",
            )
            mock_eq.assert_not_called()

    def test_pending_step_does_not_touch_dlq_manager(self, tmp_path: Any) -> None:
        session_dir = tmp_path / "session"
        with patch("thegent.execution.DLQManager") as mock_dlq:
            execute_playbook_step(
                session_dir=session_dir,
                step="log",
                run_id="run-011",
            )
            mock_dlq.assert_not_called()

    def test_module_all_exposes_canonical_surface(self) -> None:
        """``playbooks.__all__`` exposes the three public symbols."""
        assert sorted(_mod.__all__) == sorted(["Playbook", "execute_playbook_step", "get_playbook_for_failure"])

    def test_playbook_class_is_dataclass_like(self) -> None:
        """``Playbook`` carries ``name`` and ``steps`` attributes and
        exposes an ``execute()`` method that returns a dict so the
        canonical public type contract holds.
        """
        pb = Playbook(name="test", steps=[{"action": "retry"}])
        assert pb.name == "test"
        assert pb.steps == [{"action": "retry"}]
        result = pb.execute()
        assert isinstance(result, dict)
        assert result.get("status") == "ok"
