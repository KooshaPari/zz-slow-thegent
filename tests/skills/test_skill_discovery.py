"""Tests for SKILL.md spec-compatible skill discovery system.

# @trace FR-SKL-101
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.skills.discovery import SkillActivator, SkillDiscovery, SkillManifest

# ---------------------------------------------------------------------------
# SkillManifest model tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SKL-101")
class TestSkillManifest:
    def test_skill_manifest_fields(self) -> None:
        m = SkillManifest(
            name="test",
            description="A test skill",
            instructions="Do things",
            source_path="/tmp/test",
            tags=["a", "b"],
        )
        assert m.name == "test"
        assert m.description == "A test skill"
        assert m.instructions == "Do things"
        assert m.source_path == "/tmp/test"
        assert m.tags == ["a", "b"]

    def test_skill_manifest_is_frozen(self) -> None:
        m = SkillManifest(name="frozen")
        with pytest.raises(Exception):  # pydantic ValidationError for frozen
            m.name = "changed"

    def test_skill_manifest_default_tags_empty(self) -> None:
        m = SkillManifest(name="minimal")
        assert m.tags == []
        assert m.description == ""
        assert m.instructions == ""
        assert m.source_path == ""


# ---------------------------------------------------------------------------
# SkillDiscovery tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SKL-101")
class TestSkillDiscovery:
    def test_discover_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        sd = SkillDiscovery(search_dirs=[skills_dir])
        assert sd.discover() == []

    def test_discover_skill_md_parses_name_from_h1(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text(
            "# My Great Skill\n\nSome instructions here.",
            encoding="utf-8",
        )
        sd = SkillDiscovery(search_dirs=[skills_dir])
        results = sd.discover()
        assert len(results) == 1
        assert results[0].name == "My Great Skill"

    def test_discover_skill_md_parses_instructions(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text(
            "# Skill Name\n\nDo X then Y.",
            encoding="utf-8",
        )
        sd = SkillDiscovery(search_dirs=[skills_dir])
        results = sd.discover()
        assert len(results) == 1
        assert "Do X then Y." in results[0].instructions

    def test_discover_skill_json_parses_all_fields(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill.json").write_text(
            json.dumps(
                {
                    "name": "json-skill",
                    "description": "A JSON skill",
                    "instructions": "Follow these steps",
                    "tags": ["tag1", "tag2"],
                }
            ),
            encoding="utf-8",
        )
        sd = SkillDiscovery(search_dirs=[skills_dir])
        results = sd.discover()
        assert len(results) == 1
        assert results[0].name == "json-skill"
        assert results[0].description == "A JSON skill"
        assert results[0].instructions == "Follow these steps"
        assert results[0].tags == ["tag1", "tag2"]

    def test_discover_multiple_skills(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        (dir_a / "SKILL.md").write_text("# Alpha\n\nAlpha instructions.", encoding="utf-8")

        dir_b = tmp_path / "b"
        dir_b.mkdir()
        (dir_b / "skill.json").write_text(
            json.dumps({"name": "Beta", "instructions": "Beta instructions"}).decode(),
            encoding="utf-8",
        )

        sd = SkillDiscovery(search_dirs=[dir_a, dir_b])
        results = sd.discover()
        names = {r.name for r in results}
        assert "Alpha" in names
        assert "Beta" in names
        assert len(results) == 2

    def test_find_returns_skill_by_name(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text("# Target\n\nTarget instructions.", encoding="utf-8")

        sd = SkillDiscovery(search_dirs=[skills_dir])
        result = sd.find("Target")
        assert result.name == "Target"
        assert "Target instructions." in result.instructions

    def test_find_unknown_name_raises_key_error(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        sd = SkillDiscovery(search_dirs=[skills_dir])
        with pytest.raises(KeyError, match="nonexistent"):
            sd.find("nonexistent")

    def test_discover_nonexistent_dir_returns_empty(self) -> None:
        sd = SkillDiscovery(search_dirs=[Path("/tmp/does-not-exist-xyz-123456")])
        assert sd.discover() == []

    def test_discover_skips_unrecognized_files(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "README.txt").write_text("not a skill", encoding="utf-8")
        (skills_dir / "notes.py").write_text("# code", encoding="utf-8")

        sd = SkillDiscovery(search_dirs=[skills_dir])
        assert sd.discover() == []


# ---------------------------------------------------------------------------
# SkillActivator tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-SKL-101")
class TestSkillActivator:
    def test_activate_appends_instructions(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text(
            "# MySkill\n\nDo the thing.",
            encoding="utf-8",
        )
        sd = SkillDiscovery(search_dirs=[skills_dir])
        activator = SkillActivator(discovery=sd)
        result = activator.activate("MySkill", "You are a helpful assistant.")
        assert "You are a helpful assistant." in result
        assert "Do the thing." in result

    def test_activate_unknown_skill_raises(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        sd = SkillDiscovery(search_dirs=[skills_dir])
        activator = SkillActivator(discovery=sd)
        with pytest.raises(KeyError, match="ghost"):
            activator.activate("ghost", "base prompt")

    def test_activate_many_appends_all(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        (dir_a / "SKILL.md").write_text("# SkillA\n\nInstructions A.", encoding="utf-8")

        dir_b = tmp_path / "b"
        dir_b.mkdir()
        (dir_b / "SKILL.md").write_text("# SkillB\n\nInstructions B.", encoding="utf-8")

        sd = SkillDiscovery(search_dirs=[dir_a, dir_b])
        activator = SkillActivator(discovery=sd)
        result = activator.activate_many(["SkillA", "SkillB"], "base")
        assert "Instructions A." in result
        assert "Instructions B." in result
        assert "base" in result

    def test_activate_preserves_original_prompt(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "SKILL.md").write_text("# X\n\nExtra.", encoding="utf-8")
        sd = SkillDiscovery(search_dirs=[skills_dir])
        activator = SkillActivator(discovery=sd)
        original = "You are the original prompt."
        result = activator.activate("X", original)
        assert result.startswith(original)

    def test_activate_empty_instructions_appends_nothing_extra(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill.json").write_text(
            json.dumps({"name": "empty", "instructions": ""}).decode(),
            encoding="utf-8",
        )
        sd = SkillDiscovery(search_dirs=[skills_dir])
        activator = SkillActivator(discovery=sd)
        original = "base prompt"
        result = activator.activate("empty", original)
        assert result == original
