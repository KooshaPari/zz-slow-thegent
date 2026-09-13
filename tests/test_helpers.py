"""Tests for helpers module — read_json, write_json, find_project_root.

# @trace FR-DX-003
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json
import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.requirement("FR-DX-003")
class TestReadJson:
    """Tests for read_json."""

    def test_read_valid_json(self, tmp_path: Path) -> None:
        """Read a valid JSON file and return dict."""
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value"}).decode())

        from thegent.utils.helpers import read_json

        result = read_json(f)
        assert result == {"key": "value"}

    def test_read_nonexistent_raises(self, tmp_path: Path) -> None:
        """Reading a nonexistent JSON file raises FileNotFoundError."""
        from thegent.utils.helpers import read_json

        with pytest.raises(FileNotFoundError):
            read_json(tmp_path / "missing.json")

    def test_read_invalid_json_raises(self, tmp_path: Path) -> None:
        """Reading invalid JSON raises json.JSONDecodeError."""
        f = tmp_path / "bad.json"
        f.write_text("not json {{{")

        from thegent.utils.helpers import read_json

        with pytest.raises(json.JSONDecodeError):
            read_json(f)


@pytest.mark.requirement("FR-DX-003")
class TestWriteJson:
    """Tests for write_json."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """Write dict to JSON file."""
        f = tmp_path / "out.json"

        from thegent.utils.helpers import write_json

        write_json(f, {"hello": "world"})
        assert json.loads(f.read_text()) == {"hello": "world"}

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Parent directories are created if missing."""
        f = tmp_path / "sub" / "dir" / "out.json"

        from thegent.utils.helpers import write_json

        write_json(f, {"nested": True})
        assert f.exists()

    def test_write_overwrites_existing(self, tmp_path: Path) -> None:
        """Overwrites an existing JSON file."""
        f = tmp_path / "overwrite.json"
        f.write_text(json.dumps({"old": True}).decode())

        from thegent.utils.helpers import write_json

        write_json(f, {"new": True})
        assert json.loads(f.read_text()) == {"new": True}


@pytest.mark.requirement("FR-DX-003")
class TestFindProjectRoot:
    """Tests for find_project_root."""

    def test_finds_pyproject_toml(self, tmp_path: Path) -> None:
        """Walks up to find pyproject.toml."""
        root = tmp_path / "project"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        nested = root / "src" / "pkg"
        nested.mkdir(parents=True)

        from thegent.utils.helpers import find_project_root

        result = find_project_root(nested)
        assert result == root

    def test_raises_when_not_found(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when no pyproject.toml found."""
        from thegent.utils.helpers import find_project_root

        with pytest.raises(FileNotFoundError):
            find_project_root(tmp_path)
