"""Unit tests for ConversationDumper.

Tests the conversation dumper functionality including:
- Markdown and JSON dump formats
- Configurable dump locations
- Listing and reading dumps

# @trace CONV-DUMP-001
"""

from __future__ import annotations

from datetime import UTC, datetime

import orjson as json
import pytest

from thegent.session.conversation_dumper import (
    DEFAULT_DUMPS_DIR,
    ConversationDumper,
    ConversationRecord,
    get_dumper,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dumps_dir(tmp_path):
    """Create a temporary dumps directory."""
    dumps_dir = tmp_path / "dumps"
    dumps_dir.mkdir()
    return dumps_dir


@pytest.fixture
def dumper(temp_dumps_dir):
    """Create a ConversationDumper with a temporary directory."""
    return ConversationDumper(dumps_dir=temp_dumps_dir)


@pytest.fixture
def sample_record():
    """Create a sample ConversationRecord for testing."""
    return ConversationRecord(
        conversation_id="test-conv-123",
        timestamp=datetime(2026, 2, 20, 10, 30, 0, tzinfo=UTC),
        model="claude-3-opus",
        prompt="Hello, how are you?",
        response="I'm doing well, thank you!",
        metadata={"temperature": 0.7, "tokens": 150},
    )


# ---------------------------------------------------------------------------
# ConversationRecord tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConversationRecord:
    """Tests for ConversationRecord dataclass."""

    def test_to_markdown(self, sample_record):
        """Test conversion to markdown format."""
        markdown = sample_record.to_markdown()

        assert "# Conversation: test-conv-123" in markdown
        assert "**Timestamp:** 2026-02-20" in markdown
        assert "**Model:** claude-3-opus" in markdown
        assert "## Prompt" in markdown
        assert "Hello, how are you?" in markdown
        assert "## Response" in markdown
        assert "I'm doing well, thank you!" in markdown

    def test_to_markdown_with_metadata(self, sample_record):
        """Test markdown includes metadata."""
        markdown = sample_record.to_markdown()

        assert "**Metadata:**" in markdown
        assert '"temperature": 0.7' in markdown

    def test_to_json(self, sample_record):
        """Test conversion to JSON-serializable dict."""
        json_data = sample_record.to_json()

        assert json_data["conversation_id"] == "test-conv-123"
        assert json_data["model"] == "claude-3-opus"
        assert json_data["prompt"] == "Hello, how are you?"
        assert json_data["response"] == "I'm doing well, thank you!"
        assert json_data["metadata"]["temperature"] == 0.7

    def test_to_markdown_with_agent_synthesis(self, sample_record):
        """Markdown includes agent synthesis section when present."""
        sample_record.agent_synthesis = "Summarize blockers and next actions."
        markdown = sample_record.to_markdown()

        assert "## Agent Synthesis" in markdown
        assert "Summarize blockers and next actions." in markdown


# ---------------------------------------------------------------------------
# ConversationDumper initialization
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConversationDumperInit:
    """Tests for ConversationDumper initialization."""

    def test_default_directory(self):
        """Test default dumps directory."""
        dumper = ConversationDumper()
        assert dumper.dumps_dir == DEFAULT_DUMPS_DIR

    def test_custom_directory(self, temp_dumps_dir):
        """Test custom dumps directory."""
        dumper = ConversationDumper(dumps_dir=temp_dumps_dir)
        assert dumper.dumps_dir == temp_dumps_dir

    def test_string_directory(self, temp_dumps_dir):
        """Test string path conversion."""
        dumper = ConversationDumper(dumps_dir=str(temp_dumps_dir))
        assert dumper.dumps_dir == temp_dumps_dir


# ---------------------------------------------------------------------------
# ConversationDumper.dump_conversation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDumpConversation:
    """Tests for dump_conversation method."""

    def test_dump_creates_file(self, dumper, temp_dumps_dir):
        """Test that dumping creates a file."""
        path = dumper.dump_conversation(
            conversation_id="conv-001",
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
        )

        assert path.exists()
        assert path.parent == temp_dumps_dir
        assert path.suffix == ".md"
        assert "conv-001" in path.name

    def test_dump_content_includes_all_fields(self, dumper):
        """Test dumped content includes all conversation fields."""
        path = dumper.dump_conversation(
            conversation_id="conv-002",
            model="claude-3-sonnet",
            prompt="What is AI?",
            response="AI stands for Artificial Intelligence.",
        )

        content = path.read_text()

        assert "conv-002" in content
        assert "claude-3-sonnet" in content
        assert "What is AI?" in content
        assert "AI stands for Artificial Intelligence." in content

    def test_dump_with_metadata(self, dumper):
        """Test dumping with additional metadata."""
        path = dumper.dump_conversation(
            conversation_id="conv-003",
            model="gpt-4",
            prompt="Test",
            response="Result",
            metadata={"session_id": "sess-123", "version": "1.0"},
        )

        content = path.read_text()
        assert "session_id" in content
        assert "sess-123" in content

    def test_dump_creates_directory_if_missing(self, tmp_path):
        """Test that dump creates directory if it doesn't exist."""
        dumps_dir = tmp_path / "new_dumps"
        dumper = ConversationDumper(dumps_dir=dumps_dir)

        # Directory shouldn't exist yet
        assert not dumps_dir.exists()

        dumper.dump_conversation(
            conversation_id="conv-004",
            model="test",
            prompt="prompt",
            response="response",
        )

        assert dumps_dir.exists()


# ---------------------------------------------------------------------------
# ConversationDumper.dump_conversation_json
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDumpConversationJson:
    """Tests for dump_conversation_json method."""

    def test_json_dump_creates_file(self, dumper, temp_dumps_dir):
        """Test JSON dump creates a file."""
        path = dumper.dump_conversation_json(
            conversation_id="json-conv-001",
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
        )

        assert path.exists()
        assert path.suffix == ".json"
        assert "json-conv-001" in path.name

    def test_json_dump_content(self, dumper):
        """Test JSON dump contains valid JSON."""
        path = dumper.dump_conversation_json(
            conversation_id="json-conv-002",
            model="claude",
            prompt="prompt",
            response="response",
        )

        content = path.read_text()
        data = json.loads(content)

        assert data["conversation_id"] == "json-conv-002"
        assert data["model"] == "claude"
        assert data["prompt"] == "prompt"
        assert data["response"] == "response"

    def test_json_dump_includes_agent_synthesis(self, dumper):
        """JSON dump persists optional agent synthesis field."""
        path = dumper.dump_conversation_json(
            conversation_id="json-conv-003",
            model="claude",
            prompt="prompt",
            response="response",
            agent_synthesis="action plan summary",
        )

        data = json.loads(path.read_text())
        assert data["agent_synthesis"] == "action plan summary"


# ---------------------------------------------------------------------------
# ConversationDumper.list_dumps
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListDumps:
    """Tests for list_dumps method."""

    def test_list_empty_returns_empty_list(self, dumper):
        """Test listing empty directory returns empty list."""
        dumps = dumper.list_dumps()
        assert dumps == []

    def test_list_returns_all_dumps(self, dumper):
        """Test listing returns all dumps."""
        # Create some dumps
        dumper.dump_conversation("conv-1", "model", "p1", "r1")
        dumper.dump_conversation("conv-2", "model", "p2", "r2")
        dumper.dump_conversation("conv-3", "model", "p3", "r3")

        dumps = dumper.list_dumps()

        assert len(dumps) == 3

    def test_list_filter_by_conversation_id(self, dumper, temp_dumps_dir):
        """Test filtering by conversation ID."""
        import time

        # Create dumps with different IDs and slight delay to ensure different timestamps
        dumper.dump_conversation("conv-a", "model", "p1", "r1")
        time.sleep(0.15)  # Ensure different timestamp
        dumper.dump_conversation("conv-b", "model", "p2", "r2")
        time.sleep(0.15)
        dumper.dump_conversation("conv-a", "model", "p3", "r3")

        # Verify we created 3 files
        all_dumps = list(temp_dumps_dir.glob("conversation-*.md"))
        assert len(all_dumps) == 3, (
            f"Expected 3 dumps, got {len(all_dumps)}: {all_dumps}"
        )

        # Filter by conversation ID
        dumps = dumper.list_dumps(conversation_id="conv-a")

        assert len(dumps) == 2, (
            f"Expected 2 dumps for conv-a, got {len(dumps)}: {dumps}"
        )
        for dump in dumps:
            assert "conv-a" in dump.name

    def test_list_sorted_newest_first(self, dumper):
        """Test dumps are sorted by modification time, newest first."""
        import time

        # Create dumps with a small delay
        path1 = dumper.dump_conversation("conv-1", "model", "p1", "r1")
        time.sleep(0.01)  # Small delay to ensure different mtime
        path2 = dumper.dump_conversation("conv-2", "model", "p2", "r2")

        dumps = dumper.list_dumps()

        # Most recent should be first
        assert dumps[0] == path2
        assert dumps[1] == path1


# ---------------------------------------------------------------------------
# ConversationDumper.get_dump
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetDump:
    """Tests for get_dump method."""

    def test_get_dump_returns_record(self, dumper):
        """Test reading a dump returns a ConversationRecord."""
        path = dumper.dump_conversation(
            conversation_id="read-test",
            model="test-model",
            prompt="test prompt",
            response="test response",
        )

        record = dumper.get_dump(path)

        assert record is not None
        assert record.conversation_id == "read-test"
        assert record.model == "test-model"

    def test_get_nonexistent_returns_none(self, dumper, tmp_path):
        """Test reading nonexistent file returns None."""
        result = dumper.get_dump(tmp_path / "nonexistent.md")
        assert result is None

    def test_get_json_dump(self, dumper):
        """Test reading a JSON dump."""
        path = dumper.dump_conversation_json(
            conversation_id="json-read-test",
            model="test-model",
            prompt="prompt",
            response="response",
        )

        record = dumper.get_dump(path)

        assert record is not None
        assert record.conversation_id == "json-read-test"


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetDumper:
    """Tests for get_dumper factory function."""

    def test_get_dumper_default(self):
        """Test get_dumper with default settings."""
        dumper = get_dumper()
        assert isinstance(dumper, ConversationDumper)
        assert dumper.dumps_dir == DEFAULT_DUMPS_DIR

    def test_get_dumper_custom(self, temp_dumps_dir):
        """Test get_dumper with custom directory."""
        dumper = get_dumper(temp_dumps_dir)
        assert isinstance(dumper, ConversationDumper)
        assert dumper.dumps_dir == temp_dumps_dir
