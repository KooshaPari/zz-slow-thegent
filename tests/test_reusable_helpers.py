"""Tests for reusable_helpers module."""

from pathlib import Path

import orjson as json
import pytest
import yaml

from thegent.utils.reusable_helpers import ReusableHelpers


class TestReusableHelpers:
    """Tests for ReusableHelpers."""

    def test_safe_execute_success(self) -> None:
        """Test safe_execute with success."""

        def success_func(a, b):
            return a + b

        result, error = ReusableHelpers.safe_execute(success_func, 1, 2)
        assert result == 3
        assert error is None

    def test_safe_execute_failure(self) -> None:
        """Test safe_execute with failure."""

        def fail_func():
            raise ValueError("Test error")

        result, error = ReusableHelpers.safe_execute(fail_func)
        assert result is None
        assert isinstance(error, ValueError)

    def test_error_handler_decorator(self) -> None:
        """Test error_handler decorator."""

        @ReusableHelpers.error_handler
        def fail_func():
            raise ValueError("Decorated error")

        with pytest.raises(ValueError, match="Decorated error"):
            fail_func()

    def test_ensure_directory(self, tmp_path: Path) -> None:
        """Test ensure_directory."""
        new_dir = tmp_path / "new" / "dir"
        assert not new_dir.exists()
        ReusableHelpers.ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_load_config_json(self, tmp_path: Path) -> None:
        """Test load_config with JSON."""
        config_path = tmp_path / "config.json"
        data = {"key": "value", "int": 1}
        config_path.write_text(json.dumps(data).decode())

        config = ReusableHelpers.load_config(config_path)
        assert config == data

    def test_load_config_yaml(self, tmp_path: Path) -> None:
        """Test load_config with YAML."""
        config_path = tmp_path / "config.yaml"
        data = {"key": "value", "list": [1, 2, 3]}
        config_path.write_text(yaml.dump(data))

        config = ReusableHelpers.load_config(config_path)
        assert config == data

    def test_load_config_nonexistent(self, tmp_path: Path) -> None:
        """Test load_config with nonexistent file."""
        config = ReusableHelpers.load_config(tmp_path / "missing.json")
        assert config == {}

    def test_read_file_efficiency(self, tmp_path: Path) -> None:
        """Test read_file_efficiency."""
        file_path = tmp_path / "test.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        file_path.write_text("".join(lines))

        # Read with offset
        content = ReusableHelpers.read_file_efficiency(file_path, offset=5)
        assert content == "".join(lines[5:])

        # Read with limit
        content = ReusableHelpers.read_file_efficiency(file_path, offset=2, limit=3)
        assert content == "".join(lines[2:5])

    def test_write_json_safe(self, tmp_path: Path) -> None:
        """Test write_json_safe."""
        file_path = tmp_path / "subdir" / "test.json"
        data = {"a": 1, "b": [2, 3]}
        success = ReusableHelpers.write_json_safe(file_path, data)
        assert success
        assert file_path.exists()
        assert json.loads(file_path.read_text()) == data
