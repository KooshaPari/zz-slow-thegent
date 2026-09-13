"""Task parser module for thegent."""

import json
import re
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "parse_yaml_frontmatter",
    "parse_task_file",
    "detect_task_format",
    "extract_markdown_sections",
    "parse_legacy_task",
]


def parse_yaml_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, markdown_body)

    Raises:
        ValueError: If frontmatter is invalid or missing
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        pattern = r'^---\s*\n(.*?)\n---\s*(.*)$'
        match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise ValueError("No YAML frontmatter found")

    yaml_content = match.group(1)
    markdown_body = match.group(2)

    try:
        frontmatter = yaml.safe_load(yaml_content)
        if frontmatter is None:
            return {}, markdown_body
        if not isinstance(frontmatter, dict):
            raise ValueError("Frontmatter must be a dictionary")
        return frontmatter, markdown_body
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")


def detect_task_format(content: str) -> str:
    """Auto-detect task format."""
    if re.match(r'^---\s*\n', content):
        return 'yaml_frontmatter'
    if content.strip().startswith('{'):
        try:
            json.loads(content)
            return 'json'
        except Exception:
            pass
    if re.search(r'TASK\s*\(', content) or re.search(r'Task Input:', content):
        return 'legacy'
    return 'unknown'


def extract_markdown_sections(body: str) -> dict[str, str]:
    """Extract markdown sections by header."""
    sections = {}
    current_section = None
    current_content = []

    for line in body.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip().lower().replace(' ', '_')
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def parse_legacy_task(content: str) -> dict[str, Any]:
    """Parse legacy task format (backward compatibility)."""
    task: dict[str, Any] = {}

    task_match = re.search(r'TASK\s*\(([^:]+):\s*"([^"]+)"\)', content)
    if task_match:
        task['subagent_type'] = task_match.group(1).strip()
        task['description'] = task_match.group(2).strip()

    input_match = re.search(r'Task Input:\s*\n(.*?)(?=Task Output:|$)', content, re.DOTALL)
    if input_match:
        input_content = input_match.group(1)

        subagent_match = re.search(r'Subagent Type:\s*(.+)', input_content)
        if subagent_match:
            task['subagent_type'] = subagent_match.group(1).strip()

        prompt_match = re.search(r'Prompt:\s*\n(.*)', input_content, re.DOTALL)
        if prompt_match:
            prompt_content = prompt_match.group(1)

            id_match = re.search(r'\*\*ID:\*\*\s*(.+)', prompt_content)
            if id_match:
                task['id'] = id_match.group(1).strip()

            title_match = re.search(r'\*\*Title:\*\*\s*(.+)', prompt_content)
            if title_match:
                task['title'] = title_match.group(1).strip()

            priority_match = re.search(r'\*\*Priority:\*\*\s*(P[123])', prompt_content)
            if priority_match:
                task['priority'] = priority_match.group(1)

            depends_match = re.search(r'\*\*Depends:\*\*\s*(.+)', prompt_content)
            if depends_match:
                depends_str = depends_match.group(1).strip()
                if depends_str.lower() in ['none', '-', '']:
                    task['depends'] = []
                else:
                    task['depends'] = [d.strip() for d in depends_str.split(',')]

            impl_match = re.search(
                r'### Implementation Details\s*\n(.*?)(?=###|$)', prompt_content, re.DOTALL
            )
            if impl_match:
                task['implementation_details'] = impl_match.group(1).strip()

            steps_match = re.search(
                r'### Steps to Complete\s*\n(.*?)(?=###|$)', prompt_content, re.DOTALL
            )
            if steps_match:
                steps_content = steps_match.group(1)
                steps = []
                step_pattern = r'(\d+)\.\s+(.+)'
                for step_match in re.finditer(step_pattern, steps_content):
                    steps.append({
                        'number': int(step_match.group(1)),
                        'description': step_match.group(2).strip()
                    })
                if steps:
                    task['steps'] = steps

            deliverables_match = re.search(
                r'### Deliverables\s*\n(.*?)(?=###|$)', prompt_content, re.DOTALL
            )
            if deliverables_match:
                deliverables_content = deliverables_match.group(1)
                task['deliverables'] = [
                    d.strip() for d in deliverables_content.split('\n')
                    if d.strip() and not d.strip().startswith('-')
                ]

    return task


def parse_task_file(file_path: Path) -> dict[str, Any]:
    """Parse a task file (auto-detects format).

    Args:
        file_path: Path to task file

    Returns:
        Parsed task dictionary

    Raises:
        ValueError: If file cannot be parsed
    """
    content = file_path.read_text(encoding='utf-8')
    format_type = detect_task_format(content)

    if format_type == 'yaml_frontmatter':
        frontmatter, body = parse_yaml_frontmatter(content)
        sections = extract_markdown_sections(body)
        task: dict[str, Any] = {**frontmatter, **sections}
        return task
    elif format_type == 'legacy':
        return parse_legacy_task(content)
    elif format_type == 'json':
        return json.loads(content)
    else:
        raise ValueError(f"Unknown task format: {format_type}")
