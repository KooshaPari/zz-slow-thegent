"""Tests for thegent.models.task_io Pydantic schemas.

Covers:
- TaskInput validation (required fields, optional fields, extra-allow)
- TaskOutput validation (required fields, types, extra-allow)
- TaskError validation (required fields, retriable semantics)
- TaskSpec validation (composition, optional fields, extra-allow)
- Serialization round-trips (model_dump / model_validate)
- Backward-compatibility invariants (extra fields preserved)

Requirement trace: FR-TASK-IO-001
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from thegent.models.task_io import TaskError, TaskInput, TaskOutput, TaskSpec

# ---------------------------------------------------------------------------
# TaskInput
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskInput:
    """Unit tests for TaskInput model."""

    def test_minimal_valid_input(self) -> None:
        """Only 'task' is required; all other fields have defaults."""
        ti = TaskInput(task="do something")
        assert ti.task == "do something"
        assert ti.context == {}
        assert ti.max_tokens is None
        assert ti.temperature is None
        assert ti.tools == []

    def test_full_valid_input(self) -> None:
        """All fields populated and validated."""
        ti = TaskInput(
            task="implement feature X",
            context={"cwd": "/project", "session_id": "abc123"},
            max_tokens=4096,
            temperature=0.7,
            tools=["read_file", "write_file"],
        )
        assert ti.task == "implement feature X"
        assert ti.context["cwd"] == "/project"
        assert ti.max_tokens == 4096
        assert ti.temperature == 0.7
        assert ti.tools == ["read_file", "write_file"]

    def test_empty_task_raises(self) -> None:
        """Empty string for 'task' violates min_length=1."""
        with pytest.raises(ValidationError) as exc_info:
            TaskInput(task="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("task",) for e in errors)

    def test_missing_task_raises(self) -> None:
        """Omitting 'task' must raise ValidationError."""
        with pytest.raises(ValidationError):
            TaskInput.model_validate({})

    def test_temperature_out_of_range_raises(self) -> None:
        """temperature > 2.0 must fail validation."""
        with pytest.raises(ValidationError):
            TaskInput(task="t", temperature=2.5)

    def test_temperature_negative_raises(self) -> None:
        """temperature < 0.0 must fail validation."""
        with pytest.raises(ValidationError):
            TaskInput(task="t", temperature=-0.1)

    def test_max_tokens_zero_raises(self) -> None:
        """max_tokens < 1 must fail validation."""
        with pytest.raises(ValidationError):
            TaskInput(task="t", max_tokens=0)

    def test_extra_fields_preserved(self) -> None:
        """Extra fields are preserved (extra='allow') for forward compat."""
        data: dict[str, Any] = {
            "task": "t",
            "future_field": "value",
            "another_field": 42,
        }
        ti = TaskInput.model_validate(data)
        assert ti.model_extra is not None
        assert ti.model_extra.get("future_field") == "value"
        assert ti.model_extra.get("another_field") == 42

    def test_serialization_round_trip(self) -> None:
        """model_dump / model_validate round-trip preserves all values."""
        ti = TaskInput(task="round trip", max_tokens=1000, temperature=0.5)
        data = ti.model_dump()
        ti2 = TaskInput.model_validate(data)
        assert ti2.task == ti.task
        assert ti2.max_tokens == ti.max_tokens
        assert ti2.temperature == ti.temperature


# ---------------------------------------------------------------------------
# TaskOutput
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskOutput:
    """Unit tests for TaskOutput model."""

    def _valid_output(self, **overrides: Any) -> TaskOutput:
        defaults: dict[str, Any] = {
            "result": "Done.",
            "tokens_used": 512,
            "model": "claude-sonnet-4-5",
            "provider": "claude",
            "elapsed_ms": 1234.5,
        }
        defaults.update(overrides)
        return TaskOutput.model_validate(defaults)

    def test_minimal_valid_output(self) -> None:
        """All required fields present; tool_calls defaults to empty list."""
        to = self._valid_output()
        assert to.result == "Done."
        assert to.tokens_used == 512
        assert to.model == "claude-sonnet-4-5"
        assert to.provider == "claude"
        assert to.elapsed_ms == 1234.5
        assert to.tool_calls == []

    def test_with_tool_calls(self) -> None:
        """tool_calls accepts arbitrary list entries."""
        to = self._valid_output(tool_calls=[{"name": "read_file", "args": {}}])
        assert len(to.tool_calls) == 1
        assert to.tool_calls[0]["name"] == "read_file"

    def test_tokens_used_negative_raises(self) -> None:
        """Negative tokens_used must fail (ge=0)."""
        with pytest.raises(ValidationError):
            self._valid_output(tokens_used=-1)

    def test_elapsed_ms_negative_raises(self) -> None:
        """Negative elapsed_ms must fail (ge=0.0)."""
        with pytest.raises(ValidationError):
            self._valid_output(elapsed_ms=-1.0)

    def test_extra_fields_preserved(self) -> None:
        """Extra fields survive for forward compat."""
        to = self._valid_output(streaming=True, cost_usd=0.002)
        assert to.model_extra is not None
        assert to.model_extra.get("streaming") is True

    def test_serialization_round_trip(self) -> None:
        """Round-trip through model_dump / model_validate."""
        to = self._valid_output()
        data = to.model_dump()
        to2 = TaskOutput.model_validate(data)
        assert to2.result == to.result
        assert to2.elapsed_ms == to.elapsed_ms


# ---------------------------------------------------------------------------
# TaskError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskError:
    """Unit tests for TaskError model."""

    def test_retriable_error(self) -> None:
        """Transient API errors should be retriable."""
        err = TaskError(error_type="api_error", message="503 Service Unavailable", retriable=True)
        assert err.retriable is True
        assert err.error_type == "api_error"

    def test_non_retriable_error(self) -> None:
        """Policy denials should not be retriable."""
        err = TaskError(error_type="policy_deny", message="Denied by governance", retriable=False)
        assert err.retriable is False

    def test_missing_retriable_raises(self) -> None:
        """All three fields are required — omitting 'retriable' must raise."""
        with pytest.raises(ValidationError):
            TaskError.model_validate({"error_type": "timeout", "message": "Timed out"})

    def test_extra_fields_preserved(self) -> None:
        """Extra context fields (e.g. run_id) are preserved."""
        data: dict[str, Any] = {
            "error_type": "timeout",
            "message": "Timed out",
            "retriable": True,
            "run_id": "run_abc",
        }
        err = TaskError.model_validate(data)
        assert err.model_extra is not None
        assert err.model_extra.get("run_id") == "run_abc"

    def test_serialization_round_trip(self) -> None:
        """Round-trip through model_dump / model_validate."""
        err = TaskError(error_type="api_error", message="500", retriable=True)
        data = err.model_dump()
        err2 = TaskError.model_validate(data)
        assert err2.error_type == err.error_type
        assert err2.retriable == err.retriable


# ---------------------------------------------------------------------------
# TaskSpec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskSpec:
    """Unit tests for TaskSpec model."""

    def _valid_input(self) -> TaskInput:
        return TaskInput(task="implement X")

    def test_minimal_valid_spec(self) -> None:
        """Only 'input' is required; all other fields have defaults."""
        spec = TaskSpec(input=self._valid_input())
        assert spec.input.task == "implement X"
        assert spec.task_id is None
        assert spec.agent is None
        assert spec.model is None
        assert spec.lane == "standard"
        assert spec.priority is None
        assert spec.owner is None
        assert spec.correlation_id is None
        assert spec.idempotency_token is None

    def test_full_valid_spec(self) -> None:
        """All fields populated."""
        spec = TaskSpec(
            task_id="my-task-001",
            input=TaskInput(task="do work", max_tokens=2048),
            agent="worker",
            model="claude-sonnet-4-5",
            lane="critical",
            priority="P1",
            owner="agent-f2",
            correlation_id="corr-xyz",
            idempotency_token="idem-abc",
        )
        assert spec.task_id == "my-task-001"
        assert spec.input.max_tokens == 2048
        assert spec.lane == "critical"
        assert spec.priority == "P1"
        assert spec.owner == "agent-f2"

    def test_missing_input_raises(self) -> None:
        """'input' is required."""
        with pytest.raises(ValidationError):
            TaskSpec.model_validate({})

    def test_extra_fields_preserved(self) -> None:
        """Extra top-level fields are preserved."""
        data: dict[str, Any] = {"input": {"task": "implement X"}, "future_flag": True}
        spec = TaskSpec.model_validate(data)
        assert spec.model_extra is not None
        assert spec.model_extra.get("future_flag") is True

    def test_serialization_round_trip(self) -> None:
        """Round-trip through model_dump / model_validate."""
        spec = TaskSpec(
            task_id="rt-task",
            input=TaskInput(task="round trip", tools=["bash"]),
            lane="standard",
        )
        data = spec.model_dump()
        spec2 = TaskSpec.model_validate(data)
        assert spec2.task_id == spec.task_id
        assert spec2.input.task == spec.input.task
        assert spec2.input.tools == ["bash"]

    def test_nested_input_validation_bad_temperature(self) -> None:
        """Nested TaskInput validation propagates correctly."""
        with pytest.raises(ValidationError):
            TaskSpec.model_validate({"input": {"task": "x", "temperature": 99.9}})

    def test_nested_input_validation_empty_task(self) -> None:
        """Empty task string in nested input is rejected."""
        with pytest.raises(ValidationError):
            TaskSpec.model_validate({"input": {"task": ""}})

    def test_input_from_dict_coerced(self) -> None:
        """TaskSpec accepts dict for 'input' (Pydantic coercion)."""
        spec = TaskSpec.model_validate({"input": {"task": "coerced from dict"}})
        assert isinstance(spec.input, TaskInput)
        assert spec.input.task == "coerced from dict"
