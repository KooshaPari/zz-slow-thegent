"""Output parser for extracting structured data from model outputs."""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass
from typing import Any

OUTPUT_PARSER_SCHEMA_VERSION = "1.0.0"
PARSE_EMPTY = ""
PARSE_OK = "ok"
PARSE_TRUNCATED = "truncated"


@dataclass
class ParseResult:
    """Result of parsing output."""

    success: bool
    data: dict[str, Any] | None = None
    error: str = ""


def condense_stream_to_display(stream_data: str) -> str:
    """Condense stream data to display format."""
    if not stream_data or not stream_data.strip():
        return ""

    lines = stream_data.strip().split("\n")
    result_parts = []

    for line in lines:
        try:
            obj = json.loads(line)
            if obj.get("type") == "message":
                role = obj.get("role", "")
                content = obj.get("content", "")
                if role == "assistant":
                    if content:
                        result_parts.append(content)
                elif role == "user":
                    result_parts.append(f"User answered: {content}")
            elif obj.get("type") == "tool_use":
                tool_name = obj.get("tool_name", "unknown")
                result_parts.append(f"Tool: {tool_name}")
        except json.JSONDecodeError:
            if line.strip() and not line.startswith("{"):
                result_parts.append(line)

    return "\n".join(result_parts)


def extract_condensed(raw: str) -> str:
    """Extract condensed output from raw model output."""
    if not raw or not raw.strip():
        return ""

    # Try to parse as JSON lines
    if raw.strip().startswith("{"):
        return condense_stream_to_display(raw)

    # Return raw if no structured format detected
    return raw.strip()


def extract_condensed_structured(
    raw: str, schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Extract structured data from condensed output.

    Args:
        raw: Raw model output
        schema: Optional schema to validate against

    Returns:
        Extracted structured data
    """
    result: dict[str, Any] = {
        "text": raw,
        "schema_version": OUTPUT_PARSER_SCHEMA_VERSION,
    }

    # Try to extract JSON from the raw output
    json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if json_match:
        with contextlib.suppress(json.JSONDecodeError):
            result["parsed"] = json.loads(json_match.group(0))

    return result


def extract_condensed_validated(raw: str, schema: dict[str, Any]) -> ParseResult:
    """Extract and validate condensed output against a schema.

    Args:
        raw: Raw model output
        schema: Schema to validate against

    Returns:
        ParseResult with validation status
    """
    if not raw or not raw.strip():
        return ParseResult(success=False, error="Empty input")

    try:
        data = extract_condensed_structured(raw, schema)

        # Basic validation
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                return ParseResult(
                    success=False, error=f"Missing required field: {field}"
                )

        return ParseResult(success=True, data=data)
    except Exception as e:
        return ParseResult(success=False, error=str(e))


__all__ = [
    "OUTPUT_PARSER_SCHEMA_VERSION",
    "PARSE_EMPTY",
    "PARSE_OK",
    "PARSE_TRUNCATED",
    "ParseResult",
    "condense_stream_to_display",
    "extract_condensed",
    "extract_condensed_structured",
    "extract_condensed_validated",
]
