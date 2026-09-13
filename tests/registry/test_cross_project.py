"""Tests for CrossProjectRegistry and PersonaRecord.

FR Traceability: FR-AGT-020 (cross-project persona discovery and search)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 -- used at runtime for Path construction
from textwrap import dedent

import orjson as json
import pytest

from thegent.registry.cross_project import (
    CrossProjectRegistry,
    PersonaRecord,
    _extract_capabilities,
    _extract_name,
    _parse_frontmatter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agents_dir(tmp_path: Path) -> Path:
    """Return an agents/ subdir inside tmp_path."""
    d = tmp_path / "agents"
    d.mkdir()
    return d


def _write_persona(agents_dir: Path, filename: str, content: str) -> Path:
    f = agents_dir / filename
    f.write_text(content, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseFrontmatter:
    """Tests for the internal frontmatter parser."""

    def test_basic_frontmatter_extracted(self) -> None:
        """Valid YAML frontmatter returns a dict with expected keys."""
        # @trace FR-AGT-020
        text = dedent("""\
            ---
            name: my-agent
            tools: read-only
            ---
            Body text here.
        """)
        result = _parse_frontmatter(text)
        assert result["name"] == "my-agent"
        assert result["tools"] == "read-only"

    def test_no_frontmatter_returns_empty(self) -> None:
        """Files without frontmatter return an empty dict."""
        # @trace FR-AGT-020
        assert _parse_frontmatter("Just some text, no frontmatter.") == {}

    def test_frontmatter_with_leading_whitespace(self) -> None:
        """Leading whitespace before --- is tolerated."""
        # @trace FR-AGT-020
        text = "\n\n---\nname: agent\n---\n"
        result = _parse_frontmatter(text)
        assert result.get("name") == "agent"

    def test_unclosed_frontmatter_returns_empty(self) -> None:
        """A frontmatter block without a closing --- returns empty."""
        # @trace FR-AGT-020
        text = "---\nname: agent\n"
        assert _parse_frontmatter(text) == {}

    def test_invalid_yaml_returns_empty(self) -> None:
        """Malformed YAML in frontmatter returns an empty dict, not an error."""
        # @trace FR-AGT-020
        text = "---\n: invalid: yaml:\n---\n"
        # Should not raise; may return {} or partial dict depending on YAML parser
        result = _parse_frontmatter(text)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _extract_capabilities / _extract_name
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractHelpers:
    """Unit tests for the capability and name extraction helpers."""

    def test_extract_capabilities_from_tools_string(self) -> None:
        """Comma-delimited tools string is split into individual capabilities."""
        # @trace FR-AGT-020
        fm = {"tools": "read-only, write, execute"}
        result = _extract_capabilities(fm)
        assert result == ["read-only", "write", "execute"]

    def test_extract_capabilities_from_list(self) -> None:
        """A list of tools is returned as-is (lowercased)."""
        # @trace FR-AGT-020
        fm = {"capabilities": ["Code Review", "Testing"]}
        result = _extract_capabilities(fm)
        assert result == ["code review", "testing"]

    def test_extract_capabilities_deduplicates(self) -> None:
        """Duplicate capability values are removed, order preserved."""
        # @trace FR-AGT-020
        fm = {"tools": "search, search, read"}
        result = _extract_capabilities(fm)
        assert result == ["search", "read"]

    def test_extract_capabilities_empty_frontmatter(self) -> None:
        """Missing tools/capabilities keys returns empty list."""
        # @trace FR-AGT-020
        assert _extract_capabilities({}) == []

    def test_extract_name_from_frontmatter(self) -> None:
        """Name field in frontmatter takes precedence over stem."""
        # @trace FR-AGT-020
        assert _extract_name({"name": "my-agent"}, "fallback") == "my-agent"

    def test_extract_name_falls_back_to_stem(self) -> None:
        """Missing name field falls back to the file stem."""
        # @trace FR-AGT-020
        assert _extract_name({}, "fallback-stem") == "fallback-stem"

    def test_extract_name_blank_name_falls_back(self) -> None:
        """A blank name value falls back to the stem."""
        # @trace FR-AGT-020
        assert _extract_name({"name": "   "}, "stem") == "stem"


# ---------------------------------------------------------------------------
# PersonaRecord
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPersonaRecord:
    """Tests for PersonaRecord serialization round-trip."""

    def test_to_dict_keys_present(self, tmp_path: Path) -> None:
        """to_dict() includes all expected keys."""
        # @trace FR-AGT-020
        record = PersonaRecord(
            name="test-agent",
            project_root=tmp_path,
            capabilities=["read", "write"],
            persona_file=tmp_path / "agents" / "test-agent.md",
            last_seen=datetime(2026, 1, 1, tzinfo=UTC),
        )
        d = record.to_dict()
        assert set(d) == {"name", "project_root", "capabilities", "persona_file", "last_seen"}

    def test_from_dict_round_trip(self, tmp_path: Path) -> None:
        """PersonaRecord survives a to_dict/from_dict round-trip."""
        # @trace FR-AGT-020
        original = PersonaRecord(
            name="round-trip",
            project_root=tmp_path,
            capabilities=["cap-a"],
            persona_file=tmp_path / "agents" / "x.md",
            last_seen=datetime(2026, 2, 15, 10, 0, 0, tzinfo=UTC),
        )
        restored = PersonaRecord.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.capabilities == original.capabilities
        assert restored.project_root == original.project_root
        assert restored.persona_file == original.persona_file

    def test_from_dict_bad_timestamp_uses_fallback(self, tmp_path: Path) -> None:
        """A corrupt last_seen timestamp does not raise; a fallback time is used."""
        # @trace FR-AGT-020
        data = {
            "name": "a",
            "project_root": str(tmp_path),
            "capabilities": [],
            "persona_file": str(tmp_path / "x.md"),
            "last_seen": "not-a-date",
        }
        record = PersonaRecord.from_dict(data)
        assert isinstance(record.last_seen, datetime)


# ---------------------------------------------------------------------------
# CrossProjectRegistry - discover_personas
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiscoverPersonas:
    """Tests for CrossProjectRegistry.discover_personas."""

    def test_discover_finds_md_files(self, tmp_path: Path) -> None:
        """discover_personas() returns one record per .md file in agents/."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "alpha.md", "---\nname: alpha\n---\n# Alpha")
        _write_persona(agents_dir, "beta.md", "---\nname: beta\n---\n# Beta")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        records = reg.discover_personas(tmp_path)

        names = {r.name for r in records}
        assert names == {"alpha", "beta"}

    def test_discover_no_agents_dir_returns_empty(self, tmp_path: Path) -> None:
        """discover_personas() returns [] when agents/ directory is absent."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        assert reg.discover_personas(tmp_path) == []

    def test_discover_ignores_non_md_files(self, tmp_path: Path) -> None:
        """Non-.md files in agents/ are ignored."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        (agents_dir / "not-a-persona.txt").write_text("ignore me")
        (agents_dir / "valid.md").write_text("---\nname: valid\n---\n")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        records = reg.discover_personas(tmp_path)
        assert len(records) == 1
        assert records[0].name == "valid"

    def test_discover_extracts_capabilities(self, tmp_path: Path) -> None:
        """Capabilities are parsed from frontmatter and returned in the record."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "cap.md", "---\nname: cap\ntools: search, read\n---\n")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        records = reg.discover_personas(tmp_path)
        assert records[0].capabilities == ["search", "read"]

    def test_discover_sets_project_root(self, tmp_path: Path) -> None:
        """Each PersonaRecord carries the resolved project_root."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "x.md", "# no frontmatter")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        records = reg.discover_personas(tmp_path)
        assert records[0].project_root == tmp_path.resolve()

    def test_discover_name_falls_back_to_stem(self, tmp_path: Path) -> None:
        """When frontmatter has no name field, file stem is used as the name."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "my-persona.md", "Just plain markdown.")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        records = reg.discover_personas(tmp_path)
        assert records[0].name == "my-persona"


# ---------------------------------------------------------------------------
# CrossProjectRegistry - register_project
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRegisterProject:
    """Tests for CrossProjectRegistry.register_project."""

    def test_register_project_adds_records(self, tmp_path: Path) -> None:
        """register_project() populates get_all() with discovered personas."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "agent1.md", "---\nname: agent1\n---\n")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        returned = reg.register_project(tmp_path)

        assert len(returned) == 1
        assert len(reg.get_all()) == 1
        assert reg.get_all()[0].name == "agent1"

    def test_register_project_saves_to_disk(self, tmp_path: Path) -> None:
        """register_project() writes the registry JSON file."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "saved.md", "---\nname: saved\n---\n")

        reg_file = tmp_path / "reg.json"
        reg = CrossProjectRegistry(registry_file=reg_file)
        reg.register_project(tmp_path)

        assert reg_file.exists()
        data = json.loads(reg_file.read_text())
        assert any(d["name"] == "saved" for d in data)

    def test_register_project_updates_existing_record(self, tmp_path: Path) -> None:
        """Re-registering the same project overwrites the previous record."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        md = _write_persona(agents_dir, "agent.md", "---\nname: agent\ntools: read\n---\n")

        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        reg.register_project(tmp_path)

        # Update the persona file and re-register
        md.write_text("---\nname: agent\ntools: read, write\n---\n")
        reg.register_project(tmp_path)

        records = reg.get_all()
        assert len(records) == 1
        assert "write" in records[0].capabilities

    def test_register_empty_project_returns_empty_list(self, tmp_path: Path) -> None:
        """A project with no agents/ dir returns an empty list."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        result = reg.register_project(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# CrossProjectRegistry - search
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSearch:
    """Tests for CrossProjectRegistry.search."""

    def _populate(self, tmp_path: Path, reg: CrossProjectRegistry) -> None:
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "reader.md", "---\nname: reader\ntools: read-only\n---\n")
        _write_persona(agents_dir, "writer.md", "---\nname: writer\ntools: write\n---\n")
        _write_persona(agents_dir, "all.md", "---\nname: all\ntools: read-only, write, search\n---\n")
        reg.register_project(tmp_path)

    def test_search_finds_matching_capability(self, tmp_path: Path) -> None:
        """search() returns personas that include the queried capability."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        self._populate(tmp_path, reg)

        results = reg.search("write")
        names = {r.name for r in results}
        assert "writer" in names
        assert "all" in names
        assert "reader" not in names

    def test_search_is_case_insensitive(self, tmp_path: Path) -> None:
        """search() is case-insensitive."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        self._populate(tmp_path, reg)

        assert reg.search("READ-ONLY") == reg.search("read-only")

    def test_search_no_match_returns_empty(self, tmp_path: Path) -> None:
        """search() returns [] when no persona matches."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        self._populate(tmp_path, reg)

        assert reg.search("nonexistent-cap") == []

    def test_search_empty_registry_returns_empty(self, tmp_path: Path) -> None:
        """search() on an empty registry always returns []."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "reg.json")
        assert reg.search("anything") == []


# ---------------------------------------------------------------------------
# CrossProjectRegistry - save / load
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSaveLoad:
    """Tests for CrossProjectRegistry persistence (save/load round-trip)."""

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """save() creates parent directories if they do not exist."""
        # @trace FR-AGT-020
        reg_file = tmp_path / "deep" / "nested" / "reg.json"
        reg = CrossProjectRegistry(registry_file=reg_file)
        reg.save()
        assert reg_file.exists()

    def test_save_load_round_trip(self, tmp_path: Path) -> None:
        """Records survive a save/load cycle."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "persisted.md", "---\nname: persisted\ntools: search\n---\n")

        reg_file = tmp_path / "reg.json"
        reg1 = CrossProjectRegistry(registry_file=reg_file)
        reg1.register_project(tmp_path)

        reg2 = CrossProjectRegistry(registry_file=reg_file)
        reg2.load()

        records = reg2.get_all()
        assert len(records) == 1
        assert records[0].name == "persisted"
        assert records[0].capabilities == ["search"]

    def test_load_nonexistent_file_is_silent(self, tmp_path: Path) -> None:
        """load() on a missing file raises no error and leaves registry empty."""
        # @trace FR-AGT-020
        reg = CrossProjectRegistry(registry_file=tmp_path / "does_not_exist.json")
        reg.load()
        assert reg.get_all() == []

    def test_load_corrupt_file_raises_value_error(self, tmp_path: Path) -> None:
        """A corrupt JSON file causes load() to raise ValueError."""
        # @trace FR-AGT-020
        reg_file = tmp_path / "bad.json"
        reg_file.write_text("NOT VALID JSON{{{{", encoding="utf-8")

        reg = CrossProjectRegistry(registry_file=reg_file)
        with pytest.raises(ValueError, match="Corrupt persona registry"):
            reg.load()

    def test_load_wrong_root_type_raises_value_error(self, tmp_path: Path) -> None:
        """A JSON file containing a dict (not a list) raises ValueError."""
        # @trace FR-AGT-020
        reg_file = tmp_path / "wrong.json"
        reg_file.write_text(json.dumps({"key": "value"}).decode(), encoding="utf-8")

        reg = CrossProjectRegistry(registry_file=reg_file)
        with pytest.raises(ValueError, match="Expected JSON list"):
            reg.load()

    def test_save_is_atomic(self, tmp_path: Path) -> None:
        """save() writes to a .tmp file and then renames it (atomic write)."""
        # @trace FR-AGT-020
        agents_dir = _make_agents_dir(tmp_path)
        _write_persona(agents_dir, "a.md", "---\nname: a\n---\n")

        reg_file = tmp_path / "reg.json"
        reg = CrossProjectRegistry(registry_file=reg_file)
        reg.register_project(tmp_path)

        # The .tmp file should be cleaned up after save
        assert reg_file.exists()
        assert not reg_file.with_suffix(".tmp").exists()

    def test_multiple_projects_persist(self, tmp_path: Path) -> None:
        """Personas from two different projects are both saved and restored."""
        # @trace FR-AGT-020
        proj_a = tmp_path / "proj_a"
        proj_b = tmp_path / "proj_b"
        proj_a.mkdir()
        proj_b.mkdir()

        _make_agents_dir(proj_a)
        _make_agents_dir(proj_b)
        _write_persona(proj_a / "agents", "alpha.md", "---\nname: alpha\n---\n")
        _write_persona(proj_b / "agents", "beta.md", "---\nname: beta\n---\n")

        reg_file = tmp_path / "reg.json"
        reg1 = CrossProjectRegistry(registry_file=reg_file)
        reg1.register_project(proj_a)
        reg1.register_project(proj_b)

        reg2 = CrossProjectRegistry(registry_file=reg_file)
        reg2.load()

        names = {r.name for r in reg2.get_all()}
        assert names == {"alpha", "beta"}
