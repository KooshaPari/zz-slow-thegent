from __future__ import annotations

from dataclasses import dataclass

from tests.e2e.cli_runner_compat import (
    _extract_invoke_app,
    _extract_invoke_argv,
    _result_mentions_no_such_command,
)


@dataclass
class DummyResult:
    stdout: str | None = ""
    stderr: str | None = ""


class NoStreamsResult:
    pass


def test_extract_invoke_app_prefers_positional_over_kwargs() -> None:
    positional_app = object()
    kwargs_app = object()

    app = _extract_invoke_app(positional_app, app=kwargs_app)

    assert app is positional_app


def test_extract_invoke_app_uses_kwargs_when_no_positional() -> None:
    kwargs_app = object()

    app = _extract_invoke_app(app=kwargs_app)

    assert app is kwargs_app


def test_extract_invoke_argv_prefers_positional_over_kwargs() -> None:
    positional_argv = ["from-positional"]
    kwargs_argv = ["from-kwargs"]

    argv = _extract_invoke_argv(object(), positional_argv, args=kwargs_argv)

    assert argv == positional_argv


def test_extract_invoke_argv_uses_kwargs_when_no_positional() -> None:
    kwargs_argv = ["from-kwargs"]

    argv = _extract_invoke_argv(args=kwargs_argv)

    assert argv == kwargs_argv


def test_result_mentions_no_such_command_true_for_stdout_mixed_case() -> None:
    result = DummyResult(stdout="Oops: nO SuCh CoMmAnD happened")

    assert _result_mentions_no_such_command(result)


def test_result_mentions_no_such_command_true_for_stderr_mixed_case() -> None:
    result = DummyResult(stderr="Error: NO SUCH COMMAND used")

    assert _result_mentions_no_such_command(result)


def test_result_mentions_no_such_command_false_when_absent_or_empty_attrs() -> None:
    assert not _result_mentions_no_such_command(DummyResult(stdout="all good", stderr="still fine"))
    assert not _result_mentions_no_such_command(DummyResult(stdout=None, stderr=None))
    assert not _result_mentions_no_such_command(NoStreamsResult())
