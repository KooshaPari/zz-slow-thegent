"""Tests for GW-52: JSON schema output validation guardrail.

# @trace FR-GUARD-052
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.guardrails.json_schema import (
    SchemaValidationResult,
    extract_llm_response_content,
    extract_response_schema,
    validate_json_output,
)

pytestmark = pytest.mark.requirement("FR-GUARD-052")

_SIMPLE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name"],
}


# ---------------------------------------------------------------------------
# validate_json_output
# ---------------------------------------------------------------------------


def test_validate_json_output_valid_json():
    result = validate_json_output('{"name": "Alice", "age": 30}', _SIMPLE_SCHEMA)
    assert isinstance(result, SchemaValidationResult)
    assert result.valid is True
    assert result.errors == []
    assert result.parsed == {"name": "Alice", "age": 30}


def test_validate_json_output_invalid_json():
    result = validate_json_output("not json at all {{{", _SIMPLE_SCHEMA)
    assert result.valid is False
    assert len(result.errors) > 0
    assert result.parsed is None


def test_validate_json_output_empty_string():
    result = validate_json_output("", _SIMPLE_SCHEMA)
    assert result.valid is False
    assert result.parsed is None
    assert len(result.errors) > 0


def test_validate_json_output_valid_array():
    schema = {"type": "array", "items": {"type": "number"}}
    result = validate_json_output("[1, 2, 3]", schema)
    assert result.valid is True
    assert result.parsed == [1, 2, 3]


# ---------------------------------------------------------------------------
# extract_response_schema
# ---------------------------------------------------------------------------


def test_extract_response_schema_json_schema_format():
    body = {
        "model": "gpt-4o",
        "response_format": {
            "type": "json_schema",
            "schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
        },
    }
    schema = extract_response_schema(body)
    assert schema is not None
    assert schema["type"] == "object"


def test_extract_response_schema_no_schema():
    body = {"model": "gpt-4o"}
    assert extract_response_schema(body) is None


def test_extract_response_schema_wrong_type():
    body = {"response_format": {"type": "json_object"}}
    assert extract_response_schema(body) is None


def test_extract_response_schema_missing_schema_key():
    body = {"response_format": {"type": "json_schema"}}
    assert extract_response_schema(body) is None


# ---------------------------------------------------------------------------
# extract_llm_response_content
# ---------------------------------------------------------------------------


def test_extract_llm_response_content():
    response = {"choices": [{"message": {"role": "assistant", "content": '{"name": "Bob"}'}}]}
    assert extract_llm_response_content(response) == '{"name": "Bob"}'


def test_extract_llm_response_content_empty():
    assert extract_llm_response_content({}) == ""


def test_extract_llm_response_content_missing_choices():
    assert extract_llm_response_content({"choices": []}) == ""


def test_extract_llm_response_content_none_content():
    response = {"choices": [{"message": {"content": None}}]}
    assert extract_llm_response_content(response) == ""
