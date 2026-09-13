from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thegent.main import app

runner = CliRunner()


@pytest.mark.unit
def test_compositor_top_level_routes_to_handler() -> None:
    # @trace FR-MAIN-101
    with patch("thegent.main.run_compositor_tui") as mock_cmd:
        result = runner.invoke(
            app,
            [
                "compositor",
                "--layout",
                "stacked",
                "--include-non-claude",
                "--once",
                "--refresh",
                "0.5",
            ],
        )

    assert result.exit_code == 0
    mock_cmd.assert_called_once_with(layout_name="stacked", include_non_claude=True, once=True, refresh_interval=0.5)


@pytest.mark.unit
def test_compositor_observe_subcommand_routes_to_handler() -> None:
    # @trace FR-MAIN-102
    with patch("thegent.main.run_compositor_tui") as mock_cmd:
        result = runner.invoke(app, ["observe", "compositor", "--once"])

    assert result.exit_code == 0
    mock_cmd.assert_called_once_with(
        layout_name="balanced",
        include_non_claude=False,
        once=True,
        refresh_interval=1.0,
    )
