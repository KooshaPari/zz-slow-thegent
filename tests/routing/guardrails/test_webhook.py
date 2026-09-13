"""Tests for GW-53: Webhook guardrail interface.

# @trace FR-GUARD-053
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.utils.routing_impl.guardrails.webhook import (
    WebhookGuardrailConfig,
    WebhookVerdict,
    call_webhook_guardrail,
)

pytestmark = pytest.mark.requirement("FR-GUARD-053")

_PAYLOAD = {"messages": [{"role": "user", "content": "Hello"}]}


def _make_mock_response(body: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response-like object."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = body
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Verdict parsing
# ---------------------------------------------------------------------------


def test_webhook_verdict_allow():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail")
    mock_resp = _make_mock_response({"verdict": "allow"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp) as mock_post:
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    mock_post.assert_called_once()
    assert isinstance(result, WebhookVerdict)
    assert result.verdict == "allow"
    assert result.error == ""


def test_webhook_verdict_block():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail")
    mock_resp = _make_mock_response({"verdict": "block"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.verdict == "block"
    assert result.error == ""


def test_webhook_verdict_unknown_treated_as_allow():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail")
    mock_resp = _make_mock_response({"verdict": "maybe"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.verdict == "allow"


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


def test_webhook_on_failure_allow_when_unreachable():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", on_failure="allow")

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", side_effect=Exception("connection refused")):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.verdict == "allow"
    assert "connection refused" in result.error


def test_webhook_on_failure_block_when_unreachable():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", on_failure="block")

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", side_effect=Exception("timeout")):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.verdict == "block"
    assert result.error != ""


def test_webhook_timeout_uses_on_failure():
    import httpx as _httpx

    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", on_failure="allow", timeout_sec=0.001)

    with patch(
        "thegent.utils.routing_impl.guardrails.webhook.httpx.post", side_effect=_httpx.TimeoutException("timed out")
    ):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.verdict == "allow"
    assert result.error != ""


# ---------------------------------------------------------------------------
# Headers
# ---------------------------------------------------------------------------


def test_webhook_sends_secret_header():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", secret="mysecret")
    mock_resp = _make_mock_response({"verdict": "allow"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp) as mock_post:
        call_webhook_guardrail(cfg, _PAYLOAD)

    _, kwargs = mock_post.call_args
    headers = kwargs.get("headers", {})
    assert headers.get("X-Webhook-Secret") == "mysecret"


def test_webhook_no_secret_header_when_empty():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", secret="")
    mock_resp = _make_mock_response({"verdict": "allow"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp) as mock_post:
        call_webhook_guardrail(cfg, _PAYLOAD)

    _, kwargs = mock_post.call_args
    headers = kwargs.get("headers", {})
    assert "X-Webhook-Secret" not in headers


# ---------------------------------------------------------------------------
# transformed_data
# ---------------------------------------------------------------------------


def test_webhook_returns_transformed_data():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail")
    transformed = {"messages": [{"role": "user", "content": "Sanitised text"}]}
    mock_resp = _make_mock_response({"verdict": "allow", "transformedData": transformed})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp):
        result = call_webhook_guardrail(cfg, _PAYLOAD)

    assert result.transformed_data == transformed


def test_webhook_timeout_forwarded_to_httpx():
    cfg = WebhookGuardrailConfig(url="https://example.com/guardrail", timeout_sec=1.5)
    mock_resp = _make_mock_response({"verdict": "allow"})

    with patch("thegent.utils.routing_impl.guardrails.webhook.httpx.post", return_value=mock_resp) as mock_post:
        call_webhook_guardrail(cfg, _PAYLOAD)

    _, kwargs = mock_post.call_args
    assert kwargs.get("timeout") == pytest.approx(1.5)
