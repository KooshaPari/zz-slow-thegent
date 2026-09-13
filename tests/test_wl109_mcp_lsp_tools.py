"""WL-109 focused tests for MCP LSP tool adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.mcp.lsp_tools import lsp_diagnostics, lsp_hover, lsp_symbol_lookup
from thegent.mcp.server import _server_tools_workstream_lsp


class _FakeAdapter:
    def diagnostics(self, *, file_path: str) -> list[dict[str, object]]:
        return [
            {
                "message": "unused variable",
                "line": 3,
                "severity": "warning",
                "file": file_path,
            }
        ]

    def symbol_lookup(
        self, *, symbol_name: str, file_path: str | None
    ) -> list[dict[str, object]]:
        return [{"name": symbol_name, "kind": "function", "file_path": file_path}]

    def hover(
        self, *, file_path: str, line: int, character: int
    ) -> dict[str, object] | None:
        return {
            "contents": "hover text",
            "line": line,
            "character": character,
            "file_path": file_path,
        }


def test_lsp_diagnostics_requires_existing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="File not found"):
        lsp_diagnostics(str(tmp_path / "missing.py"), adapter=_FakeAdapter())


def test_lsp_diagnostics_returns_normalized_payload(tmp_path: Path) -> None:
    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    payload = lsp_diagnostics(str(file_path), adapter=_FakeAdapter())

    assert payload["file_path"] == str(file_path.resolve())
    assert payload["diagnostics"][0]["severity"] == "warning"
    assert payload["diagnostics"][0]["character"] == 0
    assert payload["diagnostics"][0]["file_path"] == str(file_path.resolve())
    assert payload["diagnostics"][0]["source"] == "lsp"


def test_lsp_diagnostics_normalizes_mixed_diagnostic_shapes(tmp_path: Path) -> None:
    class _ShapeAdapter:
        def diagnostics(self, *, file_path: str) -> list[dict[str, object]]:
            return [
                {
                    "message": "bad import",
                    "line": "0",
                    "character": "-2",
                    "severity": "HIGH",
                },
                {"message": "nits", "line": 2, "severity": "low", "source": "pylint"},
            ]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    payload = lsp_diagnostics(str(file_path), adapter=_ShapeAdapter())
    assert payload["diagnostics"] == [
        {
            "source": "lsp",
            "severity": "error",
            "message": "bad import",
            "line": 1,
            "character": 0,
            "file_path": str(file_path.resolve()),
        },
        {
            "source": "pylint",
            "severity": "info",
            "message": "nits",
            "line": 2,
            "character": 0,
            "file_path": str(file_path.resolve()),
        },
    ]


def test_lsp_diagnostics_rejects_non_object_diagnostic_entry(tmp_path: Path) -> None:
    class _BadAdapter:
        def diagnostics(self, *, file_path: str) -> list[object]:
            return ["bad"]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"diagnostics\[0\] must be an object"):
        lsp_diagnostics(str(file_path), adapter=_BadAdapter())


def test_lsp_diagnostics_rejects_non_integer_like_line_value(tmp_path: Path) -> None:
    class _BadLineAdapter:
        def diagnostics(self, *, file_path: str) -> list[dict[str, object]]:
            return [{"message": "bad", "line": "x1", "character": 0}]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(
        ValueError, match=r"diagnostics\[0\]\.line must be integer-like"
    ):
        lsp_diagnostics(str(file_path), adapter=_BadLineAdapter())


def test_lsp_symbol_lookup_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        lsp_symbol_lookup("   ", adapter=_FakeAdapter())


def test_lsp_symbol_lookup_normalizes_match_shape(tmp_path: Path) -> None:
    class _ShapeAdapter:
        def symbol_lookup(
            self, *, symbol_name: str, file_path: str | None
        ) -> list[dict[str, object]]:
            return [
                {
                    "name": symbol_name,
                    "kind": "function",
                    "line": "0",
                    "character": "-2",
                }
            ]

    file_path = tmp_path / "a.py"
    file_path.write_text("def f():\n    pass\n", encoding="utf-8")
    payload = lsp_symbol_lookup("f", file_path=str(file_path), adapter=_ShapeAdapter())
    assert payload["matches"] == [
        {
            "name": "f",
            "kind": "function",
            "line": 1,
            "character": 0,
            "file_path": str(file_path.resolve()),
        }
    ]


def test_lsp_symbol_lookup_strips_file_path_whitespace(tmp_path: Path) -> None:
    class _ShapeAdapter:
        def symbol_lookup(
            self, *, symbol_name: str, file_path: str | None
        ) -> list[dict[str, object]]:
            return [
                {
                    "name": symbol_name,
                    "kind": "function",
                    "file_path": " /tmp/example.py ",
                    "line": 1,
                }
            ]

    file_path = tmp_path / "a.py"
    file_path.write_text("def f():\n    pass\n", encoding="utf-8")
    payload = lsp_symbol_lookup("f", file_path=str(file_path), adapter=_ShapeAdapter())
    assert payload["matches"][0]["file_path"] == "/tmp/example.py"


def test_lsp_symbol_lookup_rejects_non_object_match(tmp_path: Path) -> None:
    class _BadAdapter:
        def symbol_lookup(
            self, *, symbol_name: str, file_path: str | None
        ) -> list[object]:
            return ["bad"]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"matches\[0\] must be an object"):
        lsp_symbol_lookup("x", file_path=str(file_path), adapter=_BadAdapter())


def test_lsp_symbol_lookup_rejects_match_without_name(tmp_path: Path) -> None:
    class _BadAdapter:
        def symbol_lookup(
            self, *, symbol_name: str, file_path: str | None
        ) -> list[dict[str, object]]:
            return [{"kind": "function", "file_path": file_path}]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty 'name'"):
        lsp_symbol_lookup("x", file_path=str(file_path), adapter=_BadAdapter())


def test_lsp_symbol_lookup_rejects_fractional_float_positions(tmp_path: Path) -> None:
    class _BadAdapter:
        def symbol_lookup(
            self, *, symbol_name: str, file_path: str | None
        ) -> list[dict[str, object]]:
            return [
                {
                    "name": symbol_name,
                    "kind": "function",
                    "file_path": file_path,
                    "line": 2.5,
                    "character": 1,
                }
            ]

    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"matches\[0\]\.line must be integer-like"):
        lsp_symbol_lookup("x", file_path=str(file_path), adapter=_BadAdapter())


def test_lsp_hover_rejects_negative_coordinates(tmp_path: Path) -> None:
    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line must be >= 0"):
        lsp_hover(str(file_path), line=-1, character=0, adapter=_FakeAdapter())


def test_lsp_hover_rejects_non_integer_coordinates(tmp_path: Path) -> None:
    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line must be an integer"):
        lsp_hover(str(file_path), line=1.5, character=0, adapter=_FakeAdapter())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="character must be an integer"):
        lsp_hover(str(file_path), line=1, character=0.5, adapter=_FakeAdapter())  # type: ignore[arg-type]


def test_python_default_adapter_returns_syntax_diagnostic(tmp_path: Path) -> None:
    file_path = tmp_path / "bad.py"
    file_path.write_text("def broken(:\n", encoding="utf-8")

    payload = lsp_diagnostics(str(file_path))

    assert payload["file_path"] == str(file_path.resolve())
    assert len(payload["diagnostics"]) == 1
    assert payload["diagnostics"][0]["source"] == "python-compile"


def test_python_default_adapter_symbol_and_hover(tmp_path: Path) -> None:
    file_path = tmp_path / "ok.py"
    file_path.write_text(
        "def greet(name):\n    return name\n\nx = greet('hi')\n", encoding="utf-8"
    )

    symbols = lsp_symbol_lookup("greet", file_path=str(file_path))
    hover = lsp_hover(str(file_path), line=3, character=4)

    assert symbols["matches"]
    assert symbols["matches"][0]["kind"] == "function"
    assert hover["hover"] is not None
    assert hover["hover"]["symbol"] == "greet"


def test_default_adapter_is_guarded_for_non_python_file(tmp_path: Path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(RuntimeError, match="LSP_BACKEND_UNAVAILABLE"):
        lsp_diagnostics(str(file_path))


def test_lsp_diagnostics_tool_maps_unavailable_backend_error(tmp_path: Path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    def _error_result(error: str, remediation: str):
        return {"error": error, "remediation": remediation}

    result = _server_tools_workstream_lsp.lsp_diagnostics_tool_impl(
        file_path=str(file_path),
        diagnostics_impl=lsp_diagnostics,
        error_result=_error_result,
    )

    assert "LSP_BACKEND_UNAVAILABLE" in result["error"]
    assert "Configure THGENT_LSP_ADAPTER=python-ast" in result["remediation"]


def test_lsp_diagnostics_tool_maps_unsupported_adapter_remediation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file_path = tmp_path / "a.py"
    file_path.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setenv("THGENT_LSP_ADAPTER", "unknown")

    def _error_result(error: str, remediation: str):
        return {"error": error, "remediation": remediation}

    result = _server_tools_workstream_lsp.lsp_diagnostics_tool_impl(
        file_path=str(file_path),
        diagnostics_impl=lsp_diagnostics,
        error_result=_error_result,
    )

    assert "LSP_BACKEND_UNAVAILABLE" in result["error"]
    assert "unsupported value" in result["remediation"]
