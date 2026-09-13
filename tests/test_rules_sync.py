"""Unit tests for thegent.core.rules_sync — RulesSyncManager.

FR Traceability: FR-HAX-002
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.core.rules_sync import (
    Rule,
    RulesSyncManager,
    RulesSyncResult,
    _parse_frontmatter,
    _replace_managed_section,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RULE_TEMPLATE = """\
---
id: {id}
title: {title}
platforms: [{platforms}]
---
{body}
"""


def _make_rules_dir(tmp_path: Path, rules: list[dict]) -> Path:
    """Create .thegent/rules/ with the given rule dicts and return its path."""
    rules_dir = tmp_path / ".thegent" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for rule in rules:
        fname = f"{rule['id']}.md"
        content = _RULE_TEMPLATE.format(
            id=rule["id"],
            title=rule["title"],
            platforms=", ".join(rule["platforms"]),
            body=rule.get("body", f"Content for {rule['id']}."),
        )
        (rules_dir / fname).write_text(content, encoding="utf-8")
    return rules_dir


def _default_rule(
    rule_id: str = "test-rule",
    title: str = "Test Rule",
    platforms: list[str] | None = None,
    body: str = "Do the right thing.",
) -> dict:
    return {
        "id": rule_id,
        "title": title,
        "platforms": platforms if platforms is not None else ["cursor", "claude", "codex"],
        "body": body,
    }


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseFrontmatter:
    def test_no_frontmatter_returns_empty_meta(self) -> None:
        # @trace FR-HAX-002
        meta, body = _parse_frontmatter("Just body text.\n")
        assert meta == {}
        assert body == "Just body text.\n"

    def test_parses_string_fields(self) -> None:
        # @trace FR-HAX-002
        text = "---\nid: my-rule\ntitle: My Rule\n---\nBody here."
        meta, body = _parse_frontmatter(text)
        assert meta["id"] == "my-rule"
        assert meta["title"] == "My Rule"
        assert body == "Body here."

    def test_parses_list_field(self) -> None:
        # @trace FR-HAX-002
        text = "---\nplatforms: [cursor, claude]\n---\nContent."
        meta, _ = _parse_frontmatter(text)
        assert meta["platforms"] == ["cursor", "claude"]

    def test_unclosed_frontmatter_raises(self) -> None:
        # @trace FR-HAX-002
        text = "---\nid: broken\n"
        with pytest.raises(ValueError, match="Unclosed frontmatter"):
            _parse_frontmatter(text)

    def test_strips_quotes_from_string_value(self) -> None:
        # @trace FR-HAX-002
        text = '---\nid: "quoted-id"\n---\nBody.'
        meta, _ = _parse_frontmatter(text)
        assert meta["id"] == "quoted-id"


# ---------------------------------------------------------------------------
# load_canonical_rules
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadCanonicalRules:
    def test_raises_if_rules_dir_missing(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        manager = RulesSyncManager()
        with pytest.raises(FileNotFoundError, match=r"\.thegent/rules"):
            manager.load_canonical_rules(tmp_path)

    def test_returns_empty_list_when_no_md_files(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules_dir = tmp_path / ".thegent" / "rules"
        rules_dir.mkdir(parents=True)
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert rules == []

    def test_loads_single_rule(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule()])
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0].id == "test-rule"
        assert rules[0].title == "Test Rule"

    def test_loads_multiple_rules(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(
            tmp_path,
            [
                _default_rule("rule-a", "Rule A"),
                _default_rule("rule-b", "Rule B"),
                _default_rule("rule-c", "Rule C"),
            ],
        )
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert len(rules) == 3
        assert {r.id for r in rules} == {"rule-a", "rule-b", "rule-c"}

    def test_rule_platforms_parsed_correctly(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule(platforms=["cursor", "codex"])])
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert rules[0].platforms == ["cursor", "codex"]

    def test_raises_on_missing_id(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules_dir = tmp_path / ".thegent" / "rules"
        rules_dir.mkdir(parents=True)
        bad = rules_dir / "bad.md"
        bad.write_text("---\ntitle: No ID Rule\nplatforms: [cursor]\n---\nBody.", encoding="utf-8")
        manager = RulesSyncManager()
        with pytest.raises(ValueError, match="missing required field 'id'"):
            manager.load_canonical_rules(tmp_path)

    def test_raises_on_missing_title(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules_dir = tmp_path / ".thegent" / "rules"
        rules_dir.mkdir(parents=True)
        bad = rules_dir / "no-title.md"
        bad.write_text("---\nid: no-title\nplatforms: [cursor]\n---\nBody.", encoding="utf-8")
        manager = RulesSyncManager()
        with pytest.raises(ValueError, match="missing required field 'title'"):
            manager.load_canonical_rules(tmp_path)

    def test_raises_on_missing_platforms(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules_dir = tmp_path / ".thegent" / "rules"
        rules_dir.mkdir(parents=True)
        bad = rules_dir / "no-plat.md"
        bad.write_text("---\nid: no-plat\ntitle: No Plat\n---\nBody.", encoding="utf-8")
        manager = RulesSyncManager()
        with pytest.raises(ValueError, match="missing required field 'platforms'"):
            manager.load_canonical_rules(tmp_path)

    def test_raises_on_unknown_platform(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules_dir = tmp_path / ".thegent" / "rules"
        rules_dir.mkdir(parents=True)
        bad = rules_dir / "bad-plat.md"
        bad.write_text(
            "---\nid: bad-plat\ntitle: Bad\nplatforms: [cursor, vscode]\n---\nBody.",
            encoding="utf-8",
        )
        manager = RulesSyncManager()
        with pytest.raises(ValueError, match="unknown platform"):
            manager.load_canonical_rules(tmp_path)

    def test_rule_body_content_captured(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule(body="Always use structlog.")])
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert "Always use structlog." in rules[0].content

    def test_source_file_set_correctly(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule("my-rule")])
        manager = RulesSyncManager()
        rules = manager.load_canonical_rules(tmp_path)
        assert rules[0].source_file.name == "my-rule.md"


# ---------------------------------------------------------------------------
# sync_to_cursor
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncToCursor:
    def _make_rules(self, tmp_path: Path) -> list[Rule]:
        _make_rules_dir(tmp_path, [_default_rule("r1", "Rule 1", ["cursor"])])
        return RulesSyncManager().load_canonical_rules(tmp_path)

    def test_writes_mdc_file(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_cursor(rules, tmp_path, dry_run=False)
        dest = tmp_path / ".cursor" / "rules" / "thegent-rules.mdc"
        assert dest.exists()
        assert len(records) == 1
        assert records[0].action == "write"

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_cursor(rules, tmp_path, dry_run=True)
        dest = tmp_path / ".cursor" / "rules" / "thegent-rules.mdc"
        assert not dest.exists()
        assert records[0].action == "dry_run"

    def test_mdc_file_contains_rule_title(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_cursor(rules, tmp_path)
        content = (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").read_text()
        assert "Rule 1" in content

    def test_skips_non_cursor_rules(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule("claude-only", platforms=["claude"])])
        rules = RulesSyncManager().load_canonical_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_cursor(rules, tmp_path)
        assert records == []

    def test_mdc_frontmatter_includes_always_apply(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_cursor(rules, tmp_path)
        content = (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").read_text()
        assert "alwaysApply: true" in content

    def test_destination_is_cursor_rules_dir(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_cursor(rules, tmp_path)
        assert records[0].platform == "cursor"
        assert ".cursor/rules" in str(records[0].destination)

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_cursor(rules, tmp_path)
        assert (tmp_path / ".cursor" / "rules").is_dir()


# ---------------------------------------------------------------------------
# sync_to_claude
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncToClaude:
    def _make_rules(self, tmp_path: Path, body: str = "No fallbacks.") -> list[Rule]:
        _make_rules_dir(tmp_path, [_default_rule("r1", "Rule 1", ["claude"], body=body)])
        return RulesSyncManager().load_canonical_rules(tmp_path)

    def test_creates_claude_md_when_absent(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_claude(rules, tmp_path)
        assert (tmp_path / "CLAUDE.md").exists()
        assert records[0].action == "write"

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_claude(rules, tmp_path, dry_run=True)
        assert not (tmp_path / "CLAUDE.md").exists()
        assert records[0].action == "dry_run"

    def test_appends_to_existing_claude_md(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        existing = "# Existing content\n\nSome pre-existing rules.\n"
        (tmp_path / "CLAUDE.md").write_text(existing, encoding="utf-8")
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_claude(rules, tmp_path)
        result = (tmp_path / "CLAUDE.md").read_text()
        assert "Existing content" in result
        assert "Rule 1" in result

    def test_replaces_managed_section_on_second_sync(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path, body="Version 1 content.")
        manager = RulesSyncManager()
        manager.sync_to_claude(rules, tmp_path)

        # Second sync with updated body
        _make_rules_dir(
            tmp_path,
            [_default_rule("r1", "Rule 1", ["claude"], body="Version 2 content.")],
        )
        rules2 = manager.load_canonical_rules(tmp_path)
        manager.sync_to_claude(rules2, tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()
        assert "Version 2 content." in content
        assert "Version 1 content." not in content

    def test_skips_non_claude_rules(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule("cursor-only", platforms=["cursor"])])
        rules = RulesSyncManager().load_canonical_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_claude(rules, tmp_path)
        assert records == []

    def test_managed_section_markers_present(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_claude(rules, tmp_path)
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "<!-- thegent:rules:start -->" in content
        assert "<!-- thegent:rules:end -->" in content

    def test_destination_is_claude_md(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_claude(rules, tmp_path)
        assert records[0].platform == "claude"
        assert records[0].destination.name == "CLAUDE.md"


# ---------------------------------------------------------------------------
# sync_to_codex
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncToCodex:
    def _make_rules(self, tmp_path: Path) -> list[Rule]:
        _make_rules_dir(tmp_path, [_default_rule("r1", "Rule 1", ["codex"])])
        return RulesSyncManager().load_canonical_rules(tmp_path)

    def test_writes_skill_md(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_codex(rules, tmp_path)
        dest = tmp_path / ".codex" / "skills" / "SKILL.md"
        assert dest.exists()
        assert records[0].action == "write"

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_codex(rules, tmp_path, dry_run=True)
        assert not (tmp_path / ".codex" / "skills" / "SKILL.md").exists()
        assert records[0].action == "dry_run"

    def test_skill_md_contains_rule_title(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_codex(rules, tmp_path)
        content = (tmp_path / ".codex" / "skills" / "SKILL.md").read_text()
        assert "Rule 1" in content

    def test_skips_non_codex_rules(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule("claude-only", platforms=["claude"])])
        rules = RulesSyncManager().load_canonical_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_codex(rules, tmp_path)
        assert records == []

    def test_destination_is_codex_skills_skill_md(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        records = manager.sync_to_codex(rules, tmp_path)
        assert records[0].platform == "codex"
        assert records[0].destination.name == "SKILL.md"
        assert ".codex" in str(records[0].destination)

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        rules = self._make_rules(tmp_path)
        manager = RulesSyncManager()
        manager.sync_to_codex(rules, tmp_path)
        assert (tmp_path / ".codex" / "skills").is_dir()


# ---------------------------------------------------------------------------
# sync_all (orchestration)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncAll:
    def _setup(self, tmp_path: Path) -> None:
        _make_rules_dir(
            tmp_path,
            [
                _default_rule("all-platforms", "All Platforms Rule", ["cursor", "claude", "codex"]),
                _default_rule("cursor-only", "Cursor Rule", ["cursor"]),
                _default_rule("claude-only", "Claude Rule", ["claude"]),
            ],
        )

    def test_returns_rules_sync_result(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        assert isinstance(result, RulesSyncResult)

    def test_loads_all_rules(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        assert result.rules_loaded == 3

    def test_default_syncs_all_platforms(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        platforms_synced = {r.platform for r in result.records}
        assert "cursor" in platforms_synced
        assert "claude" in platforms_synced
        assert "codex" in platforms_synced

    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path, dry_run=True)
        assert result.dry_run is True
        assert result.files_written == []
        assert len(result.files_dry_run) > 0

    def test_platform_filter_cursor_only(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path, platforms=["cursor"])
        assert all(r.platform == "cursor" for r in result.records)
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_platform_filter_claude_only(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path, platforms=["claude"])
        assert all(r.platform == "claude" for r in result.records)
        assert not (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()

    def test_platform_filter_codex_only(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path, platforms=["codex"])
        assert all(r.platform == "codex" for r in result.records)

    def test_success_when_all_writes_ok(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        assert result.success is True
        assert result.errors == []

    def test_raises_when_rules_dir_missing(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        manager = RulesSyncManager()
        with pytest.raises(FileNotFoundError):
            manager.sync_all(tmp_path)

    def test_duration_is_positive(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        assert result.duration > 0

    def test_files_written_matches_records(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        self._setup(tmp_path)
        manager = RulesSyncManager()
        result = manager.sync_all(tmp_path)
        for path in result.files_written:
            assert path.exists()


# ---------------------------------------------------------------------------
# _replace_managed_section
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReplaceManagedSection:
    def test_appends_when_markers_absent(self) -> None:
        # @trace FR-HAX-002
        existing = "# Preamble\n\nSome text.\n"
        new = "<!-- thegent:rules:start -->\n# Rules\n<!-- thegent:rules:end -->\n"
        result = _replace_managed_section(existing, new)
        assert "Preamble" in result
        assert "# Rules" in result

    def test_replaces_existing_section(self) -> None:
        # @trace FR-HAX-002
        existing = "# Preamble\n\n<!-- thegent:rules:start -->\nOld content\n<!-- thegent:rules:end -->\n"
        new = "<!-- thegent:rules:start -->\nNew content\n<!-- thegent:rules:end -->\n"
        result = _replace_managed_section(existing, new)
        assert "New content" in result
        assert "Old content" not in result
        assert "Preamble" in result

    def test_existing_content_after_section_preserved(self) -> None:
        # @trace FR-HAX-002
        existing = "<!-- thegent:rules:start -->\nOld\n<!-- thegent:rules:end -->\n\n# After section\n"
        new = "<!-- thegent:rules:start -->\nNew\n<!-- thegent:rules:end -->\n"
        result = _replace_managed_section(existing, new)
        assert "# After section" in result

    def test_no_double_newline_on_append_to_empty(self) -> None:
        # @trace FR-HAX-002
        new = "<!-- thegent:rules:start -->\nNew\n<!-- thegent:rules:end -->\n"
        result = _replace_managed_section("", new)
        assert result.startswith("<!--")


# ---------------------------------------------------------------------------
# CLI integration — thegent rules sync
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRulesSyncCLI:
    """Verify the `thegent rules sync` CLI command is registered and functional."""

    def test_rules_subcommand_visible_in_help(self) -> None:
        # @trace FR-HAX-002
        from typer.testing import CliRunner

        from thegent.cli.apps.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "rules" in result.output

    def test_rules_sync_help_reachable(self) -> None:
        # @trace FR-HAX-002
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        # When invoked via the rules sub-app directly (not through main),
        # typer collapses the single "sync" command so --help is at the root.
        result = runner.invoke(rules_app, ["--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--platform" in result.output

    def test_rules_sync_dry_run_flag(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule()])
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(rules_app, ["--dry-run", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert not (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()

    def test_rules_sync_cursor_platform_only(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule()])
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(rules_app, ["--platform", "cursor", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_rules_sync_invalid_platform_exits_1(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(rules_app, ["--platform", "vscode", "--project", str(tmp_path)])
        assert result.exit_code == 1

    def test_rules_sync_no_rules_dir_exits_nonzero(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(rules_app, ["--project", str(tmp_path)])
        assert result.exit_code != 0

    def test_rules_sync_all_platforms_writes_all_files(self, tmp_path: Path) -> None:
        # @trace FR-HAX-002
        _make_rules_dir(tmp_path, [_default_rule()])
        from thegent.cli.apps.rules import app as rules_app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(rules_app, ["--project", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".codex" / "skills" / "SKILL.md").exists()
