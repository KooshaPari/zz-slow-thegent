from __future__ import annotations

from tests.e2e.cli_runner_compat import (
    ATTEMPTED_ARGV_COMMAND_PATH_PREFIX,
    COMMAND_SURFACE_DRIFT_SKIP_MESSAGE,
    _build_command_surface_drift_skip_message,
)


def test_skip_message_starts_with_surface_drift_prefix() -> None:
    message = _build_command_surface_drift_skip_message(None, ["logs"])
    assert message.startswith(COMMAND_SURFACE_DRIFT_SKIP_MESSAGE)


def test_skip_message_contains_attempted_prefix_once() -> None:
    message = _build_command_surface_drift_skip_message(None, ["logs", "--tail", "10"])
    assert message.count(ATTEMPTED_ARGV_COMMAND_PATH_PREFIX) == 1


def test_skip_message_retains_exact_token_joining() -> None:
    message = _build_command_surface_drift_skip_message(None, ["run", "logs", "--tail", "10"])
    assert message.endswith("run logs --tail 10")
