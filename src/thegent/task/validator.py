"""Task validator module for thegent."""

import re
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any

__all__ = [
    "ValidationError",
    "ValidationResult",
    "validate_task",
    "validate_task_file",
]


@dataclass
class ValidationError:
    """Single validation error."""
    field: str
    message: str
    code: str
    path: list[str] = dataclass_field(default_factory=list)


@dataclass
class ValidationResult:
    """Task validation result."""
    valid: bool
    errors: list[ValidationError] = dataclass_field(default_factory=list)
    warnings: list[ValidationError] = dataclass_field(default_factory=list)

    def format_errors(self) -> str:
        """Format errors for display."""
        lines = []
        for error in self.errors:
            path_str = '.'.join(error.path) if error.path else error.field
            lines.append(f"{path_str}: {error.message} ({error.code})")
        return '\n'.join(lines)


VALID_PRIORITIES = {"P1", "P2", "P3"}
VALID_SUBAGENT_TYPES = {"worker", "flash", "researcher", "reviewer", "planner"}


def validate_task(task: dict[str, Any]) -> ValidationResult:
    """Validate a task dictionary.

    Args:
        task: Task dictionary to validate

    Returns:
        ValidationResult with validation status and any errors
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    required_fields = ["id", "title", "subagent_type", "priority"]
    for field_name in required_fields:
        if field_name not in task or not task[field_name]:
            errors.append(ValidationError(
                field=field_name,
                message=f"Required field '{field_name}' is missing or empty",
                code="required",
                path=[field_name]
            ))

    if "id" in task:
        task_id = task["id"]
        if not isinstance(task_id, str):
            errors.append(ValidationError(
                field="id",
                message=f"Task ID must be a string, got {type(task_id).__name__}",
                code="type",
                path=["id"]
            ))
        elif not re.match(r'^[a-z0-9-]+$', task_id):
            errors.append(ValidationError(
                field="id",
                message=f"Task ID must be lowercase alphanumeric with hyphens, got '{task_id}'",
                code="invalid_format",
                path=["id"]
            ))
        elif len(task_id) < 3:
            errors.append(ValidationError(
                field="id",
                message=f"Task ID must be at least 3 characters, got {len(task_id)}",
                code="min_length",
                path=["id"]
            ))
        elif len(task_id) > 100:
            errors.append(ValidationError(
                field="id",
                message=f"Task ID must be at most 100 characters, got {len(task_id)}",
                code="max_length",
                path=["id"]
            ))

    if "title" in task:
        title = task["title"]
        if not isinstance(title, str):
            errors.append(ValidationError(
                field="title",
                message=f"Title must be a string, got {type(title).__name__}",
                code="type",
                path=["title"]
            ))
        elif len(title) < 1:
            errors.append(ValidationError(
                field="title",
                message="Title must be at least 1 character",
                code="min_length",
                path=["title"]
            ))
        elif len(title) > 200:
            errors.append(ValidationError(
                field="title",
                message=f"Title must be at most 200 characters, got {len(title)}",
                code="max_length",
                path=["title"]
            ))

    if "priority" in task:
        priority = task["priority"]
        if priority not in VALID_PRIORITIES:
            errors.append(ValidationError(
                field="priority",
                message=f"Priority must be one of {sorted(VALID_PRIORITIES)}, got '{priority}'",
                code="enum",
                path=["priority"]
            ))

    if "subagent_type" in task:
        subagent_type = task["subagent_type"]
        if subagent_type not in VALID_SUBAGENT_TYPES:
            errors.append(ValidationError(
                field="subagent_type",
                message=f"Subagent type must be one of {sorted(VALID_SUBAGENT_TYPES)}, got '{subagent_type}'",
                code="enum",
                path=["subagent_type"]
            ))

    if "depends" in task:
        depends = task["depends"]
        if not isinstance(depends, list):
            errors.append(ValidationError(
                field="depends",
                message=f"Depends must be a list, got {type(depends).__name__}",
                code="type",
                path=["depends"]
            ))
        else:
            for i, dep in enumerate(depends):
                if not isinstance(dep, str):
                    errors.append(ValidationError(
                        field="depends",
                        message=f"Dependency at index {i} must be a string, got {type(dep).__name__}",
                        code="type",
                        path=["depends", str(i)]
                    ))
                elif not re.match(r'^[a-z0-9-]+$', dep):
                    errors.append(ValidationError(
                        field="depends",
                        message=f"Dependency '{dep}' must be lowercase alphanumeric with hyphens",
                        code="invalid_format",
                        path=["depends", str(i)]
                    ))

    subagent_type = task.get("subagent_type")
    if subagent_type == "worker":
        steps = task.get("steps", [])
        deliverables = task.get("deliverables", [])
        if not steps or len(steps) == 0:
            errors.append(ValidationError(
                field="steps",
                message="Worker tasks must have at least one step",
                code="min_items",
                path=["steps"]
            ))
        if not deliverables or len(deliverables) == 0:
            errors.append(ValidationError(
                field="deliverables",
                message="Worker tasks must have at least one deliverable",
                code="min_items",
                path=["deliverables"]
            ))

    if subagent_type == "researcher":
        research_questions = task.get("research_questions", [])
        expected_outcomes = task.get("expected_outcomes", [])
        if not research_questions or len(research_questions) == 0:
            errors.append(ValidationError(
                field="research_questions",
                message="Researcher tasks must have at least one research question",
                code="min_items",
                path=["research_questions"]
            ))
        if not expected_outcomes or len(expected_outcomes) == 0:
            errors.append(ValidationError(
                field="expected_outcomes",
                message="Researcher tasks must have at least one expected outcome",
                code="min_items",
                path=["expected_outcomes"]
            ))

    if subagent_type == "reviewer":
        review_criteria = task.get("review_criteria", [])
        files_to_review = task.get("files_to_review", [])
        if not review_criteria or len(review_criteria) == 0:
            errors.append(ValidationError(
                field="review_criteria",
                message="Reviewer tasks must have at least one review criterion",
                code="min_items",
                path=["review_criteria"]
            ))
        if not files_to_review or len(files_to_review) == 0:
            errors.append(ValidationError(
                field="files_to_review",
                message="Reviewer tasks must have at least one file to review",
                code="min_items",
                path=["files_to_review"]
            ))

    visibility = task.get("visibility")
    if visibility == "restricted":
        allowed_agents = task.get("allowed_agents", [])
        if not allowed_agents or len(allowed_agents) == 0:
            errors.append(ValidationError(
                field="allowed_agents",
                message="Restricted tasks must have at least one allowed agent",
                code="min_items",
                path=["allowed_agents"]
            ))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_task_file(file_path: Path) -> ValidationResult:
    """Validate a task file.

    Args:
        file_path: Path to task file

    Returns:
        ValidationResult with validation status and any errors
    """
    from thegent.task.parser import parse_task_file

    try:
        task = parse_task_file(file_path)
        return validate_task(task)
    except FileNotFoundError as e:
        return ValidationResult(
            valid=False,
            errors=[ValidationError(
                field='file',
                message=f"File not found: {e}",
                code='file_not_found',
                path=[]
            )],
            warnings=[]
        )
    except ValueError as e:
        return ValidationResult(
            valid=False,
            errors=[ValidationError(
                field='file',
                message=f"Failed to parse file: {e}",
                code='parse_error',
                path=[]
            )],
            warnings=[]
        )
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[ValidationError(
                field='file',
                message=f"Unexpected error: {e}",
                code='unknown_error',
                path=[]
            )],
            warnings=[]
        )
