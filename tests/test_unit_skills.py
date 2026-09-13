"""Tests for skills auto-discovery and MCP integration."""

from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest


class TestSkillDiscovery:
    """Tests for skill discovery functionality."""

    def test_discover_skills_finds_existing_skills(self):
        """Test that discover_skills finds skills in the skills directory."""
        from thegent.skills.discovery import discover_skills

        skills = discover_skills()

        # Should find at least the thegent-skills and sitback-agent
        assert len(skills) >= 2

        skill_names = [s.name for s in skills]
        assert "thegent-skills" in skill_names
        assert "sitback-agent" in skill_names

    def test_discover_skills_returns_skill_info(self):
        """Test that discover_skills returns SkillInfo with expected fields."""
        from thegent.skills.discovery import discover_skills

        skills = discover_skills()

        for skill in skills:
            assert skill.name
            assert skill.description
            assert skill.version
            assert skill.entrypoint
            assert skill.path.exists()
            assert skill.skill_md_path.exists()
            assert skill.skill_json_path.exists()

    def test_load_skill_thegent_skills(self):
        """Test loading the thegent-skills skill."""
        from thegent.skills.discovery import load_skill

        skill = load_skill("thegent-skills")

        assert skill is not None
        assert skill["name"] == "thegent-skills"
        assert "description" in skill
        assert "version" in skill
        assert "entrypoint" in skill
        assert "content" in skill
        assert len(skill["content"]) > 0

    def test_load_skill_sitback_agent(self):
        """Test loading the sitback-agent skill."""
        from thegent.skills.discovery import load_skill

        skill = load_skill("sitback-agent")

        assert skill is not None
        assert skill["name"] == "sitback-agent"
        assert "description" in skill

    def test_load_skill_nonexistent(self):
        """Test loading a non-existent skill returns None."""
        from thegent.skills.discovery import load_skill

        skill = load_skill("nonexistent-skill")

        assert skill is None

    def test_validate_skill_valid(self):
        """Test validating a valid skill."""
        from thegent.skills.discovery import discover_skills, validate_skill

        skills = discover_skills()
        assert len(skills) > 0

        result = validate_skill(skills[0].path)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_skill_missing_json(self):
        """Test validating a skill without skill.json."""
        import tempfile
        from pathlib import Path

        from thegent.skills.discovery import validate_skill

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "test-skill"
            skill_path.mkdir()

            # Create SKILL.md but no skill.json
            (skill_path / "SKILL.md").write_text("# Test")

            result = validate_skill(skill_path)

            assert result["valid"] is True
            assert any("Missing skill.json" in warning for warning in result["warnings"])

    def test_validate_skill_invalid_json(self):
        """Test validating a skill with invalid JSON."""
        import tempfile
        from pathlib import Path

        from thegent.skills.discovery import validate_skill

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "test-skill"
            skill_path.mkdir()

            # Create invalid skill.json
            (skill_path / "skill.json").write_text("{ invalid json }")
            (skill_path / "SKILL.md").write_text("# Test")

            result = validate_skill(skill_path)

            assert result["valid"] is False
            assert len(result["errors"]) > 0

    def test_discover_skills_supports_skill_md_only(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """SKILL.md-only skill directories are discoverable for spec compatibility."""
        from thegent.skills.discovery import discover_skills

        skill_dir = tmp_path / "skills" / "md-only-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# MD only skill", encoding="utf-8")

        monkeypatch.setattr(
            "thegent.skills.discovery._get_all_skills_dirs",
            lambda: [tmp_path / "skills"],
        )

        skills = discover_skills()
        assert len(skills) == 1
        assert skills[0].name == "md-only-skill"
        assert skills[0].skill_md_path.name == "SKILL.md"

    def test_load_skill_supports_skill_md_only(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """load_skill() returns default metadata for SKILL.md-only skills."""
        from thegent.skills.discovery import load_skill

        skill_dir = tmp_path / "skills" / "md-only-load"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Instructions", encoding="utf-8")

        monkeypatch.setattr(
            "thegent.skills.discovery._get_all_skills_dirs",
            lambda: [tmp_path / "skills"],
        )

        skill = load_skill("md-only-load")
        assert skill is not None
        assert skill["name"] == "md-only-load"
        assert skill["version"] == "1.0.0"
        assert skill["content"] == "# Instructions"

    def test_discover_skills_sorts_results_deterministically(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """discover_skills should be deterministic regardless of filesystem iteration order."""
        from thegent.skills.discovery import discover_skills

        skills_root = tmp_path / "skills"
        for name in ("zeta", "alpha"):
            skill_dir = skills_root / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}", encoding="utf-8")

        monkeypatch.setattr("thegent.skills.discovery._get_all_skills_dirs", lambda: [skills_root])
        skills = discover_skills()
        assert [skill.name for skill in skills] == ["alpha", "zeta"]

    def test_discover_skills_skips_empty_manifest_name(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Manifest entries with empty names are rejected."""
        from thegent.skills.discovery import discover_skills

        skill_dir = tmp_path / "skills" / "bad-name"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Has content", encoding="utf-8")
        (skill_dir / "skill.json").write_text(
            json.dumps(
                {
                    "name": "   ",
                    "description": "bad",
                    "version": "1.0.0",
                    "entrypoint": "x",
                }
            ).decode(),
            encoding="utf-8",
        )

        monkeypatch.setattr(
            "thegent.skills.discovery._get_all_skills_dirs",
            lambda: [tmp_path / "skills"],
        )
        assert discover_skills() == []

    def test_load_skill_rejects_empty_name(self):
        """Whitespace-only skill names are invalid."""
        from thegent.skills.discovery import load_skill

        assert load_skill("   ") is None


class TestMCPIntegration:
    """Tests for MCP integration functions."""

    def test_list_skills_returns_json(self):
        """Test that list_skills returns valid JSON."""
        from thegent.skills.mcp_integration import list_skills

        result = list_skills()

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 2

        # Each skill should have expected fields
        for skill in data:
            assert "name" in skill
            assert "description" in skill
            assert "version" in skill
            assert "entrypoint" in skill
            assert "path" in skill

    def test_get_skill_returns_json(self):
        """Test that get_skill returns valid JSON."""
        from thegent.skills.mcp_integration import get_skill

        result = get_skill("thegent-skills")

        data = json.loads(result)
        assert data["name"] == "thegent-skills"
        assert "content" in data
        assert len(data["content"]) > 0

    def test_get_skill_not_found(self):
        """Test that get_skill returns error for non-existent skill."""
        from thegent.skills.mcp_integration import get_skill

        result = get_skill("nonexistent-skill")

        data = json.loads(result)
        assert "error" in data
        assert "available_skills" in data

    def test_run_skill_returns_result(self):
        """Test that run_skill returns execution result."""
        from thegent.skills.mcp_integration import run_skill

        result = run_skill("thegent-skills")

        data = json.loads(result)
        assert data["skill"] == "thegent-skills"
        assert data["status"] == "ready"
        assert "entrypoint" in data
        assert "message" in data

    def test_run_skill_not_found(self):
        """Test that run_skill returns error for non-existent skill."""
        from thegent.skills.mcp_integration import run_skill

        result = run_skill("nonexistent-skill")

        data = json.loads(result)
        assert "error" in data


class TestCLISkillsCommands:
    """Tests for CLI skills commands."""

    def test_skills_list_command(self):
        """Test the skills list CLI command."""

        from thegent.cli.apps.skills import skills_list

        with patch("thegent.cli.apps.skills.discover_skills") as mock_discover:
            from thegent.skills.discovery import SkillInfo

            mock_discover.return_value = [
                SkillInfo(
                    name="test-skill",
                    description="A test skill",
                    version="1.0.0",
                    entrypoint="thegent",
                    path=Path("/tmp/test"),
                    skill_md_path=Path("/tmp/test/SKILL.md"),
                    skill_json_path=Path("/tmp/test/skill.json"),
                )
            ]

            # This should work without errors
            skills_list()

    def test_skills_show_command_not_found(self):
        """Test the skills show CLI command for non-existent skill."""

        import pytest

        from thegent.cli.apps.skills import skills_show

        with patch("thegent.cli.apps.skills.load_skill", return_value=None):
            with pytest.raises(SystemExit):
                skills_show("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
