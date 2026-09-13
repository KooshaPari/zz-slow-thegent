"""Unit tests for droid runner module (agents/droid.py)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.droid import (
    CodexRunner,
    CustomCliRunner,
    DroidRunner,
    _resolve_cmd,
    _resolve_droid_cmd,
    get_droid_runner,
)
from thegent.utils import strip_ansi


@pytest.mark.unit
class TestStripAnsi:
    """Tests for strip_ansi helper."""

    def test_strips_color_codes(self) -> None:
        # @trace FR-DRD-001
        assert strip_ansi("\x1b[32mgreen\x1b[0m") == "green"

    def test_passthrough_plain_text(self) -> None:
        # @trace FR-DRD-001
        assert strip_ansi("plain text") == "plain text"

    def test_strips_multiple_codes(self) -> None:
        # @trace FR-DRD-001
        assert strip_ansi("\x1b[1;31mred bold\x1b[0m \x1b[34mblue\x1b[0m") == "red bold blue"


@pytest.mark.unit
class TestResolveCmd:
    """Tests for _resolve_cmd."""

    def test_returns_cmd_as_is_when_not_path(self) -> None:
        # @trace FR-DRD-002
        result = _resolve_cmd("echo")
        assert result == "echo"

    def test_returns_absolute_path_when_exists(self, tmp_path: Path) -> None:
        # @trace FR-DRD-002
        binary = tmp_path / "mybinary"
        binary.touch()
        binary.chmod(0o755)
        result = _resolve_cmd(str(binary))
        assert result == str(binary)

    def test_uses_candidate_when_available(self, tmp_path: Path) -> None:
        # @trace FR-DRD-002
        candidate = tmp_path / "candidate_bin"
        candidate.touch()
        result = _resolve_cmd("nonexistent", candidates=[candidate])
        assert result == str(candidate)

    def test_skips_missing_candidates(self) -> None:
        # @trace FR-DRD-002
        missing = Path("/nonexistent/path/to/binary")
        result = _resolve_cmd("fallback", candidates=[missing])
        assert result == "fallback"


@pytest.mark.unit
class TestResolveDroidCmd:
    """Tests for _resolve_droid_cmd."""

    def test_returns_droid_when_no_candidates_exist(self) -> None:
        # @trace FR-DRD-002
        result = _resolve_droid_cmd("droid")
        # Should return "droid" if neither ~/.local/bin/droid nor ~/.factory/bin/droid exist
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("thegent.agents.droid.Path.exists", return_value=False)
    def test_falls_back_to_cmd_string(self, _mock_exists: MagicMock) -> None:
        # @trace FR-DRD-002
        result = _resolve_droid_cmd("my-droid")
        assert result == "my-droid"


@pytest.mark.unit
class TestDroidRunner:
    """Tests for DroidRunner class."""

    def _make_runner(self, tmp_path: Path) -> DroidRunner:
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        return DroidRunner(
            droid_name="test-droid",
            droids_dir=droids_dir,
            droid_cmd="droid",
            model="test-model",
        )

    def test_init_stores_attributes(self, tmp_path: Path) -> None:
        # @trace FR-DRD-003
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        runner = DroidRunner(
            droid_name="my-droid",
            droids_dir=droids_dir,
            droid_cmd="droid",
            model="custom:TestModel",
        )
        assert runner.droid_name == "my-droid"
        assert runner.droids_dir == droids_dir.resolve()
        assert runner._model == "custom:TestModel"

    def test_run_returns_error_when_droid_file_missing(self, tmp_path: Path) -> None:
        # @trace FR-DRD-004
        runner = self._make_runner(tmp_path)
        result = runner.run(prompt="hello", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "Droid not found" in result.stderr
        assert result.timed_out is False

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-005
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Test Droid\nInstructions here.")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="task completed",
            stderr="",
        )

        result = runner.run(prompt="do something", cwd=tmp_path, mode="write", timeout=60)
        assert result.exit_code == 0
        assert result.stdout == "task completed"
        mock_run.assert_called_once()

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_write_mode_sets_auto_low(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-006
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner.run(prompt="test", cwd=tmp_path, mode="write", timeout=30)

        cmd = mock_run.call_args[0][0]
        assert "--auto" in cmd
        assert "low" in cmd

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_full_mode_sets_auto_high(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-006
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner.run(prompt="test", cwd=tmp_path, mode="full", timeout=30)

        cmd = mock_run.call_args[0][0]
        assert "--auto" in cmd
        assert "high" in cmd

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_minimax_forces_stream_output_format(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-006
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        runner = DroidRunner(
            droid_name="test-droid",
            droids_dir=droids_dir,
            droid_cmd="droid",
            model="custom:minimax-m2.5",
        )
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner.run(prompt="test", cwd=tmp_path, mode="full", timeout=30, use_stream=False)

        cmd = mock_run.call_args[0][0]
        assert "--output-format" in cmd
        assert "stream-json" in cmd

    @patch("thegent.agents.droid.run_subprocess_optimized", side_effect=FileNotFoundError)
    def test_run_missing_binary(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-007
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "droid CLI not found" in result.stderr

    @patch(
        "thegent.agents.droid.run_subprocess_optimized",
        side_effect=subprocess.TimeoutExpired(cmd="droid", timeout=30),
    )
    def test_run_timeout(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-008
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_strips_ansi_from_output(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-009
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "test-droid.md"
        droid_file.write_text("# Droid")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\x1b[32mgreen output\x1b[0m",
            stderr="\x1b[31merror\x1b[0m",
        )
        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert "\x1b" not in result.stdout
        assert "\x1b" not in result.stderr


@pytest.mark.unit
class TestCodexRunner:
    """Tests for CodexRunner class."""

    def _make_runner(self, tmp_path: Path) -> CodexRunner:
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        return CodexRunner(
            droid_name="codex-droid",
            droids_dir=droids_dir,
            codex_cmd="codex",
            model="gpt-test",
        )

    def test_init_stores_attributes(self, tmp_path: Path) -> None:
        # @trace FR-DRD-010
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        runner = CodexRunner(
            droid_name="codex-droid",
            droids_dir=droids_dir,
            codex_cmd="codex",
            model="gpt-5",
        )
        assert runner.droid_name == "codex-droid"
        assert runner._model == "gpt-5"

    def test_run_returns_error_when_droid_missing(self, tmp_path: Path) -> None:
        # @trace FR-DRD-011
        runner = self._make_runner(tmp_path)
        result = runner.run(prompt="hello", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "Droid not found" in result.stderr

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_success_sends_prompt_via_stdin(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-012
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "codex-droid.md"
        droid_file.write_text("# Codex Droid")

        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        result = runner.run(prompt="do it", cwd=tmp_path, mode="read", timeout=60)

        assert result.exit_code == 0
        # Verify input was passed (combined droid content + prompt)
        call_kwargs = mock_run.call_args[1]
        assert "# Codex Droid" in call_kwargs["input"]
        assert "do it" in call_kwargs["input"]

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_write_mode_sets_sandbox(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-013
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "codex-droid.md"
        droid_file.write_text("# Codex")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner.run(prompt="test", cwd=tmp_path, mode="write", timeout=30)

        cmd = mock_run.call_args[0][0]
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_full_mode_sets_full_auto(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-013
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "codex-droid.md"
        droid_file.write_text("# Codex")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner.run(prompt="test", cwd=tmp_path, mode="full", timeout=30)

        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd

    @patch("thegent.agents.droid.run_subprocess_optimized", side_effect=FileNotFoundError)
    def test_run_missing_codex_binary(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-014
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "codex-droid.md"
        droid_file.write_text("# Codex")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "Codex CLI not found" in result.stderr

    @patch(
        "thegent.agents.droid.run_subprocess_optimized",
        side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=60),
    )
    def test_run_timeout(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-015
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "codex-droid.md"
        droid_file.write_text("# Codex")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=60)
        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr


@pytest.mark.unit
class TestCustomCliRunner:
    """Tests for CustomCliRunner class."""

    def _make_runner(self, tmp_path: Path, custom_cmd: str = "mycli") -> CustomCliRunner:
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir(exist_ok=True)
        return CustomCliRunner(
            droid_name="custom-droid",
            droids_dir=droids_dir,
            custom_cmd=custom_cmd,
            model="custom-model",
        )

    def test_init_plain_command(self, tmp_path: Path) -> None:
        # @trace FR-DRD-016
        runner = self._make_runner(tmp_path, custom_cmd="claudemax")
        assert runner._custom_cmd == "claudemax"

    def test_init_empty_command(self, tmp_path: Path) -> None:
        # @trace FR-DRD-016
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        runner = CustomCliRunner(droid_name="x", droids_dir=droids_dir, custom_cmd="", model="")
        assert runner._custom_cmd == ""

    def test_init_path_command_resolved(self, tmp_path: Path) -> None:
        # @trace FR-DRD-016
        droids_dir = tmp_path / "droids"
        droids_dir.mkdir()
        runner = CustomCliRunner(
            droid_name="x",
            droids_dir=droids_dir,
            custom_cmd="/usr/local/bin/mycli",
            model="",
        )
        assert runner._custom_cmd == "/usr/local/bin/mycli"

    def test_run_returns_error_when_droid_missing(self, tmp_path: Path) -> None:
        # @trace FR-DRD-017
        runner = self._make_runner(tmp_path)
        result = runner.run(prompt="hello", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "Droid not found" in result.stderr

    @patch("thegent.agents.droid.run_subprocess_optimized")
    def test_run_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-018
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "custom-droid.md"
        droid_file.write_text("# Custom Droid")

        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        result = runner.run(prompt="do stuff", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 0
        assert result.stdout == "output"

    @patch("thegent.agents.droid.run_subprocess_optimized", side_effect=FileNotFoundError)
    def test_run_missing_custom_binary(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-019
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "custom-droid.md"
        droid_file.write_text("# Custom")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 1
        assert "Custom CLI not found" in result.stderr

    @patch(
        "thegent.agents.droid.run_subprocess_optimized",
        side_effect=subprocess.TimeoutExpired(cmd="mycli", timeout=30),
    )
    def test_run_timeout(self, _mock_run: MagicMock, tmp_path: Path) -> None:
        # @trace FR-DRD-020
        runner = self._make_runner(tmp_path)
        droid_file = runner.droids_dir / "custom-droid.md"
        droid_file.write_text("# Custom")

        result = runner.run(prompt="test", cwd=tmp_path, mode="read", timeout=30)
        assert result.exit_code == 124
        assert result.timed_out is True


@pytest.mark.unit
class TestGetDroidRunner:
    """Tests for get_droid_runner factory."""

    def test_returns_codex_runner_for_codex_backend(self, tmp_path: Path) -> None:
        # @trace FR-DRD-021
        runner = get_droid_runner("codex", "my-droid", tmp_path)
        assert isinstance(runner, CodexRunner)

    def test_returns_custom_runner_when_custom_cmd_provided(self, tmp_path: Path) -> None:
        # @trace FR-DRD-022
        runner = get_droid_runner("custom", "my-droid", tmp_path, custom_cmd="claudemax")
        assert isinstance(runner, CustomCliRunner)

    def test_returns_droid_runner_as_default(self, tmp_path: Path) -> None:
        # @trace FR-DRD-023
        runner = get_droid_runner("droid", "my-droid", tmp_path)
        assert isinstance(runner, DroidRunner)

    def test_returns_droid_runner_for_unknown_backend(self, tmp_path: Path) -> None:
        # @trace FR-DRD-023
        runner = get_droid_runner("unknown-thing", "my-droid", tmp_path)
        assert isinstance(runner, DroidRunner)

    def test_custom_without_cmd_falls_back_to_droid(self, tmp_path: Path) -> None:
        # @trace FR-DRD-024
        runner = get_droid_runner("custom", "my-droid", tmp_path, custom_cmd="")
        assert isinstance(runner, DroidRunner)

    def test_codex_backend_case_insensitive(self, tmp_path: Path) -> None:
        # @trace FR-DRD-025
        runner = get_droid_runner("  CODEX  ", "my-droid", tmp_path)
        assert isinstance(runner, CodexRunner)
