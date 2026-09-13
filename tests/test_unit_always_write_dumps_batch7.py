from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.research.always_write_dumps import ConversationDumper


def _payload_shape(payload: dict) -> dict[str, object]:
    return {key: sorted(value.keys()) if isinstance(value, dict) else type(value) for key, value in payload.items()}


def test_list_dump_categories_returns_sorted_categories(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation("run-z", "z", category="zeta")
    dumper.dump_conversation("run-a", "a", category="alpha")
    dumper.dump_conversation("run-m", "m", category="middle")

    assert dumper.list_dump_categories() == ["alpha", "middle", "zeta"]


def test_dump_index_payload_has_expected_keys_and_writes_no_files(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    payload = dumper.dump_index_payload()

    assert {
        "generated_at",
        "docs_dir",
        "categories",
        "latest_dump",
        "latest_json_dump",
    } <= set(payload)
    assert [p for p in tmp_path.rglob("*") if p.is_file()] == []


def test_persist_dump_index_structure_matches_dump_index_payload_shape(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation("run-shape", "content", category="execution")

    payload = dumper.dump_index_payload()
    index_path = dumper.persist_dump_index()
    persisted = json.loads(index_path.read_text(encoding="utf-8"))

    assert _payload_shape(persisted) == _payload_shape(payload)


def test_export_dump_index_markdown_contains_total_markdown_dumps_line(
    tmp_path: Path,
) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation("run-1", "one", category="execution")
    dumper.dump_conversation("run-2", "two", category="research")

    markdown_path = dumper.export_dump_index_markdown()
    markdown = markdown_path.read_text(encoding="utf-8")

    assert "Total markdown dumps:" in markdown


def test_new_dump_apis_are_sane_for_empty_docs_dir(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    assert dumper.list_dump_categories() == []
    assert dumper.latest_dump() is None
    assert dumper.latest_dump(json_only=True) is None

    payload = dumper.dump_index_payload()
    assert payload["categories"] == {}
    assert payload["latest_dump"] is None
    assert payload["latest_json_dump"] is None
