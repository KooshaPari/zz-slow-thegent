"""Tests for task validator."""

from pathlib import Path

from thegent.task.validator import (
    ValidationError,
    ValidationResult,
    validate_task,
    validate_task_file,
)


class TestValidateTask:
    """Tests for validate_task function."""

    def test_validate_task_valid_minimal(self):
        """Test validation of minimal valid task."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_task_valid_complete(self):
        """Test validation of complete valid task."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P2",
            "depends": ["dep-1", "dep-2"],
            "description": "A description",
            "source": "TEST.md",
            "steps": [{"number": 1, "description": "Step 1"}],
            "deliverables": ["Deliverable 1"],
            "metadata": {
                "estimated_hours": 4,
                "complexity": "moderate",
                "tags": ["test", "validation"],
            },
        }
        result = validate_task(task)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_task_missing_all_required(self):
        """Test validation of task with all required fields missing."""
        task = {}
        result = validate_task(task)
        assert not result.valid
        assert len(result.errors) == 4
        error_fields = {e.field for e in result.errors}
        assert error_fields == {"id", "title", "subagent_type", "priority"}

    def test_validate_task_missing_single_required(self):
        """Test validation of task with single required field missing."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
        }
        result = validate_task(task)
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].field == "priority"

    def test_validate_task_id_uppercase(self):
        """Test validation of task with uppercase ID."""
        task = {
            "id": "INVALID_ID",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "id" in e.field.lower() and "format" in e.code for e in result.errors
        )

    def test_validate_task_id_with_underscores(self):
        """Test validation of task with underscores in ID."""
        task = {
            "id": "invalid_id",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() for e in result.errors)

    def test_validate_task_id_with_spaces(self):
        """Test validation of task with spaces in ID."""
        task = {
            "id": "invalid id",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() for e in result.errors)

    def test_validate_task_id_too_short(self):
        """Test validation of task with too short ID."""
        task = {
            "id": "ab",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() and "min" in e.code for e in result.errors)

    def test_validate_task_id_too_long(self):
        """Test validation of task with too long ID."""
        task = {
            "id": "a" * 101,
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() and "max" in e.code for e in result.errors)

    def test_validate_task_id_not_string(self):
        """Test validation of task with non-string ID."""
        task = {
            "id": 123,
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() and "type" in e.code for e in result.errors)

    def test_validate_task_id_empty_string(self):
        """Test validation of task with empty string ID."""
        task = {
            "id": "",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("id" in e.field.lower() for e in result.errors)

    def test_validate_task_title_not_string(self):
        """Test validation of task with non-string title."""
        task = {
            "id": "test-task",
            "title": 123,
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "title" in e.field.lower() and "type" in e.code for e in result.errors
        )

    def test_validate_task_title_too_long(self):
        """Test validation of task with too long title."""
        task = {
            "id": "test-task",
            "title": "A" * 201,
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "title" in e.field.lower() and "max" in e.code for e in result.errors
        )

    def test_validate_task_priority_p1(self):
        """Test validation of task with P1 priority."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_priority_p2(self):
        """Test validation of task with P2 priority."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P2",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_priority_p3(self):
        """Test validation of task with P3 priority."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P3",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_priority_invalid(self):
        """Test validation of task with invalid priority."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P4",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "priority" in e.field.lower() and "enum" in e.code for e in result.errors
        )

    def test_validate_task_priority_invalid_zero(self):
        """Test validation of task with P0 priority."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P0",
        }
        result = validate_task(task)
        assert not result.valid

    def test_validate_task_subagent_type_worker(self):
        """Test validation of task with worker subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_subagent_type_flash(self):
        """Test validation of task with flash subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "flash",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_subagent_type_researcher(self):
        """Test validation of task with researcher subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "researcher",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_subagent_type_reviewer(self):
        """Test validation of task with reviewer subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "reviewer",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_subagent_type_planner(self):
        """Test validation of task with planner subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "planner",
            "priority": "P1",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_subagent_type_invalid(self):
        """Test validation of task with invalid subagent type."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "invalid-agent",
            "priority": "P1",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "subagent_type" in e.field.lower() and "enum" in e.code
            for e in result.errors
        )

    def test_validate_task_depends_empty_list(self):
        """Test validation of task with empty depends list."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "depends": [],
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_depends_valid(self):
        """Test validation of task with valid dependencies."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "depends": ["dep-1", "another-dep"],
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_depends_invalid_format(self):
        """Test validation of task with invalid dependency format."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "depends": ["INVALID_DEP"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("depends" in e.field.lower() for e in result.errors)

    def test_validate_task_depends_not_list(self):
        """Test validation of task with non-list depends."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "depends": "not-a-list",
        }
        result = validate_task(task)
        assert not result.valid
        assert any(
            "depends" in e.field.lower() and "type" in e.code for e in result.errors
        )

    def test_validate_task_depends_item_not_string(self):
        """Test validation of task with non-string dependency item."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "depends": [123],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("depends" in e.field.lower() for e in result.errors)


class TestValidateTaskWorker:
    """Tests for worker task validation."""

    def test_validate_task_worker_with_steps_and_deliverables(self):
        """Test validation of worker task with steps and deliverables."""
        task = {
            "id": "worker-task",
            "title": "Worker Task",
            "subagent_type": "worker",
            "priority": "P1",
            "steps": [{"number": 1, "description": "Step 1"}],
            "deliverables": ["Deliverable 1"],
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_worker_missing_steps(self):
        """Test validation of worker task missing steps."""
        task = {
            "id": "worker-task",
            "title": "Worker Task",
            "subagent_type": "worker",
            "priority": "P1",
            "deliverables": ["Deliverable 1"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("steps" in e.field.lower() for e in result.errors)

    def test_validate_task_worker_missing_deliverables(self):
        """Test validation of worker task missing deliverables."""
        task = {
            "id": "worker-task",
            "title": "Worker Task",
            "subagent_type": "worker",
            "priority": "P1",
            "steps": [{"number": 1, "description": "Step 1"}],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("deliverables" in e.field.lower() for e in result.errors)

    def test_validate_task_worker_empty_steps(self):
        """Test validation of worker task with empty steps list."""
        task = {
            "id": "worker-task",
            "title": "Worker Task",
            "subagent_type": "worker",
            "priority": "P1",
            "steps": [],
            "deliverables": ["Deliverable 1"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("steps" in e.field.lower() for e in result.errors)

    def test_validate_task_worker_empty_deliverables(self):
        """Test validation of worker task with empty deliverables list."""
        task = {
            "id": "worker-task",
            "title": "Worker Task",
            "subagent_type": "worker",
            "priority": "P1",
            "steps": [{"number": 1, "description": "Step 1"}],
            "deliverables": [],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("deliverables" in e.field.lower() for e in result.errors)


class TestValidateTaskResearcher:
    """Tests for researcher task validation."""

    def test_validate_task_researcher_valid(self):
        """Test validation of valid researcher task."""
        task = {
            "id": "research-task",
            "title": "Research Task",
            "subagent_type": "researcher",
            "priority": "P1",
            "research_questions": ["Question 1?"],
            "expected_outcomes": ["Outcome 1"],
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_researcher_missing_research_questions(self):
        """Test validation of researcher task missing research questions."""
        task = {
            "id": "research-task",
            "title": "Research Task",
            "subagent_type": "researcher",
            "priority": "P1",
            "expected_outcomes": ["Outcome 1"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("research_questions" in e.field.lower() for e in result.errors)

    def test_validate_task_researcher_missing_expected_outcomes(self):
        """Test validation of researcher task missing expected outcomes."""
        task = {
            "id": "research-task",
            "title": "Research Task",
            "subagent_type": "researcher",
            "priority": "P1",
            "research_questions": ["Question 1?"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("expected_outcomes" in e.field.lower() for e in result.errors)

    def test_validate_task_researcher_empty_research_questions(self):
        """Test validation of researcher task with empty research questions."""
        task = {
            "id": "research-task",
            "title": "Research Task",
            "subagent_type": "researcher",
            "priority": "P1",
            "research_questions": [],
            "expected_outcomes": ["Outcome 1"],
        }
        result = validate_task(task)
        assert not result.valid

    def test_validate_task_researcher_empty_expected_outcomes(self):
        """Test validation of researcher task with empty expected outcomes."""
        task = {
            "id": "research-task",
            "title": "Research Task",
            "subagent_type": "researcher",
            "priority": "P1",
            "research_questions": ["Question 1?"],
            "expected_outcomes": [],
        }
        result = validate_task(task)
        assert not result.valid


class TestValidateTaskReviewer:
    """Tests for reviewer task validation."""

    def test_validate_task_reviewer_valid(self):
        """Test validation of valid reviewer task."""
        task = {
            "id": "review-task",
            "title": "Review Task",
            "subagent_type": "reviewer",
            "priority": "P1",
            "review_criteria": ["Criterion 1"],
            "files_to_review": ["file1.py"],
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_reviewer_missing_review_criteria(self):
        """Test validation of reviewer task missing review criteria."""
        task = {
            "id": "review-task",
            "title": "Review Task",
            "subagent_type": "reviewer",
            "priority": "P1",
            "files_to_review": ["file1.py"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("review_criteria" in e.field.lower() for e in result.errors)

    def test_validate_task_reviewer_missing_files_to_review(self):
        """Test validation of reviewer task missing files to review."""
        task = {
            "id": "review-task",
            "title": "Review Task",
            "subagent_type": "reviewer",
            "priority": "P1",
            "review_criteria": ["Criterion 1"],
        }
        result = validate_task(task)
        assert not result.valid
        assert any("files_to_review" in e.field.lower() for e in result.errors)


class TestValidateTaskVisibility:
    """Tests for visibility validation."""

    def test_validate_task_visibility_public(self):
        """Test validation of public visibility task."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "visibility": "public",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_visibility_private(self):
        """Test validation of private visibility task."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "visibility": "private",
        }
        result = validate_task(task)
        assert result.valid

    def test_validate_task_visibility_restricted_without_agents(self):
        """Test validation of restricted visibility without allowed agents."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "visibility": "restricted",
        }
        result = validate_task(task)
        assert not result.valid
        assert any("allowed_agents" in e.field.lower() for e in result.errors)

    def test_validate_task_visibility_restricted_with_agents(self):
        """Test validation of restricted visibility with allowed agents."""
        task = {
            "id": "test-task",
            "title": "Test Task",
            "subagent_type": "worker",
            "priority": "P1",
            "visibility": "restricted",
            "allowed_agents": ["agent-1", "agent-2"],
        }
        result = validate_task(task)
        assert result.valid


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_validation_result_format_errors(self):
        """Test formatting errors in ValidationResult."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    field="id",
                    message="Invalid ID",
                    code="invalid_format",
                    path=["id"],
                ),
                ValidationError(
                    field="priority",
                    message="Invalid priority",
                    code="enum",
                    path=["priority"],
                ),
            ],
        )
        formatted = result.format_errors()
        assert "id" in formatted
        assert "Invalid ID" in formatted
        assert "priority" in formatted
        assert "Invalid priority" in formatted

    def test_validation_result_format_errors_empty(self):
        """Test formatting errors when there are no errors."""
        result = ValidationResult(valid=True, errors=[], warnings=[])
        formatted = result.format_errors()
        assert formatted == ""

    def test_validation_result_format_errors_no_path(self):
        """Test formatting errors with empty path."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    field="file",
                    message="File error",
                    code="file_not_found",
                    path=[],
                ),
            ],
        )
        formatted = result.format_errors()
        assert "file" in formatted


class TestValidateTaskFile:
    """Tests for validate_task_file function."""

    def test_validate_task_file_valid(self, tmp_path: Path):
        """Test validating a valid task file."""
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
        result = validate_task_file(task_file)
        assert result.valid

    def test_validate_task_file_worker_with_steps(self, tmp_path: Path):
        """Test validating a worker task file with steps."""
        task_file = tmp_path / "worker-task.md"
        task_file.write_text("""---
id: worker-task
title: Worker Task
subagent_type: worker
priority: P1
depends: []
steps:
  - number: 1
    description: Step 1
deliverables:
  - Deliverable 1
---
""")
        result = validate_task_file(task_file)
        assert result.valid

    def test_validate_task_file_missing(self, tmp_path: Path):
        """Test validating a non-existent task file."""
        task_file = tmp_path / "nonexistent.md"
        result = validate_task_file(task_file)
        assert not result.valid
        assert len(result.errors) > 0
        assert any("file" in e.field.lower() for e in result.errors)

    def test_validate_task_file_invalid_frontmatter(self, tmp_path: Path):
        """Test validating a file with invalid frontmatter."""
        task_file = tmp_path / "invalid.md"
        task_file.write_text("""---
id: test-task
invalid: yaml: syntax: error
---
""")
        result = validate_task_file(task_file)
        assert not result.valid

    def test_validate_task_file_no_frontmatter(self, tmp_path: Path):
        """Test validating a file without frontmatter."""
        task_file = tmp_path / "no-frontmatter.md"
        task_file.write_text("""# Just a markdown file
Some content without frontmatter
""")
        result = validate_task_file(task_file)
        assert not result.valid
