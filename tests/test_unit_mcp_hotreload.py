"""Unit tests for MCP production hot-reload helpers."""

from pathlib import Path

import pytest

from thegent.mcp import hotreload


@pytest.mark.unit
def test_default_watch_paths_only_existing(tmp_path: Path) -> None:
    (tmp_path / "src" / "thegent").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "process-compose.yaml").write_text("version: '0.5'\n", encoding="utf-8")

    paths = hotreload._default_watch_paths(tmp_path)
    assert (tmp_path / "src" / "thegent") in paths
    assert (tmp_path / "scripts") in paths
    assert (tmp_path / "process-compose.yaml") in paths
    assert (tmp_path / "pyproject.toml") not in paths


@pytest.mark.unit
def test_is_relevant_change_filters_expected_paths() -> None:
    assert hotreload._is_relevant_change(Path("/repo/src/thegent/mcp/server.py")) is True
    assert hotreload._is_relevant_change(Path("/repo/process-compose.yaml")) is True
    assert hotreload._is_relevant_change(Path("/repo/docs/readme.md")) is False
    assert hotreload._is_relevant_change(Path("/repo/.venv/lib/site-packages/a.py")) is False


@pytest.mark.unit
def test_run_prod_hotreload_rejects_non_positive_debounce() -> None:
    with pytest.raises(ValueError, match="debounce_s must be > 0"):
        hotreload.run_prod_hotreload(project_root=Path.cwd(), debounce_s=0)
