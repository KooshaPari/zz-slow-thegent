"""Package: thegent.task"""

from thegent.task.parser import (
    detect_task_format,
    extract_markdown_sections,
    parse_legacy_task,
    parse_task_file,
    parse_yaml_frontmatter,
)
from thegent.task.validator import (
    ValidationError,
    ValidationResult,
    validate_task,
    validate_task_file,
)

__all__ = [
    "parse_yaml_frontmatter",
    "parse_task_file",
    "detect_task_format",
    "extract_markdown_sections",
    "parse_legacy_task",
    "ValidationError",
    "ValidationResult",
    "validate_task",
    "validate_task_file",
]
