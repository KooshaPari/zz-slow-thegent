"""Unit tests for orchestration recovery modules (WP-2003, WP-2004, WP-2005, WP-2006, WP-2008, WP-Y2)."""

from __future__ import annotations

import pytest

from thegent.orchestration.resilience.circuit_breaker import is_open, should_allow

pytestmark = pytest.mark.unit
from typing import TYPE_CHECKING

from thegent.orchestration.failure_modes import FailureMode, classify_failure
from thegent.orchestration.oversight import (
    get_oversight_action,
    should_trigger_oversight,
)
from thegent.orchestration.playbooks import get_playbook_for_failure
from thegent.orchestration.probes import (
    run_post_rollback_probes,
    run_pre_promote_probes,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestFailureModes:
    """WP-2005: MAST 14-mode failure taxonomy."""

    def test_classify_timeout(self) -> None:
        assert classify_failure("request timed out") == FailureMode.TIMEOUT

    def test_classify_rate_limit(self) -> None:
        assert classify_failure("429 rate limit exceeded") == FailureMode.RATE_LIMIT

    def test_classify_auth(self) -> None:
        assert classify_failure("401 unauthorized") == FailureMode.AUTH_FAILURE

    def test_classify_unknown(self) -> None:
        assert classify_failure("something random") == FailureMode.UNKNOWN


class TestPlaybooks:
    """WP-2004: Recovery playbook automation."""

    def test_playbook_timeout(self) -> None:
        steps = get_playbook_for_failure("timeout exceeded")
        assert "retry_with_backoff" in steps
        assert "escalate" in steps

    def test_playbook_unknown(self) -> None:
        steps = get_playbook_for_failure("xyz")
        assert "log" in steps or "escalate" in steps


class TestProbes:
    """WP-2006: Regression prevention probes."""

    def test_pre_promote_probes(self, tmp_path: Path) -> None:
        r = run_pre_promote_probes(tmp_path)
        assert "passed" in r
        assert "findings" in r

    def test_post_rollback_probes(self, tmp_path: Path) -> None:
        r = run_post_rollback_probes(tmp_path)
        assert r["passed"] is True


class TestOversight:
    """WP-2008: Controlled oversight."""

    def test_should_trigger_oversight(self, tmp_path: Path) -> None:
        assert not should_trigger_oversight(tmp_path, "agent", 2, threshold=3)
        assert should_trigger_oversight(tmp_path, "agent", 3, threshold=3)

    def test_get_oversight_action(self) -> None:
        assert get_oversight_action(1) == "continue"
        assert get_oversight_action(3) == "pause"
        assert get_oversight_action(5) == "escalate"


class TestCircuitBreaker:
    """WP-2003: Circuit breakers per subsystem."""

    def test_should_allow_when_no_failures(self, tmp_path: Path) -> None:
        assert should_allow(tmp_path, "test-agent") is True

    def test_is_open_initially_false(self, tmp_path: Path) -> None:
        assert is_open(tmp_path, "test-agent") is False
