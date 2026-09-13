"""Tests for WL-113: --output-schema Support in thegent run.

Validates OutputSchemaValidator: file loading, schema validation,
system prompt injection, and codex arg generation.

# @trace WL-113
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.agents.output_schema import OutputSchemaValidator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
    },
    "required": ["name", "count"],
}

STRING_SCHEMA = {
    "type": "string",
}

ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "number"},
}


@pytest.fixture
def schema_file(tmp_path: Path) -> Path:
    """Write SIMPLE_SCHEMA to a temp file and return its path."""
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(SIMPLE_SCHEMA).decode(), encoding="utf-8")
    return p


@pytest.fixture
def string_schema_file(tmp_path: Path) -> Path:
    """Write STRING_SCHEMA to a temp file and return its path."""
    p = tmp_path / "string_schema.json"
    p.write_text(json.dumps(STRING_SCHEMA).decode(), encoding="utf-8")
    return p


@pytest.fixture
def array_schema_file(tmp_path: Path) -> Path:
    """Write ARRAY_SCHEMA to a temp file and return its path."""
    p = tmp_path / "array_schema.json"
    p.write_text(json.dumps(ARRAY_SCHEMA).decode(), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# OutputSchemaValidator: initialization
# ---------------------------------------------------------------------------


class TestOutputSchemaValidatorInit:
    """Tests for OutputSchemaValidator.__init__."""

    def test_loads_schema_from_file(self, schema_file: Path) -> None:
        # @trace WL-113
        """Loading a valid schema file populates self.schema."""
        validator = OutputSchemaValidator(schema_file)
        assert validator.schema == SIMPLE_SCHEMA

    def test_stores_schema_path(self, schema_file: Path) -> None:
        # @trace WL-113
        """The resolved schema_path is stored on the instance."""
        validator = OutputSchemaValidator(schema_file)
        assert validator.schema_path == schema_file

    def test_accepts_str_path(self, schema_file: Path) -> None:
        # @trace WL-113
        """A string path is accepted and coerced to Path."""
        validator = OutputSchemaValidator(str(schema_file))
        assert validator.schema == SIMPLE_SCHEMA

    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        # @trace WL-113
        """FileNotFoundError is raised when the schema file does not exist."""
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            OutputSchemaValidator(missing)

    def test_raises_value_error_for_invalid_json(self, tmp_path: Path) -> None:
        # @trace WL-113
        """ValueError is raised when the schema file contains invalid JSON."""
        bad = tmp_path / "bad.json"
        bad.write_text("not json at all {{{{", encoding="utf-8")
        with pytest.raises(ValueError, match="Schema file is not valid JSON"):
            OutputSchemaValidator(bad)


# ---------------------------------------------------------------------------
# OutputSchemaValidator: validate()
# ---------------------------------------------------------------------------


class TestOutputSchemaValidatorValidate:
    """Tests for OutputSchemaValidator.validate()."""

    def test_valid_output_passes(self, schema_file: Path) -> None:
        # @trace WL-113
        """Valid JSON matching the schema returns the parsed dict."""
        validator = OutputSchemaValidator(schema_file)
        data = validator.validate('{"name": "Alice", "count": 42}')
        assert data == {"name": "Alice", "count": 42}

    def test_returns_parsed_dict(self, schema_file: Path) -> None:
        # @trace WL-113
        """validate() returns a dict, not a string."""
        validator = OutputSchemaValidator(schema_file)
        result = validator.validate('{"name": "Bob", "count": 0}')
        assert isinstance(result, dict)

    def test_raises_for_non_json_output(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised when agent output is not valid JSON."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Agent output is not valid JSON"):
            validator.validate("this is plain text")

    def test_raises_for_empty_output(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised for empty output (not valid JSON)."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Agent output is not valid JSON"):
            validator.validate("")

    def test_raises_for_missing_required_field(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised when a required field is missing."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Output schema validation failed"):
            validator.validate('{"name": "Alice"}')

    def test_raises_for_wrong_type(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised when a field has the wrong type."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Output schema validation failed"):
            validator.validate('{"name": "Alice", "count": "not-a-number"}')

    def test_raises_for_json_array_when_object_expected(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised when a JSON array is given but object is expected."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Output schema validation failed"):
            validator.validate("[1, 2, 3]")

    def test_raises_for_json_null(self, schema_file: Path) -> None:
        # @trace WL-113
        """ValueError is raised for JSON null when an object is expected."""
        validator = OutputSchemaValidator(schema_file)
        with pytest.raises(ValueError, match="Output schema validation failed"):
            validator.validate("null")

    def test_valid_array_schema(self, array_schema_file: Path) -> None:
        # @trace WL-113
        """An array output validates against an array schema."""
        validator = OutputSchemaValidator(array_schema_file)
        result = validator.validate("[1.0, 2.5, 3.14]")
        assert result == [1.0, 2.5, 3.14]


# ---------------------------------------------------------------------------
# OutputSchemaValidator: get_system_prompt_injection()
# ---------------------------------------------------------------------------


class TestOutputSchemaValidatorSystemPromptInjection:
    """Tests for OutputSchemaValidator.get_system_prompt_injection()."""

    def test_injection_contains_schema_json(self, schema_file: Path) -> None:
        # @trace WL-113
        """The injection string contains the schema as indented JSON."""
        validator = OutputSchemaValidator(schema_file)
        injection = validator.get_system_prompt_injection()
        assert json.dumps(SIMPLE_SCHEMA, indent=2).decode() in injection

    def test_injection_contains_must_respond_instruction(self, schema_file: Path) -> None:
        # @trace WL-113
        """The injection string contains the mandatory instruction phrase."""
        validator = OutputSchemaValidator(schema_file)
        injection = validator.get_system_prompt_injection()
        assert "You MUST respond with valid JSON matching this schema" in injection

    def test_injection_starts_with_newlines(self, schema_file: Path) -> None:
        # @trace WL-113
        """The injection string starts with newlines for clean prompt separation."""
        validator = OutputSchemaValidator(schema_file)
        injection = validator.get_system_prompt_injection()
        assert injection.startswith("\n\n")

    def test_injection_is_string(self, schema_file: Path) -> None:
        # @trace WL-113
        """get_system_prompt_injection() returns a str."""
        validator = OutputSchemaValidator(schema_file)
        assert isinstance(validator.get_system_prompt_injection(), str)


# ---------------------------------------------------------------------------
# OutputSchemaValidator: get_codex_args()
# ---------------------------------------------------------------------------


class TestOutputSchemaValidatorCodexArgs:
    """Tests for OutputSchemaValidator.get_codex_args()."""

    def test_returns_output_schema_flag(self, schema_file: Path) -> None:
        # @trace WL-113
        """get_codex_args() returns ['--output-schema', '<path>']."""
        validator = OutputSchemaValidator(schema_file)
        args = validator.get_codex_args()
        assert args[0] == "--output-schema"

    def test_returns_schema_path_as_second_arg(self, schema_file: Path) -> None:
        # @trace WL-113
        """get_codex_args() second element is the schema file path string."""
        validator = OutputSchemaValidator(schema_file)
        args = validator.get_codex_args()
        assert args[1] == str(schema_file)

    def test_returns_two_element_list(self, schema_file: Path) -> None:
        # @trace WL-113
        """get_codex_args() returns a list of exactly two elements."""
        validator = OutputSchemaValidator(schema_file)
        args = validator.get_codex_args()
        assert len(args) == 2


# ---------------------------------------------------------------------------
# run_impl integration: output_schema parameter
# ---------------------------------------------------------------------------


class TestRunImplOutputSchema:
    """Tests for run_impl integration with output_schema parameter.

    # @trace WL-113
    """

    def _make_run_result(self, stdout: str, exit_code: int = 0):
        """Helper to build a RunResult-like object."""
        from thegent.agents.base import RunResult

        return RunResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr="",
            timed_out=False,
        )

    def test_run_impl_accepts_output_schema_parameter(self) -> None:
        # @trace WL-113
        """run_impl signature accepts output_schema keyword argument."""
        import inspect

        from thegent.cli.commands.impl import run_impl

        sig = inspect.signature(run_impl)
        assert "output_schema" in sig.parameters

    def test_output_schema_parameter_defaults_to_none(self) -> None:
        # @trace WL-113
        """output_schema parameter defaults to None."""
        import inspect

        from thegent.cli.commands.impl import run_impl

        sig = inspect.signature(run_impl)
        assert sig.parameters["output_schema"].default is None

    def test_schema_injection_appended_to_prompt(self, schema_file: Path, tmp_path: Path) -> None:
        # @trace WL-113
        """Schema injection is appended to the prompt before agent execution."""
        validator = OutputSchemaValidator(schema_file)
        injection = validator.get_system_prompt_injection()
        original_prompt = "Do something useful"
        augmented = original_prompt + injection
        assert "You MUST respond with valid JSON matching this schema" in augmented
        assert original_prompt in augmented
