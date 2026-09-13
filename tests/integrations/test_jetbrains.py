"""Tests for thegent.integrations.jetbrains — JetBrains IDE MCP integration.

FR traceability: FR-IDE-001 (JetBrains MCP integration)

All filesystem operations use pytest's tmp_path fixture so the real
~/.config/JetBrains/ directory is never touched.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import orjson as json
import pytest

from thegent.integrations.jetbrains import (
    _IDE_DIR_PREFIXES,
    DEFAULT_MCP_SERVER_URL,
    JetBrainsConfig,
    JetBrainsIntegration,
    _jetbrains_base_dirs,
    _match_ide_type,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_jb_base(tmp_path: Path) -> Path:
    """Create a fake JetBrains base directory with several IDE sub-dirs."""
    base = tmp_path / "JetBrains"
    base.mkdir()
    for name in [
        "PyCharm2024.2",
        "IntelliJIdea2024.1",
        "GoLand2023.3",
        "WebStorm2024.1",
        "NotAnIDE",
    ]:
        (base / name).mkdir()
    return base


@pytest.fixture
def integration() -> JetBrainsIntegration:
    return JetBrainsIntegration()


@pytest.fixture
def pycharm_config(tmp_path: Path) -> JetBrainsConfig:
    return JetBrainsConfig(
        ide_type="pycharm",
        config_dir=tmp_path / "PyCharm2024.2",
    )


# ---------------------------------------------------------------------------
# Tests: JetBrainsConfig dataclass  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestJetBrainsConfig:
    """Tests for JetBrainsConfig dataclass construction and properties."""

    def test_mcp_config_path_is_mcp_json(self, tmp_path: Path) -> None:
        """mcp_config_path must be <config_dir>/mcp.json. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="pycharm", config_dir=tmp_path)
        assert cfg.mcp_config_path == tmp_path / "mcp.json"

    def test_default_mcp_server_url(self, tmp_path: Path) -> None:
        """Default mcp_server_url equals DEFAULT_MCP_SERVER_URL. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="intellij", config_dir=tmp_path)
        assert cfg.mcp_server_url == DEFAULT_MCP_SERVER_URL

    def test_custom_mcp_server_url(self, tmp_path: Path) -> None:
        """Custom mcp_server_url is stored correctly. @trace FR-IDE-001"""
        url = "http://localhost:9999/mcp"
        cfg = JetBrainsConfig(ide_type="goland", config_dir=tmp_path, mcp_server_url=url)
        assert cfg.mcp_server_url == url

    def test_default_serena_project_root_is_empty(self, tmp_path: Path) -> None:
        """Default serena_project_root is an empty string. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="clion", config_dir=tmp_path)
        assert cfg.serena_project_root == ""

    def test_invalid_ide_type_raises_value_error(self, tmp_path: Path) -> None:
        """Constructing with an unknown ide_type raises ValueError. @trace FR-IDE-001"""
        with pytest.raises(ValueError, match="ide_type must be one of"):
            JetBrainsConfig(ide_type="sublime", config_dir=tmp_path)

    def test_all_valid_ide_types_accepted(self, tmp_path: Path) -> None:
        """All valid IDE types can be used without error. @trace FR-IDE-001"""
        valid_types = list(_IDE_DIR_PREFIXES.keys())
        for ide_type in valid_types:
            cfg = JetBrainsConfig(ide_type=ide_type, config_dir=tmp_path)
            assert cfg.ide_type == ide_type


# ---------------------------------------------------------------------------
# Tests: _match_ide_type  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestMatchIdeType:
    """Tests for the _match_ide_type helper. @trace FR-IDE-001"""

    @pytest.mark.parametrize(
        ("dir_name", "expected"),
        [
            ("PyCharm2024.2", "pycharm"),
            ("PyCharmCE2023.1", "pycharm"),
            ("IntelliJIdea2024.1", "intellij"),
            ("IdeaIC2024.1", "intellij"),
            ("GoLand2023.3", "goland"),
            ("CLion2023.2", "clion"),
            ("WebStorm2024.1", "webstorm"),
            ("Rider2024.1", "rider"),
            ("DataGrip2024.1", "datagrip"),
            ("RubyMine2023.3", "rubymine"),
            ("PhpStorm2024.1", "phpstorm"),
            ("Fleet1.31", "fleet"),
        ],
    )
    def test_known_prefixes(self, dir_name: str, expected: str) -> None:
        """Known JetBrains directory names map to the correct IDE type. @trace FR-IDE-001"""
        assert _match_ide_type(dir_name) == expected

    def test_unknown_prefix_returns_none(self) -> None:
        """Unknown directory name returns None. @trace FR-IDE-001"""
        assert _match_ide_type("VisualStudio2022") is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None. @trace FR-IDE-001"""
        assert _match_ide_type("") is None


# ---------------------------------------------------------------------------
# Tests: detect_installed_ides  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestDetectInstalledIdes:
    """Tests for JetBrainsIntegration.detect_installed_ides. @trace FR-IDE-001"""

    def test_finds_correct_ides_from_fake_base(self, tmp_path: Path, fake_jb_base: Path) -> None:
        """Detects all IDE dirs in fake base, ignoring unknown dirs. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[fake_jb_base],
        ):
            configs = integration.detect_installed_ides()

        ide_types = {c.ide_type for c in configs}
        assert "pycharm" in ide_types
        assert "intellij" in ide_types
        assert "goland" in ide_types
        assert "webstorm" in ide_types
        # NotAnIDE directory must NOT be detected
        assert len(configs) == 4

    def test_returns_empty_when_no_base_dir(self, tmp_path: Path) -> None:
        """Returns empty list when no JetBrains base dirs exist. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[],
        ):
            configs = integration.detect_installed_ides()
        assert configs == []

    def test_config_dir_path_matches_actual_dir(self, fake_jb_base: Path) -> None:
        """Detected config_dir is the actual filesystem directory. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[fake_jb_base],
        ):
            configs = integration.detect_installed_ides()

        pycharm = next(c for c in configs if c.ide_type == "pycharm")
        assert pycharm.config_dir.exists()
        assert pycharm.config_dir.name.startswith("PyCharm")

    def test_mcp_server_url_propagated(self, fake_jb_base: Path) -> None:
        """Custom mcp_server_url is propagated to all detected configs. @trace FR-IDE-001"""
        url = "http://localhost:1234/mcp"
        integration = JetBrainsIntegration(mcp_server_url=url)
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[fake_jb_base],
        ):
            configs = integration.detect_installed_ides()

        assert all(c.mcp_server_url == url for c in configs)

    def test_permission_error_skips_base_dir(self, tmp_path: Path) -> None:
        """PermissionError on a base directory is handled gracefully. @trace FR-IDE-001"""
        bad_base = tmp_path / "JetBrains"
        bad_base.mkdir()
        integration = JetBrainsIntegration()

        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[bad_base],
        ), mock.patch.object(
            Path,
            "iterdir",
            side_effect=PermissionError("access denied"),
        ):
            configs = integration.detect_installed_ides()

        assert configs == []


# ---------------------------------------------------------------------------
# Tests: write_mcp_config  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestWriteMcpConfig:
    """Tests for JetBrainsIntegration.write_mcp_config. @trace FR-IDE-001"""

    def test_creates_valid_json(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """write_mcp_config produces parseable JSON. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="pycharm", config_dir=tmp_path / "PyCharm2024.2")
        path = integration.write_mcp_config(cfg)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_written_config_contains_thegent_entry(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Written JSON contains mcpServers.thegent with the correct url. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="intellij", config_dir=tmp_path / "IntelliJIdea2024.1")
        integration.write_mcp_config(cfg)
        data = json.loads(cfg.mcp_config_path.read_text())
        assert "mcpServers" in data
        assert "thegent" in data["mcpServers"]
        assert data["mcpServers"]["thegent"]["url"] == DEFAULT_MCP_SERVER_URL

    def test_creates_config_dir_if_missing(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """write_mcp_config creates the config_dir if it does not exist. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="goland", config_dir=tmp_path / "new_dir" / "GoLand2024")
        path = integration.write_mcp_config(cfg)
        assert path.exists()

    def test_merges_existing_mcp_servers(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Existing mcpServers entries are preserved when writing. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="webstorm", config_dir=tmp_path / "WebStorm2024.1")
        cfg.config_dir.mkdir(parents=True)
        existing = {"mcpServers": {"other-tool": {"url": "http://other.example/mcp"}}}
        cfg.mcp_config_path.write_text(json.dumps(existing).decode())

        integration.write_mcp_config(cfg)
        data = json.loads(cfg.mcp_config_path.read_text())
        assert "other-tool" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]

    def test_overwrites_stale_thegent_entry(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Existing thegent entry is replaced with the current URL. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="clion", config_dir=tmp_path / "CLion2024.1")
        cfg.config_dir.mkdir()
        old = {"mcpServers": {"thegent": {"url": "http://old-url/mcp"}}}
        cfg.mcp_config_path.write_text(json.dumps(old).decode())

        new_url = "http://localhost:3847/mcp"
        integration2 = JetBrainsIntegration(mcp_server_url=new_url)
        cfg2 = JetBrainsConfig(ide_type="clion", config_dir=cfg.config_dir, mcp_server_url=new_url)
        integration2.write_mcp_config(cfg2)
        data = json.loads(cfg.mcp_config_path.read_text())
        assert data["mcpServers"]["thegent"]["url"] == new_url

    def test_includes_env_when_project_root_set(self, tmp_path: Path) -> None:
        """When serena_project_root is set, env block appears in thegent entry. @trace FR-IDE-001"""
        root = "/Users/dev/myproject"
        integration = JetBrainsIntegration(serena_project_root=root)
        cfg = JetBrainsConfig(
            ide_type="pycharm",
            config_dir=tmp_path / "PyCharm2024.2",
            serena_project_root=root,
        )
        integration.write_mcp_config(cfg)
        data = json.loads(cfg.mcp_config_path.read_text())
        entry = data["mcpServers"]["thegent"]
        assert "env" in entry
        assert entry["env"]["SERENA_PROJECT_ROOT"] == root

    def test_no_env_when_project_root_empty(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """No env block appears when serena_project_root is empty. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="rider", config_dir=tmp_path / "Rider2024.1")
        integration.write_mcp_config(cfg)
        data = json.loads(cfg.mcp_config_path.read_text())
        assert "env" not in data["mcpServers"]["thegent"]

    def test_returns_path_to_mcp_json(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """write_mcp_config returns the Path to the written mcp.json. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="datagrip", config_dir=tmp_path / "DataGrip2024.1")
        result = integration.write_mcp_config(cfg)
        assert result == cfg.mcp_config_path
        assert result.name == "mcp.json"


# ---------------------------------------------------------------------------
# Tests: read_existing_config  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestReadExistingConfig:
    """Tests for JetBrainsIntegration.read_existing_config. @trace FR-IDE-001"""

    def test_returns_none_when_file_missing(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns None when mcp.json does not exist. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="pycharm", config_dir=tmp_path / "PyCharm")
        assert integration.read_existing_config(cfg) is None

    def test_parses_valid_json(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Parses a valid mcp.json and returns the dict. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="intellij", config_dir=tmp_path / "IntelliJ")
        cfg.config_dir.mkdir()
        payload = {"mcpServers": {"thegent": {"url": "http://localhost:3847/mcp"}}}
        cfg.mcp_config_path.write_text(json.dumps(payload).decode())

        result = integration.read_existing_config(cfg)
        assert result == payload

    def test_returns_none_on_invalid_json(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns None when mcp.json contains invalid JSON. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="goland", config_dir=tmp_path / "GoLand")
        cfg.config_dir.mkdir()
        cfg.mcp_config_path.write_text("{ this is not valid json }")

        assert integration.read_existing_config(cfg) is None

    def test_returns_none_when_json_is_not_object(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns None when mcp.json root is not a JSON object. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="webstorm", config_dir=tmp_path / "WebStorm")
        cfg.config_dir.mkdir()
        cfg.mcp_config_path.write_text(json.dumps([1, 2, 3]).decode())

        assert integration.read_existing_config(cfg) is None

    def test_preserves_all_top_level_keys(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """All top-level keys in mcp.json are returned, not just mcpServers. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="clion", config_dir=tmp_path / "CLion")
        cfg.config_dir.mkdir()
        payload = {
            "mcpServers": {"thegent": {"url": "http://localhost:3847/mcp"}},
            "extra": "value",
        }
        cfg.mcp_config_path.write_text(json.dumps(payload).decode())

        result = integration.read_existing_config(cfg)
        assert result is not None
        assert result.get("extra") == "value"


# ---------------------------------------------------------------------------
# Tests: is_mcp_plugin_installed  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestIsMcpPluginInstalled:
    """Tests for JetBrainsIntegration.is_mcp_plugin_installed. @trace FR-IDE-001"""

    def test_false_when_no_config_file(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns False when mcp.json does not exist. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="pycharm", config_dir=tmp_path / "PyCharm")
        assert integration.is_mcp_plugin_installed(cfg) is False

    def test_true_when_thegent_key_present(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns True when thegent entry exists in mcpServers. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="intellij", config_dir=tmp_path / "IntelliJ")
        cfg.config_dir.mkdir()
        payload = {"mcpServers": {"thegent": {"url": "http://localhost:3847/mcp"}}}
        cfg.mcp_config_path.write_text(json.dumps(payload).decode())

        assert integration.is_mcp_plugin_installed(cfg) is True

    def test_false_when_thegent_key_absent(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns False when mcpServers exists but lacks thegent key. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="goland", config_dir=tmp_path / "GoLand")
        cfg.config_dir.mkdir()
        payload = {"mcpServers": {"other-server": {"url": "http://other/mcp"}}}
        cfg.mcp_config_path.write_text(json.dumps(payload).decode())

        assert integration.is_mcp_plugin_installed(cfg) is False

    def test_false_when_config_is_invalid_json(self, integration: JetBrainsIntegration, tmp_path: Path) -> None:
        """Returns False when mcp.json is malformed. @trace FR-IDE-001"""
        cfg = JetBrainsConfig(ide_type="webstorm", config_dir=tmp_path / "WebStorm")
        cfg.config_dir.mkdir()
        cfg.mcp_config_path.write_text("not json at all")

        assert integration.is_mcp_plugin_installed(cfg) is False


# ---------------------------------------------------------------------------
# Tests: setup_all  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestSetupAll:
    """Tests for JetBrainsIntegration.setup_all. @trace FR-IDE-001"""

    def test_returns_result_for_each_detected_ide(self, fake_jb_base: Path) -> None:
        """setup_all returns one result dict per detected IDE. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[fake_jb_base],
        ):
            results = integration.setup_all()

        assert len(results) == 4  # PyCharm, IntelliJ, GoLand, WebStorm
        for r in results:
            assert "ide_type" in r
            assert "success" in r

    def test_success_true_when_write_succeeds(self, fake_jb_base: Path) -> None:
        """Each result has success=True when the config is written. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[fake_jb_base],
        ):
            results = integration.setup_all()

        assert all(r["success"] for r in results)

    def test_returns_empty_when_no_ides(self, tmp_path: Path) -> None:
        """setup_all returns an empty list when no IDEs are found. @trace FR-IDE-001"""
        integration = JetBrainsIntegration()
        with mock.patch(
            "thegent.integrations.jetbrains._jetbrains_base_dirs",
            return_value=[],
        ):
            results = integration.setup_all()

        assert results == []


# ---------------------------------------------------------------------------
# Tests: _jetbrains_base_dirs  @trace FR-IDE-001
# ---------------------------------------------------------------------------


class TestJetBrainsBaseDirs:
    """Tests for _jetbrains_base_dirs platform detection. @trace FR-IDE-001"""

    def test_returns_list_of_paths(self) -> None:
        """_jetbrains_base_dirs returns a list of Path instances. @trace FR-IDE-001"""
        dirs = _jetbrains_base_dirs()
        assert isinstance(dirs, list)
        for d in dirs:
            assert isinstance(d, Path)

    def test_all_returned_dirs_exist(self) -> None:
        """All returned paths exist on disk. @trace FR-IDE-001"""
        dirs = _jetbrains_base_dirs()
        for d in dirs:
            assert d.exists(), f"Expected existing dir, got {d}"

    def test_macos_candidate_includes_library_support(self, tmp_path: Path) -> None:
        """On macOS the ~/Library/Application Support/JetBrains path is a candidate.

        @trace FR-IDE-001
        """
        fake_support = tmp_path / "Library" / "Application Support" / "JetBrains"
        fake_support.mkdir(parents=True)

        with (
            mock.patch("platform.system", return_value="Darwin"),
            mock.patch("pathlib.Path.home", return_value=tmp_path),
        ):
            dirs = _jetbrains_base_dirs()

        assert fake_support in dirs
