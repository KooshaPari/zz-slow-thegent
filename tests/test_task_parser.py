"""Tests for task parser."""

import json
from pathlib import Path

import pytest

from thegent.task.parser import (
    detect_task_format,
    extract_markdown_sections,
    parse_legacy_task,
    parse_task_file,
    parse_yaml_frontmatter,
)


class TestParseYamlFrontmatter:
    """Tests for parse_yaml_frontmatter function."""

    def test_parse_yaml_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
id: test-task
title: Test Task
priority: P1
---
## Body
Test body content
"""
        frontmatter, body = parse_yaml_frontmatter(content)
        assert frontmatter["id"] == "test-task"
        assert frontmatter["title"] == "Test Task"
        assert frontmatter["priority"] == "P1"
        assert "## Body" in body
        assert "Test body content" in body

    def test_parse_yaml_frontmatter_with_nested(self):
        """Test parsing YAML frontmatter with nested structures."""
        content = """---
id: test-task
title: Test Task
metadata:
  tags:
    - test
    - validation
  estimated_hours: 5
depends:
  - dep-1
  - dep-2
---
## Body
Content here
"""
        frontmatter, _body = parse_yaml_frontmatter(content)
        assert frontmatter["id"] == "test-task"
        assert frontmatter["metadata"]["tags"] == ["test", "validation"]
        assert frontmatter["metadata"]["estimated_hours"] == 5
        assert frontmatter["depends"] == ["dep-1", "dep-2"]

    def test_parse_yaml_frontmatter_empty(self):
        """Test parsing empty YAML frontmatter."""
        content = """---
---
## Body
Content here
"""
        frontmatter, _body = parse_yaml_frontmatter(content)
        assert frontmatter == {}

    def test_parse_yaml_frontmatter_missing(self):
        """Test parsing content without frontmatter raises ValueError."""
        content = """## Body
Content without frontmatter
"""
        with pytest.raises(ValueError, match="No YAML frontmatter found"):
            parse_yaml_frontmatter(content)

    def test_parse_yaml_frontmatter_invalid_yaml(self):
        """Test parsing invalid YAML raises ValueError."""
        content = """---
id: test-task
invalid: yaml: syntax: error
---
"""
        with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
            parse_yaml_frontmatter(content)

    def test_parse_yaml_frontmatter_yaml_not_dict(self):
        """Test parsing YAML that is not a dictionary raises ValueError."""
        content = """---
- item 1
- item 2
---
"""
        with pytest.raises(ValueError, match="Frontmatter must be a dictionary"):
            parse_yaml_frontmatter(content)

    def test_parse_yaml_frontmatter_no_trailing_newline(self):
        """Test parsing frontmatter without trailing newline after closing ---."""
        content = """---
id: test-task
title: Test Task
---## Body
Content here
"""
        frontmatter, _body = parse_yaml_frontmatter(content)
        assert frontmatter["id"] == "test-task"

    def test_parse_yaml_frontmatter_multiline_values(self):
        """Test parsing frontmatter with multiline YAML values."""
        content = """---
description: |
  This is a multiline
  description that spans
  multiple lines
---
## Body
"""
        frontmatter, _body = parse_yaml_frontmatter(content)
        assert "multiline" in frontmatter["description"]
        assert "spans" in frontmatter["description"]

    def test_parse_yaml_frontmatter_special_characters(self):
        """Test parsing frontmatter with special characters."""
        content = """---
id: test-task
title: "Test: Task with \"quotes\" and 'apostrophes'"
---
## Body
"""
        frontmatter, _body = parse_yaml_frontmatter(content)
        assert frontmatter["id"] == "test-task"
        assert "quotes" in frontmatter["title"]


class TestDetectTaskFormat:
    """Tests for detect_task_format function."""

    def test_detect_yaml_frontmatter(self):
        """Test detecting YAML frontmatter format."""
        content = """---
id: test-task
---
"""
        assert detect_task_format(content) == "yaml_frontmatter"

    def test_detect_json(self):
        """Test detecting JSON format."""
        content = '{"id": "test-task", "title": "Test"}'
        assert detect_task_format(content) == "json"

    def test_detect_legacy_task_format(self):
        """Test detecting legacy TASK() format."""
        content = """TASK(worker: "Test task")
Task Input:
"""
        assert detect_task_format(content) == "legacy"

    def test_detect_legacy_task_input(self):
        """Test detecting legacy Task Input format."""
        content = """Task Input:
**ID:** test-task
"""
        assert detect_task_format(content) == "legacy"

    def test_detect_unknown(self):
        """Test detecting unknown format."""
        content = """# Just a header
Some content
"""
        assert detect_task_format(content) == "unknown"

    def test_detect_json_with_whitespace(self):
        """Test detecting JSON with leading whitespace."""
        content = '  {"id": "test-task"}'
        assert detect_task_format(content) == "json"


class TestExtractMarkdownSections:
    """Tests for extract_markdown_sections function."""

    def test_extract_sections_single(self):
        """Test extracting a single section."""
        body = """## Description
This is the description.
"""
        sections = extract_markdown_sections(body)
        assert "description" in sections
        assert "This is the description." in sections["description"]

    def test_extract_sections_multiple(self):
        """Test extracting multiple sections."""
        body = """## Description
Description content.

## Steps
Step content.

## Deliverables
Deliverables content.
"""
        sections = extract_markdown_sections(body)
        assert "description" in sections
        assert "steps" in sections
        assert "deliverables" in sections
        assert sections["description"] == "Description content."
        assert sections["steps"] == "Step content."
        assert sections["deliverables"] == "Deliverables content."

    def test_extract_sections_no_sections(self):
        """Test extracting sections when none exist."""
        body = """Just plain content
without headers
"""
        sections = extract_markdown_sections(body)
        assert sections == {}

    def test_extract_sections_with_multiline_content(self):
        """Test extracting sections with multiline content."""
        body = """## Implementation Details
Line 1
Line 2
Line 3
## Notes
Notes content
"""
        sections = extract_markdown_sections(body)
        assert "implementation_details" in sections
        assert "Line 1" in sections["implementation_details"]
        assert "notes" in sections

    def test_extract_sections_header_with_spaces(self):
        """Test that header spaces are converted to underscores."""
        body = """## Implementation Details
Content
"""
        sections = extract_markdown_sections(body)
        assert "implementation_details" in sections


class TestParseLegacyTask:
    """Tests for parse_legacy_task function."""

    def test_parse_legacy_task_basic(self):
        """Test parsing basic legacy task format."""
        content = """TASK(worker: "Test task description")
Task Input:
**ID:** legacy-task
**Title:** Legacy Task
**Priority:** P1
**Depends:** none

### Implementation Details
Some implementation details.
"""
        task = parse_legacy_task(content)
        assert task["subagent_type"] == "worker"
        assert task["description"] == "Test task description"
        assert task["id"] == "legacy-task"
        assert task["title"] == "Legacy Task"
        assert task["priority"] == "P1"
        assert task["depends"] == []

    def test_parse_legacy_task_with_dependencies(self):
        """Test parsing legacy task with dependencies."""
        content = """TASK(worker: "Task")
Task Input:
**ID:** task-id
**Title:** Task Title
**Priority:** P2
**Depends:** dep-1, dep-2
"""
        task = parse_legacy_task(content)
        assert task["depends"] == ["dep-1", "dep-2"]

    def test_parse_legacy_task_with_steps(self):
        """Test parsing legacy task with steps."""
        content = """TASK(worker: "Task")
Task Input:
**ID:** task-id
**Title:** Task Title
**Priority:** P1
**Depends:** none

### Steps to Complete
1. First step
2. Second step
3. Third step
"""
        task = parse_legacy_task(content)
        assert "steps" in task
        assert len(task["steps"]) == 3

    def test_parse_legacy_task_minimal(self):
        """Test parsing minimal legacy task."""
        content = """TASK(flash: "Quick task")
Task Input:
"""
        task = parse_legacy_task(content)
        assert task["subagent_type"] == "flash"
        assert task["description"] == "Quick task"


class TestParseTaskFile:
    """Tests for parse_task_file function."""

    def test_parse_task_file_yaml_frontmatter(self, tmp_path: Path):
        """Test parsing task file with YAML frontmatter."""
        task_file = tmp_path / "test-task.md"
        task_file.write_text("""---
id: test-task
title: Test Task
subagent_type: worker
priority: P1
depends: []
---
## Description
Test task description
""")
        task = parse_task_file(task_file)
        assert task["id"] == "test-task"
        assert task["title"] == "Test Task"
        assert task["subagent_type"] == "worker"
        assert task["priority"] == "P1"
        assert task["depends"] == []

    def test_parse_task_file_json(self, tmp_path: Path):
        """Test parsing task file with JSON content."""
        task_file = tmp_path / "task.json"
        task_file.write_text(
            json.dumps(
                {
                    "id": "json-task",
                    "title": "JSON Task",
                    "subagent_type": "worker",
                    "priority": "P1",
                }
            )
        )
        task = parse_task_file(task_file)
        assert task["id"] == "json-task"
        assert task["title"] == "JSON Task"

    def test_parse_task_file_with_markdown_sections(self, tmp_path: Path):
        """Test parsing task file with markdown sections extracted."""
        task_file = tmp_path / "task.md"
        task_file.write_text("""---
id: test-task
title: Test Task
subagent_type: worker
priority: P1
---
## Implementation Details
Some implementation details here.

## Steps
1. First step
2. Second step
""")
        task = parse_task_file(task_file)
        assert task["id"] == "test-task"
        assert "implementation_details" in task
        assert "steps" in task

    def test_parse_task_file_nonexistent(self, tmp_path: Path):
        """Test parsing non-existent file raises ValueError."""
        task_file = tmp_path / "nonexistent.md"
        with pytest.raises(ValueError, match="Unknown task format"):
            parse_task_file(task_file)

    def test_parse_task_file_legacy_format(self, tmp_path: Path):
        """Test parsing task file with legacy format."""
        task_file = tmp_path / "legacy.task"
        task_file.write_text("""TASK(worker: "Legacy task")
Task Input:
**ID:** legacy-task
**Title:** Legacy Task
**Priority:** P1
**Depends:** none
""")
        task = parse_task_file(task_file)
        assert task["id"] == "legacy-task"
        assert task["subagent_type"] == "worker"

    def test_parse_task_file_unknown_format(self, tmp_path: Path):
        """Test parsing file with unknown format raises ValueError."""
        task_file = tmp_path / "unknown.txt"
        task_file.write_text("""Just some random content
without any recognized format
""")
        with pytest.raises(ValueError, match="Unknown task format"):
            parse_task_file(task_file)

    def test_parse_task_file_with_special_chars_in_id(self, tmp_path: Path):
        """Test parsing task file with special characters in ID."""
        task_file = tmp_path / "special.md"
        task_file.write_text("""---
id: task-with-special-chars
title: Special Task
subagent_type: worker
priority: P1
---
""")
        task = parse_task_file(task_file)
        assert task["id"] == "task-with-special-chars"

    def test_parse_task_file_encoding(self, tmp_path: Path):
        """Test parsing task file with UTF-8 encoding."""
        task_file = tmp_path / "unicode.md"
        task_file.write_text("""---
id: unicode-task
title: Task with émojis 🎉
subagent_type: worker
priority: P1
---
## Description
Testing unicode: café, Ñ, 中文
""")
        task = parse_task_file(task_file)
        assert task["id"] == "unicode-task"
        assert "émojis" in task["title"]
