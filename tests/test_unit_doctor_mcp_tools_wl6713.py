from __future__ import annotations

from unittest.mock import patch

import httpx

from thegent.doctor import _check_mcp_tools


class _BadJsonResponse:
    status_code = 200

    def json(self) -> dict[str, str]:
        raise ValueError("bad json")


class _ListResponse:
    status_code = 200

    def json(self) -> list[str]:
        return ["not-dict"]


class _StatusResponse:
    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.text = body

    def json(self) -> dict[str, str]:
        return {"ok": True}


def test_check_mcp_tools_connection_refused_has_details() -> None:
    request = httpx.Request("GET", "http://127.0.0.1:3847/health")
    exc = httpx.ConnectError("refused", request=request)
    with patch("thegent.doctor.httpx.get", side_effect=exc):
        result = _check_mcp_tools()[0]

    assert result.status == "warn"
    assert "connection refused" in result.message.lower()
    assert "ConnectError" in (result.details or "")


def test_check_mcp_tools_timeout_has_details() -> None:
    request = httpx.Request("GET", "http://127.0.0.1:3847/health")
    exc = httpx.ReadTimeout("timeout", request=request)
    with patch("thegent.doctor.httpx.get", side_effect=exc):
        result = _check_mcp_tools()[0]

    assert result.status == "warn"
    assert "timed out" in result.message.lower()
    assert "ReadTimeout" in (result.details or "")


def test_check_mcp_tools_malformed_response_has_details() -> None:
    with patch("thegent.doctor.httpx.get", return_value=_BadJsonResponse()):
        result = _check_mcp_tools()[0]

    assert result.status == "warn"
    assert "malformed" in result.message.lower()
    assert "ValueError" in (result.details or "")


def test_check_mcp_tools_non_dict_payload_has_details() -> None:
    with patch("thegent.doctor.httpx.get", return_value=_ListResponse()):
        result = _check_mcp_tools()[0]

    assert result.status == "warn"
    assert "unexpected payload" in result.message.lower()
    assert "payload_type=list" in (result.details or "")


def test_check_mcp_tools_http_error_status_has_details() -> None:
    with patch("thegent.doctor.httpx.get", return_value=_StatusResponse(500, "error body")):
        result = _check_mcp_tools()[0]

    assert result.status == "warn"
    assert "http 500" in result.message.lower()
    assert "status_code=500" in (result.details or "")
