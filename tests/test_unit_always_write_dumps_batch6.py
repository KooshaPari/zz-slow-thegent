from __future__ import annotations

import os
from pathlib import Path

import orjson as json

from thegent.research.always_write_dumps import ConversationDumper


def test_latest_dump_returns_newest_markdown_for_category_and_global(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    old_exec = dumper.dump_conversation("run-old-exec", "old", category="execution")
    new_exec = dumper.dump_conversation("run-new-exec", "new", category="execution")
    newest_research = dumper.dump_conversation("run-newest-research", "newest", category="research")

    old_mtime = 1_700_000_001
    new_exec_mtime = 1_700_000_002
    newest_research_mtime = 1_700_000_003
    os.utime(old_exec, (old_mtime, old_mtime))
    os.utime(new_exec, (new_exec_mtime, new_exec_mtime))
    os.utime(newest_research, (newest_research_mtime, newest_research_mtime))

    assert dumper.latest_dump(category="execution") == new_exec
    assert dumper.latest_dump() == newest_research


def test_latest_dump_json_only_returns_newest_json_companion(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    first_md = dumper.dump_conversation("run-json-a", "a", category="execution")
    second_md = dumper.dump_conversation("run-json-b", "b", category="execution")
    first_json = first_md.with_suffix(".json")
    second_json = second_md.with_suffix(".json")

    first_mtime = 1_700_000_010
    second_mtime = 1_700_000_020
    os.utime(first_json, (first_mtime, first_mtime))
    os.utime(second_json, (second_mtime, second_mtime))

    assert dumper.latest_dump(json_only=True) == second_json


def test_load_dump_json_returns_dict_for_valid_and_none_for_invalid_json(
    tmp_path: Path,
    caplog,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    valid_path = tmp_path / "valid.json"
    invalid_path = tmp_path / "invalid.json"

    valid_path.write_text('{"ok": true, "count": 2}', encoding="utf-8")
    invalid_path.write_text('{"ok": true,', encoding="utf-8")

    assert dumper.load_dump_json(valid_path) == {"ok": True, "count": 2}
    assert dumper.load_dump_json(invalid_path) is None
    assert f"Failed to parse JSON companion {invalid_path}" in caplog.text


def test_load_dump_json_returns_none_for_missing_companion_file(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    missing = tmp_path / "missing.json"
    assert dumper.load_dump_json(missing) is None


def test_summarize_dump_categories_returns_expected_counts(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    dumper.dump_conversation("run-exec-1", "x", category="execution")
    dumper.dump_conversation("run-exec-2", "y", category="execution")
    dumper.dump_conversation("run-research-1", "z", category="research")
    (tmp_path / "conversation-root-only.md").write_text("root", encoding="utf-8")

    assert dumper.summarize_dump_categories() == {
        "execution": 2,
        "research": 1,
        "uncategorized": 1,
    }


def test_persist_dump_index_and_export_markdown_create_expected_artifacts(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation("run-exec-index", "exec", category="execution")
    dumper.dump_conversation("run-research-index", "research", category="research")

    json_index_path = dumper.persist_dump_index()
    md_index_path = dumper.export_dump_index_markdown()

    assert json_index_path.exists()
    assert md_index_path.exists()

    payload = json.loads(json_index_path.read_text(encoding="utf-8"))
    assert {"generated_at", "docs_dir", "categories", "latest_dump", "latest_json_dump"} <= set(payload)
    assert payload["categories"] == {"execution": 1, "research": 1}
    assert payload["latest_dump"]
    assert payload["latest_json_dump"]

    markdown = md_index_path.read_text(encoding="utf-8")
    assert "# Dump Index" in markdown
    assert "## Category Counts" in markdown
    assert "| `execution` | 1 |" in markdown
    assert "| `research` | 1 |" in markdown
    assert "Latest markdown dump:" in markdown
    assert "Latest JSON dump:" in markdown
