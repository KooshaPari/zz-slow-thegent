from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
import typer

import tests.e2e.cli_runner_compat as cli_runner_compat_module
from tests.e2e.cli_runner_compat import (
    ATTEMPTED_ARGV_COMMAND_PATH_PREFIX,
    COMMAND_SURFACE_DRIFT_SKIP_MESSAGE,
    CompatCliRunner,
    _alias_rewrite_argv,
    _build_command_surface_drift_skip_message,
    _extract_invoke_app,
    _extract_invoke_argv,
    _result_mentions_no_such_command,
)


@dataclass
class DummyResult:
    stdout: str = ""
    stderr: str = ""


def _expected_skip_message(argv: list[str]) -> str:
    attempted_command_path = " ".join(argv)
    return f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} {attempted_command_path}"


def test_invoke_skips_when_no_such_command_in_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_runner_compat_module.CliRunner, "invoke", lambda *args, **kwargs: DummyResult(stdout="No such command: foo")
    )

    runner = CompatCliRunner()
    argv = ["foo", "bar"]
    expected_message = _expected_skip_message(argv)

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(None, argv)


def test_invoke_skips_when_no_such_command_in_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_runner_compat_module.CliRunner, "invoke", lambda *args, **kwargs: DummyResult(stderr="No such command: bar")
    )

    runner = CompatCliRunner()
    argv = ["bar", "baz"]
    expected_message = _expected_skip_message(argv)

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(None, argv)


def test_invoke_does_not_skip_for_normal_result(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = DummyResult(stdout="ok", stderr="")
    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", lambda *args, **kwargs: expected)

    runner = CompatCliRunner()

    assert runner.invoke(None) is expected


def test_invoke_retries_with_alias_rewrite_when_command_surface_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        # Bound monkeypatch call shape is (self, app, argv) for positional args.
        if argv is None and len(args) >= 3:
            argv = args[2]
        argv_list = [str(part) for part in (argv or [])]
        calls.append(argv_list)
        if len(calls) == 1:
            return DummyResult(stderr="No such command: logs")
        return DummyResult(stdout="ok")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    result = runner.invoke(app, ["logs"])

    assert result.stdout == "ok"
    assert calls == [["logs"], ["run", "logs"]]


def test_invoke_retries_with_alias_rewrite_for_kwargs_form_invoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        if argv is None and len(args) >= 3:
            argv = args[2]
        calls.append([str(part) for part in (argv or [])])
        if len(calls) == 1:
            return DummyResult(stderr="No such command: logs")
        return DummyResult(stdout="ok")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    result = runner.invoke(app=app, args=["logs"])

    assert result.stdout == "ok"
    assert calls == [["logs"], ["run", "logs"]]


def test_invoke_retry_preserves_non_args_kwargs_when_rewriting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_invoke(*args, **kwargs):
        calls.append((args, dict(kwargs)))
        if len(calls) == 1:
            return DummyResult(stderr="No such command: logs")
        return DummyResult(stdout="ok")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    env = {"THGENT_TEST_ENV": "1"}
    result = runner.invoke(app=app, args=["logs"], env=env, catch_exceptions=False)

    assert result.stdout == "ok"
    assert len(calls) == 2
    first_args, first_kwargs = calls[0]
    assert len(first_args) == 1
    assert first_kwargs == {
        "app": app,
        "args": ["logs"],
        "env": env,
        "catch_exceptions": False,
    }
    second_args, second_kwargs = calls[1]
    assert len(second_args) == 1
    assert second_kwargs == {
        "app": app,
        "args": ["run", "logs"],
        "env": env,
        "catch_exceptions": False,
    }


def test_invoke_retry_from_positional_call_uses_positional_app_and_kwargs_args_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_invoke(*args, **kwargs):
        calls.append((args, dict(kwargs)))
        if len(calls) == 1:
            return DummyResult(stderr="No such command: logs")
        return DummyResult(stdout="ok")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    result = runner.invoke(app, ["logs"])

    assert result.stdout == "ok"
    assert len(calls) == 2
    first_args, first_kwargs = calls[0]
    assert len(first_args) == 3
    assert first_args[1] is app
    assert first_args[2] == ["logs"]
    assert first_kwargs == {}
    second_args, second_kwargs = calls[1]
    assert len(second_args) == 2
    assert second_args[1] is app
    assert second_kwargs == {"args": ["run", "logs"]}


def test_invoke_does_not_retry_when_alias_rewrite_returns_none_even_on_no_such_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    rewrite_calls: list[tuple[object, object]] = []

    def fake_invoke(*args, **kwargs):
        calls.append((args, dict(kwargs)))
        return DummyResult(stderr="No such command: logs")

    def fake_alias_rewrite_argv(rewrite_app: object, rewrite_argv: object) -> None:
        rewrite_calls.append((rewrite_app, rewrite_argv))

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)
    monkeypatch.setattr(cli_runner_compat_module, "_alias_rewrite_argv", fake_alias_rewrite_argv)

    runner = CompatCliRunner()
    expected_message = _expected_skip_message(["logs"])

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(app=app, args=["logs"])

    assert len(calls) == 1
    assert rewrite_calls == [(app, ["logs"])]


def test_invoke_skips_when_retry_still_reports_no_such_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        if argv is None and len(args) >= 3:
            argv = args[2]
        calls.append([str(part) for part in (argv or [])])
        return DummyResult(stderr="No such command: logs")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    expected_message = _expected_skip_message(["logs"])

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(app=app, args=["logs"])

    assert calls == [["logs"], ["run", "logs"]]


def test_invoke_does_not_retry_or_skip_for_no_such_option_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []
    expected = DummyResult(stderr="No such option: --tail")

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        if argv is None and len(args) >= 3:
            argv = args[2]
        calls.append([str(part) for part in (argv or [])])
        return expected

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    result = runner.invoke(app=app, args=["logs"])

    assert result is expected
    assert calls == [["logs"]]


def test_invoke_does_not_rewrite_argumentful_alias_and_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs(_target: str) -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        if argv is None and len(args) >= 3:
            argv = args[2]
        argv_list = [str(part) for part in (argv or [])]
        calls.append(argv_list)
        return DummyResult(stderr="No such command: logs")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    argv = ["logs", "session-123"]
    expected_message = _expected_skip_message(argv)

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(app, argv)

    assert calls == [argv]


def test_invoke_does_not_rewrite_option_bearing_alias_and_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs(follow: bool = typer.Option(False, "--follow")) -> None:
        return None

    app.add_typer(run_app, name="run")

    calls: list[list[str]] = []

    def fake_invoke(*args, **kwargs):
        argv = kwargs.get("args")
        if argv is None and len(args) >= 3:
            argv = args[2]
        argv_list = [str(part) for part in (argv or [])]
        calls.append(argv_list)
        return DummyResult(stderr="No such command: logs")

    monkeypatch.setattr(cli_runner_compat_module.CliRunner, "invoke", fake_invoke)

    runner = CompatCliRunner()
    argv = ["logs", "--follow"]
    expected_message = _expected_skip_message(argv)

    with pytest.raises(pytest.skip.Exception, match=re.escape(expected_message)):
        runner.invoke(app, argv)

    assert calls == [argv]


def test_build_command_surface_drift_skip_message_extracts_positional_args() -> None:
    message = _build_command_surface_drift_skip_message("app", ["logs", "now"])

    assert message == _expected_skip_message(["logs", "now"])


def test_build_command_surface_drift_skip_message_extracts_kwargs_args() -> None:
    message = _build_command_surface_drift_skip_message(app="app", args=["status"])

    assert message == _expected_skip_message(["status"])


def test_build_command_surface_drift_skip_message_handles_tuple_argv() -> None:
    message = _build_command_surface_drift_skip_message("app", ("logs", "now"))

    assert message == _expected_skip_message(["logs", "now"])


def test_build_command_surface_drift_skip_message_handles_scalar_positional_argv() -> None:
    message = _build_command_surface_drift_skip_message("app", "logs")

    assert message == (f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} logs")


def test_build_command_surface_drift_skip_message_handles_missing_args() -> None:
    message = _build_command_surface_drift_skip_message("app")

    assert message == (f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} <unspecified>")


def test_extract_invoke_app_extracts_positional_app() -> None:
    app = object()
    assert _extract_invoke_app(app, ["logs"]) is app


def test_extract_invoke_app_extracts_kwargs_app() -> None:
    app = object()
    assert _extract_invoke_app(app=app, args=["logs"]) is app


def test_extract_invoke_app_prefers_positional_over_kwargs() -> None:
    positional_app = object()
    kwargs_app = object()

    assert _extract_invoke_app(positional_app, app=kwargs_app, args=["logs"]) is positional_app


def test_extract_invoke_app_returns_none_when_missing() -> None:
    assert _extract_invoke_app() is None


def test_extract_invoke_argv_extracts_positional_args() -> None:
    argv = ["logs", "now"]
    assert _extract_invoke_argv("app", argv) == argv


def test_extract_invoke_argv_extracts_kwargs_args() -> None:
    argv = ["status"]
    assert _extract_invoke_argv(app="app", args=argv) == argv


def test_extract_invoke_argv_prefers_positional_over_kwargs_args() -> None:
    positional_argv = ["logs"]
    kwargs_argv = ["status"]

    assert _extract_invoke_argv("app", positional_argv, args=kwargs_argv) == positional_argv


def test_extract_invoke_argv_returns_none_when_positional_is_explicitly_none_and_kwargs_missing() -> None:
    assert _extract_invoke_argv("app", None) is None


def test_extract_invoke_argv_returns_none_when_missing() -> None:
    assert _extract_invoke_argv("app") is None


@pytest.mark.parametrize(
    ("args", "kwargs", "expected"),
    [
        (("app", ("logs", "now")), {}, ("logs", "now")),
        ((), {"app": "app", "args": "logs"}, "logs"),
    ],
)
def test_extract_invoke_argv_edge_cases(
    args: tuple[object, ...],
    kwargs: dict[str, object],
    expected: object,
) -> None:
    assert _extract_invoke_argv(*args, **kwargs) == expected


@pytest.mark.parametrize(
    ("stdout", "stderr"),
    [
        ("NO SUCH COMMAND: logs", ""),
        ("", "No SuCh CoMmAnD: logs"),
    ],
)
def test_result_mentions_no_such_command_positive_cases_in_stdout_or_stderr(
    stdout: str,
    stderr: str,
) -> None:
    assert _result_mentions_no_such_command(DummyResult(stdout=stdout, stderr=stderr))


def test_result_mentions_no_such_command_handles_none_stdout_stderr_values() -> None:
    class ResultWithNoneStreams:
        stdout = None
        stderr = None

    assert not _result_mentions_no_such_command(ResultWithNoneStreams())


def test_result_mentions_no_such_command_handles_missing_stdout_stderr_attributes() -> None:
    assert not _result_mentions_no_such_command(object())


def test_result_mentions_no_such_command_ignores_separate_no_and_command_words() -> None:
    result = DummyResult(
        stdout="There is no issue here; we can run another command later.",
        stderr="",
    )

    assert not _result_mentions_no_such_command(result)


def test_result_mentions_no_such_command_returns_false_when_absent() -> None:
    assert not _result_mentions_no_such_command(DummyResult(stdout="ok", stderr="done"))


def test_alias_rewrite_argv_returns_none_for_non_typer_app() -> None:
    assert _alias_rewrite_argv(object(), ["logs"]) is None


def test_alias_rewrite_argv_returns_none_for_non_list_tuple_argv() -> None:
    app = typer.Typer()
    assert _alias_rewrite_argv(app, "logs") is None


@pytest.mark.parametrize(
    ("argv", "group_name", "command_name", "expected"),
    [
        (["logs"], "run", "logs", ["run", "logs"]),
        (["recover", "rollback"], "plan", "rollback", ["plan", "rollback"]),
    ],
)
def test_alias_rewrite_argv_rewrites_exact_alias_path_when_canonical_exists(
    argv: list[str],
    group_name: str,
    command_name: str,
    expected: list[str],
) -> None:
    app = typer.Typer()
    canonical_group = typer.Typer()

    @canonical_group.command(command_name)
    def _canonical() -> None:
        return None

    app.add_typer(canonical_group, name=group_name)

    assert _alias_rewrite_argv(app, argv) == expected


def test_alias_rewrite_argv_does_not_rewrite_when_alias_has_trailing_token() -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def _logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    assert _alias_rewrite_argv(app, ["logs", "--follow"]) is None


def test_alias_rewrite_argv_returns_none_when_rewritten_path_missing() -> None:
    app = typer.Typer()

    @app.command("unrelated")
    def _unrelated() -> None:
        return None

    assert _alias_rewrite_argv(app, ["logs"]) is None
