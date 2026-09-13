# task_io API Reference

> **Source**: `src/thegent/models/task_io.py`

Pydantic schemas for task input/output validation and documentation.

These models provide structured, type-safe representations of task I/O,
replacing the loosely-typed dicts used across the execution pipeline.

All models use `extra="allow"` for forward compatibility: unknown fields
are preserved rather than rejected, so callers on older versions can still
communicate with newer agents that emit additional fields.

---

## TaskError

Structured error envelope for a failed task execution.

Provides machine-readable classification so orchestrators can decide
whether to retry, escalate, or abort.

**Inherits from**: `BaseModel`

---

## TaskInput

Structured input for a single agent task execution.

Replaces ad-hoc `dict[str, Any]` payloads passed to run_impl and
related call sites. All fields beyond `task` are optional to ensure
backward compatibility with existing callers.

**Inherits from**: `BaseModel`

---

## TaskOutput

Structured output from a completed agent task execution.

Captures both the textual result and key execution telemetry in a
single, validated envelope.

**Inherits from**: `BaseModel`

---

## TaskSpec

Full task specification combining structured input with execution metadata.

Intended as the canonical envelope passed into the orchestration layer.
The `input` field carries the validated TaskInput; remaining fields
capture routing and governance metadata that travels alongside the task.

**Inherits from**: `BaseModel`

---
