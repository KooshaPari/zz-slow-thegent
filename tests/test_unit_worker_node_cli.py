"""CLI tests for worker_node Typer entrypoint."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from thegent.infra.worker_node import app as worker_app

runner = CliRunner()


def test_help_exits_zero() -> None:
    result = runner.invoke(worker_app, ["--help"])
    assert result.exit_code == 0


def test_required_options_enforced() -> None:
    result = runner.invoke(worker_app, [])
    assert result.exit_code != 0


def test_runs_worker_loop_with_options(tmp_path: Path) -> None:
    with (
        patch(
            "thegent.infra.worker_node.worker_loop",
            new=MagicMock(return_value="sentinel"),
        ) as mock_loop,
        patch("thegent.infra.worker_node.asyncio.run") as mock_asyncio_run,
    ):
        result = runner.invoke(
            worker_app,
            [
                "--mesh-root",
                str(tmp_path),
                "--runtime",
                "CPYTHON",
            ],
        )

    assert result.exit_code == 0
    mock_loop.assert_called_once_with(Path(tmp_path), "CPYTHON")
    mock_asyncio_run.assert_called_once_with("sentinel")
