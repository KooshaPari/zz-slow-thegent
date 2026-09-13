from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.research.always_write_dumps import ConversationDumper


def test_dump_conversation_json_writes_valid_json_with_expected_fields(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    json_path = dumper.dump_conversation_json(
        "run-json-1",
        "full output text",
        prompt="exact prompt",
        synthesis="brief synthesis",
        category="execution",
        tags=["alpha"],
        metadata={"attempt": 1},
        timestamp="2026-02-22-12-00-00",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["conversation_id"] == "run-json-1"
    assert payload["timestamp"] == "2026-02-22-12-00-00"
    assert payload["category"] == "execution"
    assert payload["tags"] == ["alpha"]
    assert payload["metadata"] == {"attempt": 1}
    assert payload["prompt"] == "exact prompt"
    assert payload["synthesis"] == "brief synthesis"
    assert payload["full_output"] == "full output text"


def test_default_dump_conversation_writes_json_companion(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    md_path = dumper.dump_conversation("run-default-1", "default companion content")
    json_path = md_path.with_suffix(".json")

    assert md_path.exists()
    assert json_path.exists()


def test_disabling_write_json_companion_skips_companion_file(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    md_path = dumper.dump_conversation(
        "run-no-companion-1",
        "no companion content",
        write_json_companion=False,
    )
    json_path = md_path.with_suffix(".json")

    assert md_path.exists()
    assert not json_path.exists()


def test_markdown_frontmatter_includes_json_companion_path_when_written(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    md_path = dumper.dump_conversation("run-frontmatter-1", "frontmatter content")
    json_path = md_path.with_suffix(".json")

    text = md_path.read_text(encoding="utf-8")
    metadata_line = next(line for line in text.splitlines() if line.startswith("metadata: "))
    metadata = json.loads(metadata_line.removeprefix("metadata: "))

    assert metadata["json_companion_path"] == str(json_path)


def test_list_dumps_json_returns_recursive_category_files(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation_json("run-list-a", "a", category="execution")
    dumper.dump_conversation_json("run-list-b", "b", category="research")

    dumps = dumper.list_dumps_json()

    assert len(dumps) == 2
    assert {dump.parent.name for dump in dumps} == {"execution", "research"}
