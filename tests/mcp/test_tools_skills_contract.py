"""Contract tests for WL-111 MCP skill tool stubs."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import orjson as json
import pytest
from fastmcp.tools.tool import ToolResult

MODULE_PATH = Path(__file__).resolve().parents[2] / "src" / "thegent" / "mcp" / "server" / "tools_skills.py"
SPEC = importlib.util.spec_from_file_location("tools_skills", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

thegent_activate_skill_impl = MODULE.thegent_activate_skill_impl
thegent_list_skills_impl = MODULE.thegent_list_skills_impl


class _FakeBackend:
    def __init__(self) -> None:
        self._skills = [
            {"name": "alpha", "description": "a", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/a"},
            {"name": "beta", "description": "b", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/b"},
        ]
        self.activate_calls: list[str] = []

    def list_skills(self) -> list[dict[str, Any]]:
        return self._skills

    def activate_skill(self, skill_name: str) -> dict[str, Any] | None:
        self.activate_calls.append(skill_name)
        if skill_name == "alpha":
            return {"name": "alpha", "content": "# alpha"}
        return None


def _error_result(error: str, remediation: str, exit_code: int = 1, extra: dict[str, Any] | None = None) -> ToolResult:
    payload: dict[str, Any] = {"error": error, "remediation": remediation, "exit_code": exit_code}
    if extra:
        payload.update(extra)
    return ToolResult(content=json.dumps(payload).decode(), structured_content=payload, meta={"execution_time_ms": 0})


def test_list_skills_returns_structured_payload() -> None:
    result = thegent_list_skills_impl(backend=_FakeBackend())
    data = result.structured_content
    assert "skills" in data
    assert len(data["skills"]) == 2
    assert result.structured_content["skills"][0]["name"] == "alpha"


def test_list_skills_is_sorted_by_name() -> None:
    backend = _FakeBackend()
    backend._skills = [backend._skills[1], backend._skills[0]]
    result = thegent_list_skills_impl(backend=backend)
    names = [item["name"] for item in result.structured_content["skills"]]
    assert names == ["alpha", "beta"]


def test_list_skills_is_sorted_case_insensitively() -> None:
    backend = _FakeBackend()
    backend._skills = [
        {"name": "Zulu", "description": "z", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/z"},
        {"name": "alpha", "description": "a", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/a"},
        {"name": "Bravo", "description": "b", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/b"},
    ]
    result = thegent_list_skills_impl(backend=backend)
    names = [item["name"] for item in result.structured_content["skills"]]
    assert names == ["alpha", "Bravo", "Zulu"]


def test_list_skills_rejects_duplicate_names_case_insensitively() -> None:
    backend = _FakeBackend()
    backend._skills = [
        {"name": "Alpha", "description": "a", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/a"},
        {"name": "alpha", "description": "b", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/b"},
    ]
    with pytest.raises(ValueError) as exc:
        thegent_list_skills_impl(backend=backend)
    assert isinstance(exc.value, ValueError)
    assert "Duplicate skill name detected" in str(exc.value)


def test_list_skills_trims_names_in_output() -> None:
    backend = _FakeBackend()
    backend._skills = [
        {"name": "  Bravo  ", "description": "b", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/b"},
        {"name": " alpha ", "description": "a", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/a"},
    ]
    result = thegent_list_skills_impl(backend=backend)
    names = [item["name"] for item in result.structured_content["skills"]]
    assert names == ["alpha", "Bravo"]


def test_list_skills_rejects_duplicates_after_whitespace_trim() -> None:
    backend = _FakeBackend()
    backend._skills = [
        {"name": "Alpha ", "description": "a", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/a"},
        {"name": " alpha", "description": "b", "version": "1.0.0", "entrypoint": "thegent", "path": "/tmp/b"},
    ]
    with pytest.raises(ValueError) as exc:
        thegent_list_skills_impl(backend=backend)
    assert "Duplicate skill name detected" in str(exc.value)


def test_activate_skill_returns_payload_for_existing_skill() -> None:
    result = thegent_activate_skill_impl(skill_name="alpha", backend=_FakeBackend(), error_result_impl=_error_result)
    data = result.structured_content
    assert data["skill"]["name"] == "alpha"
    assert "content" in data["skill"]


def test_activate_skill_returns_error_for_missing_skill() -> None:
    result = thegent_activate_skill_impl(skill_name="missing", backend=_FakeBackend(), error_result_impl=_error_result)
    data = result.structured_content
    assert "error" in data
    assert data["skill_name"] == "missing"


def test_activate_skill_missing_error_uses_normalized_name() -> None:
    result = thegent_activate_skill_impl(
        skill_name="  missing  ", backend=_FakeBackend(), error_result_impl=_error_result
    )
    data = result.structured_content
    assert "error" in data
    assert data["skill_name"] == "missing"


def test_activate_skill_rejects_empty_name() -> None:
    result = thegent_activate_skill_impl(skill_name="   ", backend=_FakeBackend(), error_result_impl=_error_result)
    data = result.structured_content
    assert data["error"] == "skill_name must be non-empty"


def test_activate_skill_rejects_non_string_name() -> None:
    result = thegent_activate_skill_impl(skill_name=123, backend=_FakeBackend(), error_result_impl=_error_result)
    data = result.structured_content
    assert data["error"] == "skill_name must be a string"


def test_activate_skill_strips_whitespace_before_backend_call() -> None:
    backend = _FakeBackend()
    result = thegent_activate_skill_impl(skill_name="  alpha  ", backend=backend, error_result_impl=_error_result)
    data = result.structured_content
    assert backend.activate_calls == ["alpha"]
    assert data["skill"]["name"] == "alpha"


# noqa: PT018
