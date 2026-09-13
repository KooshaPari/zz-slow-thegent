"""Unit tests for WL-091: SchemaVetterCheck, DiffSizeVetterCheck, SafetyVetterCheck.

All three new checks are added to src/thegent/govern/vetter/checks.py.
Key distinction from WL-090 checks:
  - SchemaVetterCheck uses Pydantic model_validate_json (not jsonschema).
  - DiffSizeVetterCheck uses max_lines_changed param (not max_lines).
  - SafetyVetterCheck is pure regex — no SemanticFirewall dependency.

Every test carries # @trace WL-091
"""

from __future__ import annotations

import asyncio

import orjson as json
from pydantic import BaseModel

from thegent.govern.vetter.checks import (
    DiffSizeVetterCheck,
    SafetyVetterCheck,
    SchemaVetterCheck,
)
from thegent.govern.vetter.models import VetterCheck, VetterCheckResult

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------


class _Item(BaseModel):
    name: str
    value: int


class _Nested(BaseModel):
    items: list[_Item]
    count: int


# ---------------------------------------------------------------------------
# SchemaVetterCheck — construction
# ---------------------------------------------------------------------------


def test_schema_vetter_check_name_default():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    assert check.name == "schema_vetter"


def test_schema_vetter_check_implements_protocol():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    assert isinstance(check, VetterCheck)


def test_schema_vetter_check_target_default_is_stdout():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    assert check.target == "stdout"


def test_schema_vetter_check_target_stderr():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="stderr")
    assert check.target == "stderr"


def test_schema_vetter_check_target_combined():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="combined")
    assert check.target == "combined"


# ---------------------------------------------------------------------------
# SchemaVetterCheck — stdout target (default)
# ---------------------------------------------------------------------------


def test_schema_vetter_check_passes_valid_stdout():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    payload = json.dumps({"name": "widget", "value": 42}).decode()
    result = asyncio.run(check.check("run-1", payload, {"stdout": payload, "stderr": ""}))
    assert result.passed is True
    assert result.check_name == "schema_vetter"


def test_schema_vetter_check_fails_invalid_json_stdout():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    bad = "not-json{{{"
    result = asyncio.run(check.check("run-1", bad, {"stdout": bad, "stderr": ""}))
    assert result.passed is False
    assert "JSON parse failed" in result.message


def test_schema_vetter_check_fails_schema_mismatch_stdout():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    # value is a string, not int
    payload = json.dumps({"name": "widget", "value": "not-an-int"}).decode()
    result = asyncio.run(check.check("run-1", payload, {"stdout": payload, "stderr": ""}))
    assert result.passed is False
    assert "Schema validation failed" in result.message


def test_schema_vetter_check_fails_missing_required_field():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    payload = json.dumps({"name": "widget"}).decode()  # missing 'value'
    result = asyncio.run(check.check("run-1", payload, {"stdout": payload, "stderr": ""}))
    assert result.passed is False
    assert "Schema validation failed" in result.message


# ---------------------------------------------------------------------------
# SchemaVetterCheck — stderr target
# ---------------------------------------------------------------------------


def test_schema_vetter_check_reads_stderr_when_target_is_stderr():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="stderr")
    stderr_payload = json.dumps({"name": "err-item", "value": 7}).decode()
    result = asyncio.run(check.check("run-2", "irrelevant-output", {"stdout": "irrelevant", "stderr": stderr_payload}))
    assert result.passed is True


def test_schema_vetter_check_fails_bad_stderr_json():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="stderr")
    result = asyncio.run(check.check("run-2", "out", {"stdout": "out", "stderr": "bad{"}))
    assert result.passed is False
    assert "JSON parse failed" in result.message


# ---------------------------------------------------------------------------
# SchemaVetterCheck — combined target
# ---------------------------------------------------------------------------


def test_schema_vetter_check_combined_concatenates_stdout_stderr():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="combined")
    # combined should concat stdout + stderr; the full JSON is in combined
    payload = json.dumps({"name": "combo", "value": 99}).decode()
    result = asyncio.run(check.check("run-3", "ignored", {"stdout": payload, "stderr": ""}))
    assert result.passed is True


def test_schema_vetter_check_combined_fails_invalid_combined():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item, target="combined")
    result = asyncio.run(check.check("run-3", "ignored", {"stdout": "bad", "stderr": "garbage"}))
    assert result.passed is False
    assert "JSON parse failed" in result.message


def test_schema_vetter_check_nested_model_passes():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Nested)
    payload = json.dumps({"items": [{"name": "a", "value": 1}], "count": 1}).decode()
    result = asyncio.run(check.check("run-4", payload, {"stdout": payload, "stderr": ""}))
    assert result.passed is True


def test_schema_vetter_check_nested_model_fails_wrong_type():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Nested)
    payload = json.dumps({"items": "not-a-list", "count": 1}).decode()
    result = asyncio.run(check.check("run-4", payload, {"stdout": payload, "stderr": ""}))
    assert result.passed is False
    assert "Schema validation failed" in result.message


def test_schema_vetter_check_result_is_vetter_check_result():
    # @trace WL-091
    check = SchemaVetterCheck(schema_model=_Item)
    payload = json.dumps({"name": "x", "value": 0}).decode()
    result = asyncio.run(check.check("run-5", payload, {"stdout": payload, "stderr": ""}))
    assert isinstance(result, VetterCheckResult)


# ---------------------------------------------------------------------------
# DiffSizeVetterCheck — construction
# ---------------------------------------------------------------------------


def test_diff_size_vetter_check_name_default():
    # @trace WL-091
    check = DiffSizeVetterCheck()
    assert check.name == "diff_size_vetter"


def test_diff_size_vetter_check_implements_protocol():
    # @trace WL-091
    check = DiffSizeVetterCheck()
    assert isinstance(check, VetterCheck)


def test_diff_size_vetter_check_default_max():
    # @trace WL-091
    check = DiffSizeVetterCheck()
    assert check.max_lines_changed == 500


def test_diff_size_vetter_check_custom_max():
    # @trace WL-091
    check = DiffSizeVetterCheck(max_lines_changed=100)
    assert check.max_lines_changed == 100


# ---------------------------------------------------------------------------
# DiffSizeVetterCheck — pass/fail
# ---------------------------------------------------------------------------


def test_diff_size_vetter_check_passes_small_diff():
    # @trace WL-091
    diff = "\n".join([f"+line{i}" for i in range(10)])
    check = DiffSizeVetterCheck(max_lines_changed=100)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.passed is True
    assert result.metadata["lines_changed"] == 10


def test_diff_size_vetter_check_fails_large_diff():
    # @trace WL-091
    diff = "\n".join([f"+line{i}" for i in range(600)])
    check = DiffSizeVetterCheck(max_lines_changed=500)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.passed is False
    assert "600" in result.message
    assert "500" in result.message


def test_diff_size_vetter_check_excludes_triple_plus_headers():
    # @trace WL-091
    diff = "--- a/file.py\n+++ b/file.py\n" + "\n".join([f"+line{i}" for i in range(5)])
    check = DiffSizeVetterCheck(max_lines_changed=100)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.passed is True
    assert result.metadata["lines_changed"] == 5


def test_diff_size_vetter_check_counts_removals_too():
    # @trace WL-091
    diff = "\n".join([f"-removed{i}" for i in range(10)] + [f"+added{i}" for i in range(5)])
    check = DiffSizeVetterCheck(max_lines_changed=100)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.metadata["lines_changed"] == 15


def test_diff_size_vetter_check_exact_boundary_passes():
    # @trace WL-091
    diff = "\n".join([f"+line{i}" for i in range(500)])
    check = DiffSizeVetterCheck(max_lines_changed=500)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.passed is True


def test_diff_size_vetter_check_one_over_boundary_fails():
    # @trace WL-091
    diff = "\n".join([f"+line{i}" for i in range(501)])
    check = DiffSizeVetterCheck(max_lines_changed=500)
    result = asyncio.run(check.check("run-1", diff, {}))
    assert result.passed is False


def test_diff_size_vetter_check_empty_diff_passes():
    # @trace WL-091
    check = DiffSizeVetterCheck(max_lines_changed=500)
    result = asyncio.run(check.check("run-1", "", {}))
    assert result.passed is True
    assert result.metadata["lines_changed"] == 0


# ---------------------------------------------------------------------------
# SafetyVetterCheck — construction
# ---------------------------------------------------------------------------


def test_safety_vetter_check_name_default():
    # @trace WL-091
    check = SafetyVetterCheck()
    assert check.name == "safety_vetter"


def test_safety_vetter_check_implements_protocol():
    # @trace WL-091
    check = SafetyVetterCheck()
    assert isinstance(check, VetterCheck)


# ---------------------------------------------------------------------------
# SafetyVetterCheck — clean output passes
# ---------------------------------------------------------------------------


def test_safety_vetter_check_passes_clean_output():
    # @trace WL-091
    check = SafetyVetterCheck()
    result = asyncio.run(check.check("run-1", "This is a normal output with no secrets.", {}))
    assert result.passed is True
    assert result.check_name == "safety_vetter"


# ---------------------------------------------------------------------------
# SafetyVetterCheck — bearer token detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_bearer_token():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123.sig"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "Secret pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — AWS key detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_aws_access_key():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "Secret pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — GitHub PAT detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_github_pat():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "token = ghp_ABCDEFGHIJKLMNOPabcdefghijklmn1234"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "Secret pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — sk- API key detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_sk_api_key():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "OPENAI_API_KEY=sk-abc123defABCDEF456789ghijklMNOP"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "Secret pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — PII: email detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_email():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "Contact the user at john.doe@example.com for details."
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "PII pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — PII: SSN detection
# ---------------------------------------------------------------------------


def test_safety_vetter_check_detects_ssn():
    # @trace WL-091
    check = SafetyVetterCheck()
    output = "SSN: 123-45-6789"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "PII pattern detected" in result.message


# ---------------------------------------------------------------------------
# SafetyVetterCheck — secrets take precedence over PII
# ---------------------------------------------------------------------------


def test_safety_vetter_check_secret_takes_precedence_over_pii():
    # @trace WL-091
    # If both a secret and PII are present, secret should be flagged (checked first)
    check = SafetyVetterCheck()
    output = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.sig and email@test.com"
    result = asyncio.run(check.check("run-1", output, {}))
    assert result.passed is False
    assert "Secret pattern detected" in result.message


def test_safety_vetter_check_result_is_vetter_check_result():
    # @trace WL-091
    check = SafetyVetterCheck()
    result = asyncio.run(check.check("run-1", "clean", {}))
    assert isinstance(result, VetterCheckResult)
