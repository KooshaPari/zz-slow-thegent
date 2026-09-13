from __future__ import annotations

from pathlib import Path

from thegent.research.always_write_dumps import ConversationDumper


def test_dump_conversation_writes_prompt_and_synthesis(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)

    path = dumper.dump_conversation(
        "run-123",
        "full output text",
        prompt="exact user prompt",
        synthesis="agent synthesis",
        category="execution",
        tags=["auto-dump"],
        metadata={"exit_code": 0},
    )

    assert path.exists()
    assert path.parent.name == "execution"
    content = path.read_text(encoding="utf-8")
    assert "# Prompt" in content
    assert "exact user prompt" in content
    assert "# Synthesis" in content
    assert "agent synthesis" in content
    assert "# Full Output" in content
    assert "full output text" in content


def test_list_dumps_recurses_categories(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    dumper.dump_conversation("run-a", "a", category="execution")
    dumper.dump_conversation("run-b", "b", category="research")

    dumps = dumper.list_dumps()
    assert len(dumps) == 2


def test_dump_conversation_infers_tags_when_missing(tmp_path: Path) -> None:
    dumper = ConversationDumper(docs_dir=tmp_path)
    path = dumper.dump_conversation("run-c", "fact: keep parity\ndecision: add flag #wl156")
    content = path.read_text(encoding="utf-8")
    assert 'tags: ["wl156", "decision", "fact"]' in content
