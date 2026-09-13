from __future__ import annotations

from dataclasses import dataclass

from tests.e2e.cli_runner_compat import (
    ATTEMPTED_ARGV_COMMAND_PATH_PREFIX,
    _build_command_surface_drift_skip_message,
    _result_mentions_no_such_command,
)


@dataclass
class DummyResult:
    stdout: str = ""
    stderr: str = ""


def test_build_command_surface_drift_skip_message_includes_prefix_constant_once() -> None:
    message = _build_command_surface_drift_skip_message(
        None,
        ["run", "logs"],
    )

    assert message.count(ATTEMPTED_ARGV_COMMAND_PATH_PREFIX) == 1


def test_build_command_surface_drift_skip_message_preserves_list_argv_token_order() -> None:
    argv = ["recover", "rollback", "--force", "session-42"]
    message = _build_command_surface_drift_skip_message(None, argv)

    assert message.endswith("recover rollback --force session-42")


def test_result_mentions_no_such_command_true_with_stderr_error_mix() -> None:
    result = DummyResult(stderr="Error: No such option: --json. No such command 'logs'.")

    assert _result_mentions_no_such_command(result)


def test_result_mentions_no_such_command_false_with_only_no_such_option() -> None:
    result = DummyResult(stderr="Error: No such option: --json.")

    assert not _result_mentions_no_such_command(result)
