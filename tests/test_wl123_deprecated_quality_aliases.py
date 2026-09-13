from __future__ import annotations

from pathlib import Path

import orjson as json

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_deprecated_quality_aliases.py"
MODULE = _load_script_module("check_deprecated_quality_aliases", SCRIPT_PATH)


def _mapping() -> dict[str, object]:
    return MODULE.load_alias_mapping(MODULE.DEFAULT_MAPPING_PATH)


def test_extract_task_names_reads_taskfile_keys() -> None:
    taskfile = """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
""".strip()

    names = MODULE.extract_task_names(taskfile)

    assert names == {"quality", "quality-a"}


def test_build_report_identifies_deprecated_and_missing_canonical() -> None:
    names = {"quality", "quality-a", "quality:dag"}

    mapping = _mapping()
    report = MODULE.build_report(
        names,
        deprecated_aliases=list(mapping["deprecated_aliases"]),
        replacement_suggestions_map=dict(mapping["replacement_suggestions"]),
        canonical_commands=list(mapping["canonical_commands"]),
    )

    assert report["deprecated_present"] == ["quality-a"]
    assert report["replacement_suggestions"] == {"quality-a": "quality"}
    assert report["canonical_missing"] == ["quality:dag:hard", "quality:dag:soft", "quality:fix:runner"]


def test_build_report_clean_state_has_no_findings() -> None:
    mapping = _mapping()
    names = set(mapping["canonical_commands"])

    report = MODULE.build_report(
        names,
        deprecated_aliases=list(mapping["deprecated_aliases"]),
        replacement_suggestions_map=dict(mapping["replacement_suggestions"]),
        canonical_commands=list(mapping["canonical_commands"]),
    )

    assert report["deprecated_count"] == 0
    assert report["canonical_missing_count"] == 0


def test_main_strict_mode_returns_nonzero_on_deprecated_aliases(tmp_path: Path) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--strict"])

    assert exit_code == 1


def test_main_migration_format_includes_replacement_suggestions(tmp_path: Path, capsys) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--format", "migration"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "quality-a -> quality" in out


def test_main_migration_markdown_format_emits_tables(tmp_path: Path, capsys) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--format", "migration-md"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "| Deprecated alias | Canonical replacement |" in out
    assert "| `quality-a` | `quality` |" in out
    assert "| Missing canonical commands |" in out


def test_main_migration_json_format_emits_structured_payload(tmp_path: Path, capsys) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--format", "migration-json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["replacement_suggestions"] == {"quality-a": "quality"}
    assert payload["canonical_missing"] == []


def test_build_migration_payload_returns_stable_keys() -> None:
    report = {
        "replacement_suggestions": {"quality-a": "quality"},
        "canonical_missing": ["quality:dag"],
    }

    payload = MODULE.build_migration_payload(report)

    assert payload == {
        "replacement_suggestions": {"quality-a": "quality"},
        "canonical_missing": ["quality:dag"],
    }


def test_build_migration_entries_returns_ordered_line_items() -> None:
    report = {
        "replacement_suggestions": {"quality-a": "quality", "quality-b": "quality:runner"},
        "canonical_missing": ["quality:dag"],
    }

    entries = MODULE.build_migration_entries(report)

    assert entries == [
        {"kind": "replacement", "deprecated_alias": "quality-a", "canonical_command": "quality"},
        {"kind": "replacement", "deprecated_alias": "quality-b", "canonical_command": "quality:runner"},
        {"kind": "canonical_missing", "canonical_command": "quality:dag"},
    ]


def test_main_migration_jsonl_format_emits_line_delimited_entries(tmp_path: Path, capsys) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--format", "migration-jsonl"])

    assert exit_code == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    assert lines == [{"canonical_command": "quality", "deprecated_alias": "quality-a", "kind": "replacement"}]


def test_main_summary_json_format_emits_compact_counts(tmp_path: Path, capsys) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
tasks:
  quality:
    cmds: []
  quality-a:
    cmds: []
  quality:dag:
    cmds: []
  quality:dag:soft:
    cmds: []
  quality:dag:hard:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--format", "summary-json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "canonical_missing_count": 0,
        "deprecated_count": 1,
        "ok": False,
        "replacement_count": 1,
        "total_findings": 1,
        "unmapped_deprecated_count": 0,
    }


def test_main_detects_canonical_commands_from_included_taskfiles(tmp_path: Path) -> None:
    include_dir = tmp_path / "templates" / "shared"
    include_dir.mkdir(parents=True)
    include_path = include_dir / "Taskfile.quality.yml"
    include_path.write_text(
        """
tasks:
  dag:
    cmds: []
  dag:soft:
    cmds: []
  dag:hard:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        """
includes:
  quality:
    taskfile: ./templates/shared/Taskfile.quality.yml
tasks:
  quality:
    cmds: []
  quality:fix:runner:
    cmds: []
""".strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = MODULE.main(["--taskfile", str(taskfile), "--strict"])

    assert exit_code == 0


def test_build_total_findings_count_sums_deprecated_and_missing_counts() -> None:
    report = {"deprecated_count": 2, "canonical_missing_count": 3}

    total = MODULE.build_total_findings_count(report)

    assert total == 5


def test_build_replacement_count_counts_replacement_entries() -> None:
    report = {"replacement_suggestions": {"quality-a": "quality", "quality-b": "quality:runner"}}

    count = MODULE.build_replacement_count(report)

    assert count == 2


def test_build_unmapped_deprecated_count_detects_missing_suggestions() -> None:
    report = {
        "deprecated_present": ["quality-a", "quality-legacy"],
        "replacement_suggestions": {"quality-a": "quality"},
    }

    count = MODULE.build_unmapped_deprecated_count(report)

    assert count == 1


def test_mapping_file_contains_required_keys() -> None:
    mapping = _mapping()

    assert sorted(mapping.keys()) == ["canonical_commands", "deprecated_aliases", "replacement_suggestions"]
