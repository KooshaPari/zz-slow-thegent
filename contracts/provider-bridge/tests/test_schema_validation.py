from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _resolver_store() -> dict:
    store = {}
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        schema = _load_json(schema_file)
        schema_id = schema.get("$id")
        if schema_id:
            store[schema_id] = schema
    return store


@pytest.mark.parametrize(
    ("schema_file", "fixture_file"),
    [
        ("request.schema.json", "request.valid.json"),
        ("response.schema.json", "response.valid.json"),
        ("events.schema.json", "event.valid.json"),
        ("route-candidate.schema.json", "route-candidate.valid.json"),
        ("harness-profile.schema.json", "harness-profile.valid.json"),
    ],
)
def test_valid_fixtures(schema_file: str, fixture_file: str) -> None:
    schema = _load_json(SCHEMA_DIR / schema_file)
    instance = _load_json(FIXTURE_DIR / fixture_file)
    validator = jsonschema.Draft202012Validator(
        schema=schema,
        resolver=jsonschema.RefResolver.from_schema(schema, store=_resolver_store()),
    )
    validator.validate(instance)


def test_request_rejects_unknown_fields() -> None:
    schema = _load_json(SCHEMA_DIR / "request.schema.json")
    instance = _load_json(FIXTURE_DIR / "request.valid.json")
    instance["unknown_key"] = "should fail"
    validator = jsonschema.Draft202012Validator(schema=schema)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(instance)


def test_response_requires_error_when_status_error() -> None:
    schema = _load_json(SCHEMA_DIR / "response.schema.json")
    instance = _load_json(FIXTURE_DIR / "response.valid.json")
    instance["status"] = "error"
    validator = jsonschema.Draft202012Validator(schema=schema)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(instance)
