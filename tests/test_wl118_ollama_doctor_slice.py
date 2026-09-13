"""WL-118 low-risk doctor slice tests."""

from __future__ import annotations

from io import StringIO

import httpx
from rich.console import Console

from thegent.doctor import CheckResult, _check_runtime_infrastructure, _display_results


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.content = b"x"

    def json(self) -> dict:
        return self._payload


def test_runtime_infrastructure_includes_ollama_check(monkeypatch) -> None:
    monkeypatch.setattr("thegent.doctor.shutil.which", lambda _bin: "/usr/local/bin/ollama")

    def fake_get(_url: str, timeout: float):
        return _Resp(200, {"models": [{"name": "llama3.3"}]})

    monkeypatch.setattr("thegent.doctor.httpx.get", fake_get)
    results = _check_runtime_infrastructure()
    ollama = [r for r in results if r.name == "Ollama Local Provider"]

    assert ollama
    assert ollama[0].status == "ok"
    assert ollama[0].severity == "info"
    assert "1 model" in ollama[0].message
    assert "/usr/local/bin/ollama" in ollama[0].message


def test_runtime_infrastructure_ollama_missing_binary(monkeypatch) -> None:
    monkeypatch.setattr("thegent.doctor.shutil.which", lambda _bin: None)
    results = _check_runtime_infrastructure()
    ollama = [r for r in results if r.name == "Ollama Local Provider"]

    assert ollama
    assert ollama[0].status == "warn"
    assert ollama[0].severity == "warning"
    assert "not found in PATH" in ollama[0].message


def test_runtime_infrastructure_ollama_timeout_sets_error_severity(monkeypatch) -> None:
    monkeypatch.setattr("thegent.doctor.shutil.which", lambda _bin: "/usr/local/bin/ollama")

    def fake_get(_url: str, timeout: float):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("thegent.doctor.httpx.get", fake_get)
    results = _check_runtime_infrastructure()
    ollama = [r for r in results if r.name == "Ollama Local Provider"]

    assert ollama
    assert ollama[0].status == "warn"
    assert ollama[0].severity == "error"
    assert "timed out" in ollama[0].message


def test_display_results_includes_severity_column(monkeypatch) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    record = CheckResult("Ollama Local Provider", "Runtime Infrastructure")
    record.status = "warn"
    record.severity = "error"
    record.message = "Probe timed out"

    success = _display_results([record])

    rendered = output.getvalue()
    assert success is True
    assert "Severity" in rendered
    assert "error" in rendered
    assert "Probe timed out" in rendered
    assert "Summary:" in rendered


def test_display_results_prints_actionable_hints_for_warn_or_fail(monkeypatch) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    warn_record = CheckResult("Ollama Local Provider", "Runtime Infrastructure")
    warn_record.status = "warn"
    warn_record.severity = "warning"
    warn_record.message = "No local model installed"
    warn_record.fix_hint = "Run `ollama pull llama3.3`."

    fail_record = CheckResult("Connectivity", "Core")
    fail_record.status = "fail"
    fail_record.severity = "critical"
    fail_record.message = "Endpoint unavailable"
    fail_record.fix_hint = "Start the daemon and retry."

    _display_results([warn_record, fail_record])
    rendered = output.getvalue()
    assert "Actionable hints:" in rendered
    assert "Run `ollama pull llama3.3`." in rendered
    assert "Start the daemon and retry." in rendered


def test_display_results_deduplicates_actionable_hints_by_normalized_text(
    monkeypatch,
) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    first = CheckResult("Ollama", "Runtime Infrastructure")
    first.status = "warn"
    first.fix_hint = "Run `ollama pull llama3.3`."

    second = CheckResult("Ollama duplicate", "Runtime Infrastructure")
    second.status = "warn"
    second.fix_hint = " run `ollama pull llama3.3`. "

    _display_results([first, second])
    rendered = output.getvalue()
    assert rendered.count("Run `ollama pull llama3.3`.") == 1


def test_display_results_deduplicates_actionable_hints_with_trailing_punctuation(
    monkeypatch,
) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    first = CheckResult("Ollama", "Runtime Infrastructure")
    first.status = "warn"
    first.fix_hint = "Start local daemon with `ollama serve`."

    second = CheckResult("Ollama duplicate", "Runtime Infrastructure")
    second.status = "warn"
    second.fix_hint = "start local daemon with `ollama serve`"

    _display_results([first, second])
    rendered = output.getvalue()
    assert rendered.count("Start local daemon with `ollama serve`.") == 1


def test_display_results_deduplicates_actionable_hints_with_leading_list_markers(
    monkeypatch,
) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    first = CheckResult("One", "Runtime Infrastructure")
    first.status = "warn"
    first.fix_hint = "1. Start local daemon with `ollama serve`."

    second = CheckResult("Two", "Runtime Infrastructure")
    second.status = "warn"
    second.fix_hint = "- Start local daemon with `ollama serve`"

    _display_results([first, second])
    rendered = output.getvalue()
    assert rendered.count("1. Start local daemon with `ollama serve`.") == 1


def test_display_results_sorts_actionable_hints_stably(monkeypatch) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )
    z_hint = CheckResult("Z", "Runtime Infrastructure")
    z_hint.status = "warn"
    z_hint.fix_hint = "zeta fix"

    a_hint = CheckResult("A", "Runtime Infrastructure")
    a_hint.status = "warn"
    a_hint.fix_hint = "alpha fix"

    _display_results([z_hint, a_hint])
    rendered = output.getvalue()
    alpha_pos = rendered.index("- [1/2] alpha fix")
    zeta_pos = rendered.index("- [2/2] zeta fix")
    assert alpha_pos < zeta_pos


def test_display_results_shows_actionable_hint_overflow_count(monkeypatch) -> None:
    output = StringIO()
    monkeypatch.setattr(
        "thegent.doctor.console",
        Console(file=output, force_terminal=False, color_system=None),
    )

    a_record = CheckResult("A", "Runtime Infrastructure")
    a_record.status = "warn"
    a_record.fix_hint = "a hint"
    b_record = CheckResult("B", "Runtime Infrastructure")
    b_record.status = "warn"
    b_record.fix_hint = "b hint"
    c_record = CheckResult("C", "Runtime Infrastructure")
    c_record.status = "warn"
    c_record.fix_hint = "c hint"
    d_record = CheckResult("D", "Runtime Infrastructure")
    d_record.status = "warn"
    d_record.fix_hint = "d hint"

    _display_results([a_record, b_record, c_record, d_record])
    rendered = output.getvalue()
    assert "- [1/3] a hint" in rendered
    assert "- [2/3] b hint" in rendered
    assert "- [3/3] c hint" in rendered
    assert "- ... and 1 more actionable hint(s)" in rendered
