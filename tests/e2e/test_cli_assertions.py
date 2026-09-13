"""Unit tests for shared E2E CLI assertion helpers."""

from __future__ import annotations

import hashlib
import json

from tests.e2e.cli_assertions import expected_trend_health_signature, load_cli_json


def test_load_cli_json_parses_plain_json_object() -> None:
    payload = '{"ok": true, "count": 2}'

    parsed = load_cli_json(payload)

    assert parsed == {"ok": True, "count": 2}


def test_load_cli_json_skips_non_json_leading_noise() -> None:
    payload = 'noise before output\n{"status": "ready", "items": [1, 2]}'

    parsed = load_cli_json(payload)

    assert parsed == {"status": "ready", "items": [1, 2]}


def test_load_cli_json_parses_array_payload() -> None:
    payload = "log prefix [1, 2, 3]"

    parsed = load_cli_json(payload)

    assert parsed == [1, 2, 3]


def test_expected_trend_health_signature_is_deterministic() -> None:
    policy_a, signature_a = expected_trend_health_signature()
    policy_b, signature_b = expected_trend_health_signature()

    assert policy_a == policy_b
    assert signature_a == signature_b
    assert signature_a == "169eb45ac5f41eb78b8837061e92d86a523fa4839a8ee9a38a94453856cfcecc"


def test_expected_trend_health_signature_matches_policy_hash() -> None:
    policy, signature = expected_trend_health_signature()

    expected = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    assert signature == expected
