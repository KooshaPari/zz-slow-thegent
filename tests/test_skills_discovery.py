"""WL-101: Skills Discovery + SKILL.md spec compatibility tests.

Covers:
- SkillManifest model (frozen pydantic)
- SkillDiscovery scan and find (SKILL.md, skill.json, skill.yaml)
- SkillActivator inject into system prompt
- AgentRunner.activate_skill integration (raises KeyError on missing)
- AgentRunner.activated_skills per-instance isolation
- AgentRunner.get_skill_prompt_suffix formatting
- MCP tool impls (thegent_list_skills, thegent_activate_skill)
- CLI skill list smoke

# @trace WL-101
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import patch

import orjson as json
import pytest

from thegent.agents.base import AgentRunner
from thegent.skills.discovery import (
    SkillActivator,
    SkillDiscovery,
    SkillManifest,
)

# tools_skills lives in a sibling directory named "server/" which has the same
# name as the module file "server.py", so we load it directly via importlib.
_TOOLS_SKILLS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "thegent"
    / "mcp"
    / "server"
    / "tools_skills.py"
)
_spec = importlib.util.spec_from_file_location(
    "_tools_skills_wl101", _TOOLS_SKILLS_PATH
)
assert _spec is not None and _spec.loader is not None
_tools_skills_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools_skills_mod)

DiscoverySkillBackend = _tools_skills_mod.DiscoverySkillBackend
thegent_activate_skill_impl = _tools_skills_mod.thegent_activate_skill_impl
thegent_list_skills_impl = _tools_skills_mod.thegent_list_skills_impl


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _write_skill_md(directory: Path, content: str) -> Path:
    path = directory / "SKILL.md"
    path.write_text(content, encoding="utf-8")
    return path


def _write_skill_json(directory: Path, data: dict[str, Any]) -> Path:
    path = directory / "skill.json"
    path.write_text(json.dumps(data).decode(), encoding="utf-8")
    return path


def _write_skill_yaml(directory: Path, data: str) -> Path:
    path = directory / "skill.yaml"
    path.write_text(data, encoding="utf-8")
    return path


def _error_result(
    error: str,
    remediation: str,
    exit_code: int = 1,
    extra: dict[str, Any] | None = None,
) -> Any:
    from fastmcp.tools.tool import ToolResult

    payload: dict[str, Any] = {
        "error": error,
        "remediation": remediation,
        "exit_code": exit_code,
    }
    if extra:
        payload.update(extra)
    return ToolResult(
        content=json.dumps(payload).decode(),
        structured_content=payload,
        meta={"execution_time_ms": 0},
    )


# ---------------------------------------------------------------------------
# 1. SkillManifest tests
# ---------------------------------------------------------------------------


class TestSkillManifest:
    """# @trace WL-101"""

    def test_manifest_name_required(self) -> None:
        """SkillManifest requires at minimum a name field."""
        m = SkillManifest(name="my-skill")
        assert m.name == "my-skill"

    def test_manifest_all_fields(self) -> None:
        """SkillManifest stores all provided fields correctly."""
        m = SkillManifest(
            name="full",
            description="A full skill",
            instructions="Step 1. Step 2.",
            source_path="/tmp/full/SKILL.md",
            tags=["alpha", "beta"],
        )
        assert m.description == "A full skill"
        assert m.instructions == "Step 1. Step 2."
        assert m.source_path == "/tmp/full/SKILL.md"
        assert m.tags == ["alpha", "beta"]

    def test_manifest_defaults_are_empty(self) -> None:
        """SkillManifest defaults: empty description, instructions, source_path, tags."""
        m = SkillManifest(name="minimal")
        assert m.description == ""
        assert m.instructions == ""
        assert m.source_path == ""
        assert m.tags == []

    def test_manifest_is_frozen(self) -> None:
        """SkillManifest is immutable; mutation raises an error."""
        m = SkillManifest(name="frozen")
        with pytest.raises(Exception):
            m.name = "changed"  # type: ignore[misc]

    def test_manifest_tags_not_shared_between_instances(self) -> None:
        """Each SkillManifest gets its own default tags list."""
        m1 = SkillManifest(name="a")
        m2 = SkillManifest(name="b")
        assert m1.tags is not m2.tags


# ---------------------------------------------------------------------------
# 2. SkillDiscovery — SKILL.md parsing
# ---------------------------------------------------------------------------


class TestSkillDiscoverySkillMd:
    """# @trace WL-101"""

    def test_discover_returns_empty_when_dir_is_empty(self, tmp_path: Path) -> None:
        sd = SkillDiscovery(search_dirs=[tmp_path])
        assert sd.discover() == []

    def test_discover_skill_md_parses_h1_as_name(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# My Great Skill\n\nInstructions here.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert len(results) == 1
        assert results[0].name == "My Great Skill"

    def test_discover_skill_md_instructions_exclude_h1(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# SkillName\n\nDo X then Y.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert "Do X then Y." in results[0].instructions
        assert "# SkillName" not in results[0].instructions

    def test_discover_skill_md_no_h1_uses_dir_name(self, tmp_path: Path) -> None:
        """When SKILL.md has no H1, the directory name is used as skill name."""
        subdir = tmp_path / "myskilldir"
        subdir.mkdir()
        _write_skill_md(subdir, "Just instructions, no heading.")
        sd = SkillDiscovery(search_dirs=[subdir])
        results = sd.discover()
        # Without H1 the directory name is used (or the parent dirs name)
        assert len(results) == 1
        assert results[0].instructions == "Just instructions, no heading."

    def test_discover_skill_md_source_path_set(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# Named\n\nContent.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert "SKILL.md" in results[0].source_path

    def test_discover_nonexistent_dir_returns_empty(self) -> None:
        sd = SkillDiscovery(search_dirs=[Path("/tmp/no-such-dir-xyz-wl101")])
        assert sd.discover() == []

    def test_discover_ignores_unrecognized_files(self, tmp_path: Path) -> None:
        (tmp_path / "README.txt").write_text("not a skill", encoding="utf-8")
        (tmp_path / "notes.py").write_text("# code", encoding="utf-8")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        assert sd.discover() == []


# ---------------------------------------------------------------------------
# 3. SkillDiscovery — skill.json parsing
# ---------------------------------------------------------------------------


class TestSkillDiscoverySkillJson:
    """# @trace WL-101"""

    def test_discover_skill_json_parses_name(self, tmp_path: Path) -> None:
        _write_skill_json(tmp_path, {"name": "json-skill", "instructions": "Do it."})
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert results[0].name == "json-skill"

    def test_discover_skill_json_all_fields(self, tmp_path: Path) -> None:
        _write_skill_json(
            tmp_path,
            {
                "name": "full-json",
                "description": "Full JSON skill",
                "instructions": "Full instructions",
                "tags": ["x", "y"],
            },
        )
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert results[0].description == "Full JSON skill"
        assert results[0].instructions == "Full instructions"
        assert results[0].tags == ["x", "y"]

    def test_discover_skill_json_missing_optional_fields_use_defaults(
        self, tmp_path: Path
    ) -> None:
        _write_skill_json(tmp_path, {"name": "minimal-json"})
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert results[0].name == "minimal-json"
        assert results[0].description == ""
        assert results[0].instructions == ""
        assert results[0].tags == []


# ---------------------------------------------------------------------------
# 4. SkillDiscovery — skill.yaml parsing
# ---------------------------------------------------------------------------


class TestSkillDiscoverySkillYaml:
    """# @trace WL-101"""

    def test_discover_skill_yaml_parses_name(self, tmp_path: Path) -> None:
        _write_skill_yaml(
            tmp_path, "name: yaml-skill\ninstructions: YAML instructions\n"
        )
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert results[0].name == "yaml-skill"
        assert results[0].instructions == "YAML instructions"

    def test_discover_skill_yaml_tags(self, tmp_path: Path) -> None:
        _write_skill_yaml(
            tmp_path,
            "name: tagged\ndescription: desc\ninstructions: instr\ntags:\n  - t1\n  - t2\n",
        )
        sd = SkillDiscovery(search_dirs=[tmp_path])
        results = sd.discover()
        assert results[0].tags == ["t1", "t2"]


# ---------------------------------------------------------------------------
# 5. SkillDiscovery — multi-dir, find
# ---------------------------------------------------------------------------


class TestSkillDiscoveryFind:
    """# @trace WL-101"""

    def test_discover_multiple_dirs_collects_all_skills(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        _write_skill_md(dir_a, "# Alpha\n\nAlpha instructions.")

        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _write_skill_json(dir_b, {"name": "Beta", "instructions": "Beta instructions"})

        sd = SkillDiscovery(search_dirs=[dir_a, dir_b])
        names = {r.name for r in sd.discover()}
        assert "Alpha" in names
        assert "Beta" in names
        assert len(names) == 2

    def test_find_returns_correct_manifest(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# Target\n\nTarget instructions.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        result = sd.find("Target")
        assert result.name == "Target"
        assert "Target instructions." in result.instructions

    def test_find_raises_key_error_for_missing_skill(self, tmp_path: Path) -> None:
        sd = SkillDiscovery(search_dirs=[tmp_path])
        with pytest.raises(KeyError, match="ghost"):
            sd.find("ghost")

    def test_find_raises_key_error_message_contains_name(self, tmp_path: Path) -> None:
        sd = SkillDiscovery(search_dirs=[tmp_path])
        with pytest.raises(KeyError) as exc_info:
            sd.find("my-missing-skill")
        assert "my-missing-skill" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 6. SkillActivator tests
# ---------------------------------------------------------------------------


class TestSkillActivator:
    """# @trace WL-101"""

    def test_activate_appends_instructions_to_prompt(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# Greeter\n\nAlways greet the user warmly.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        activator = SkillActivator(discovery=sd)
        result = activator.activate("Greeter", "You are an assistant.")
        assert "You are an assistant." in result
        assert "Always greet the user warmly." in result

    def test_activate_unknown_skill_raises_key_error(self, tmp_path: Path) -> None:
        sd = SkillDiscovery(search_dirs=[tmp_path])
        activator = SkillActivator(discovery=sd)
        with pytest.raises(KeyError, match="no-such"):
            activator.activate("no-such", "base prompt")

    def test_activate_preserves_prompt_as_prefix(self, tmp_path: Path) -> None:
        _write_skill_md(tmp_path, "# X\n\nExtra step.")
        sd = SkillDiscovery(search_dirs=[tmp_path])
        activator = SkillActivator(discovery=sd)
        original = "You are the original."
        result = activator.activate("X", original)
        assert result.startswith(original)

    def test_activate_empty_instructions_returns_prompt_unchanged(
        self, tmp_path: Path
    ) -> None:
        _write_skill_json(tmp_path, {"name": "empty-instr", "instructions": ""})
        sd = SkillDiscovery(search_dirs=[tmp_path])
        activator = SkillActivator(discovery=sd)
        original = "base prompt"
        result = activator.activate("empty-instr", original)
        assert result == original

    def test_activate_many_appends_all_skills(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        _write_skill_md(dir_a, "# SkillA\n\nInstructions A.")

        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _write_skill_md(dir_b, "# SkillB\n\nInstructions B.")

        sd = SkillDiscovery(search_dirs=[dir_a, dir_b])
        activator = SkillActivator(discovery=sd)
        result = activator.activate_many(["SkillA", "SkillB"], "base")
        assert "Instructions A." in result
        assert "Instructions B." in result
        assert "base" in result

    def test_activate_many_empty_list_returns_prompt_unchanged(
        self, tmp_path: Path
    ) -> None:
        sd = SkillDiscovery(search_dirs=[tmp_path])
        activator = SkillActivator(discovery=sd)
        original = "stay the same"
        assert activator.activate_many([], original) == original


# ---------------------------------------------------------------------------
# 7. AgentRunner.activate_skill integration
# ---------------------------------------------------------------------------


class TestAgentRunnerActivateSkill:
    """# @trace WL-101"""

    def test_activated_skills_starts_empty(self) -> None:
        runner = AgentRunner()
        assert runner.activated_skills == {}

    def test_activated_skills_is_per_instance(self) -> None:
        r1 = AgentRunner()
        r2 = AgentRunner()
        r1.activated_skills["key"] = "val"
        assert "key" not in r2.activated_skills

    def test_activate_skill_raises_key_error_for_missing(self, tmp_path: Path) -> None:
        runner = AgentRunner()
        with patch.object(
            __import__(
                "thegent.skills.discovery", fromlist=["SkillDiscovery"]
            ).SkillDiscovery,
            "find",
            side_effect=KeyError("no-skill"),
        ):
            with pytest.raises(KeyError):
                runner.activate_skill("no-skill")

    def test_run_raises_type_error_with_actionable_message(self) -> None:
        # @trace WL-3000
        runner = AgentRunner()
        with pytest.raises(
            TypeError,
            match="is abstract and must be implemented by a concrete AgentRunner subclass",
        ):
            runner.run("do work", cwd=None, mode="read", timeout=10)

    def test_activate_skill_stores_content_in_activated_skills(
        self, tmp_path: Path
    ) -> None:
        runner = AgentRunner()
        manifest = SkillManifest(name="MySkill", instructions="Do the thing.")

        with patch(
            "thegent.skills.discovery.SkillDiscovery.find", return_value=manifest
        ):
            content = runner.activate_skill("MySkill")

        assert content == "Do the thing."
        assert runner.activated_skills["MySkill"] == "Do the thing."

    def test_activate_skill_returns_instruction_content(self, tmp_path: Path) -> None:
        runner = AgentRunner()
        manifest = SkillManifest(name="ReturnCheck", instructions="Return this.")

        with patch(
            "thegent.skills.discovery.SkillDiscovery.find", return_value=manifest
        ):
            result = runner.activate_skill("ReturnCheck")

        assert result == "Return this."

    def test_get_skill_prompt_suffix_empty_when_no_skills(self) -> None:
        runner = AgentRunner()
        assert runner.get_skill_prompt_suffix() == ""

    def test_get_skill_prompt_suffix_contains_skill_name_and_content(self) -> None:
        runner = AgentRunner()
        runner.activated_skills["alpha"] = "Alpha content."
        suffix = runner.get_skill_prompt_suffix()
        assert "alpha" in suffix
        assert "Alpha content." in suffix

    def test_get_skill_prompt_suffix_contains_all_activated_skills(self) -> None:
        runner = AgentRunner()
        runner.activated_skills["alpha"] = "Alpha."
        runner.activated_skills["beta"] = "Beta."
        suffix = runner.get_skill_prompt_suffix()
        assert "Alpha." in suffix
        assert "Beta." in suffix


# ---------------------------------------------------------------------------
# 8. MCP tool impl tests
# ---------------------------------------------------------------------------


class _FakeBackend:
    def list_skills(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "alpha",
                "description": "a",
                "version": "1.0.0",
                "entrypoint": "thegent",
                "path": "/tmp/a",
            },
            {
                "name": "beta",
                "description": "b",
                "version": "1.0.0",
                "entrypoint": "thegent",
                "path": "/tmp/b",
            },
        ]

    def activate_skill(self, skill_name: str) -> dict[str, Any] | None:
        if skill_name == "alpha":
            return {"name": "alpha", "content": "# alpha instructions"}
        return None


class TestMcpSkillTools:
    """# @trace WL-101"""

    def test_list_skills_returns_all_skills(self) -> None:
        result = thegent_list_skills_impl(backend=_FakeBackend())
        data = result.structured_content
        assert "skills" in data
        assert len(data["skills"]) == 2

    def test_list_skills_response_is_sorted_by_name(self) -> None:
        result = thegent_list_skills_impl(backend=_FakeBackend())
        names = [s["name"] for s in result.structured_content["skills"]]
        assert names == sorted(names)

    def test_activate_skill_returns_skill_payload(self) -> None:
        result = thegent_activate_skill_impl(
            skill_name="alpha",
            backend=_FakeBackend(),
            error_result_impl=_error_result,
        )
        data = result.structured_content
        assert data["skill"]["name"] == "alpha"
        assert "content" in data["skill"]

    def test_activate_skill_returns_error_for_missing_skill(self) -> None:
        result = thegent_activate_skill_impl(
            skill_name="missing",
            backend=_FakeBackend(),
            error_result_impl=_error_result,
        )
        data = result.structured_content
        assert "error" in data
        assert data["skill_name"] == "missing"

    def test_activate_skill_rejects_empty_name(self) -> None:
        result = thegent_activate_skill_impl(
            skill_name="   ",
            backend=_FakeBackend(),
            error_result_impl=_error_result,
        )
        data = result.structured_content
        assert data["error"] == "skill_name must be non-empty"

    def test_discovery_skill_backend_list_skills(self, tmp_path: Path) -> None:
        """DiscoverySkillBackend.list_skills returns a list (may be empty in test env)."""
        backend = DiscoverySkillBackend()
        skills = backend.list_skills()
        assert isinstance(skills, list)

    def test_discovery_skill_backend_activate_skill_returns_none_for_missing(
        self,
    ) -> None:
        """DiscoverySkillBackend.activate_skill returns None for unknown skill."""
        backend = DiscoverySkillBackend()
        result = backend.activate_skill("__no_such_skill_wl101__")
        assert result is None


# noqa: PT018
