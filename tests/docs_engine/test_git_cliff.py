"""Tests for git-cliff changelog integration.

# @trace FR-DOCS-010
"""

from unittest.mock import MagicMock, patch

from docs_engine.git.cliff import CliffRunner


def test_cliff_runner_builds_command(tmp_path):
    runner = CliffRunner(repo_root=tmp_path, db_path=tmp_path / "test.db")
    cmd = runner._build_command(output=tmp_path / "CHANGELOG.md")
    assert "git-cliff" in cmd[0]
    assert str(tmp_path / "CHANGELOG.md") in cmd


def test_cliff_runner_run_calls_subprocess(tmp_path):
    runner = CliffRunner(repo_root=tmp_path, db_path=tmp_path / "test.db")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## v0.1.0\n\n- feat: initial\n")
        runner.run(output=tmp_path / "CHANGELOG.md")
        mock_run.assert_called_once()


def test_cliff_runner_indexes_changelog(tmp_path):
    from docs_engine.db.queries import DocQueries

    runner = CliffRunner(repo_root=tmp_path, db_path=tmp_path / "test.db")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## v0.1.0\n\n- feat: initial\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        runner.run(output=tmp_path / "CHANGELOG.md")
    results = DocQueries(tmp_path / "test.db").get_by_type("changelog")
    assert len(results) == 1
    assert results[0]["status"] == "published"


def test_cliff_runner_raises_on_nonzero(tmp_path):
    import pytest

    runner = CliffRunner(repo_root=tmp_path, db_path=tmp_path / "test.db")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        with pytest.raises(RuntimeError, match="git-cliff"):
            runner.run(output=tmp_path / "CHANGELOG.md")
