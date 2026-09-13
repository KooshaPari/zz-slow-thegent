"""Focused tests for WL-108/WL-114 incremental slices."""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.agents.base import RunResult
from thegent.cli.commands.cli import _format_context_usage_line
from thegent.cli.commands.impl import (
    _append_context_usage,
    _normalize_image_paths,
    _validate_image_capability,
)
from thegent.cli.services.run_input_helpers import build_context_usage_payload
from thegent.tui.widgets.statusbar import compute_context_usage_display


def test_wl108_append_context_usage_sets_payload_fields() -> None:
    """WL-108 helper writes used/max/ratio when context data is present."""
    payload: dict[str, object] = {}
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=600,
        context_window_max=1000,
    )

    _append_context_usage(payload, result)

    assert payload["context_usage_ratio"] == 0.6
    assert payload["context_usage"] == {
        "used": 600,
        "max": 1000,
        "ratio": 0.6,
        "display": "600/1k",
        "level": "yellow",
    }


def test_wl108_append_context_usage_skips_when_missing_fields() -> None:
    """WL-108 helper does not mutate payload when context values are absent."""
    payload: dict[str, object] = {}
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=None,
        context_window_max=1000,
    )

    _append_context_usage(payload, result)

    assert "context_usage" not in payload
    assert "context_usage_ratio" not in payload


def test_wl103_append_context_usage_emits_ratio_without_window_fields() -> None:
    payload: dict[str, object] = {}
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=None,
        context_window_max=None,
        context_usage_ratio=0.81234,
    )

    _append_context_usage(payload, result)

    assert payload["context_usage_ratio"] == 0.8123
    assert "context_usage" not in payload


@pytest.mark.parametrize("ratio", ["oops", float("nan"), float("inf"), -0.01, 1.01, True])
def test_wl103_append_context_usage_omits_invalid_ratio_without_window_fields(ratio: object) -> None:
    payload: dict[str, object] = {}
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=None,
        context_window_max=None,
        context_usage_ratio=ratio,  # type: ignore[arg-type]
    )

    _append_context_usage(payload, result)

    assert "context_usage_ratio" not in payload
    assert "context_usage" not in payload


def test_wl108_context_display_threshold_classes() -> None:
    """WL-108 context display helper maps ranges to expected classes."""
    assert compute_context_usage_display(50, 100) == ("50/100", "ctx-green")
    assert compute_context_usage_display(700, 1000) == ("700/1k", "ctx-yellow")
    assert compute_context_usage_display(900, 1000) == ("900/1k", "ctx-red")
    assert compute_context_usage_display(None, 1000) == ("N/A", None)


def test_wl108_context_line_uses_display_helper() -> None:
    line = _format_context_usage_line({"used": 700, "max": 1000, "ratio": 0.7})
    assert line == "Context usage: 700/1k"


def test_wl108_context_line_prefers_shared_threshold_path_over_precomputed_display() -> None:
    line = _format_context_usage_line({"used": 700, "max": 1000, "display": "stale"})
    assert line == "Context usage: 700/1k"


def test_wl108_build_context_usage_payload_shared_shape() -> None:
    payload = build_context_usage_payload(used=900, max_tokens=1000, ratio=None)
    assert payload == {
        "used": 900,
        "max": 1000,
        "ratio": 0.9,
        "display": "900/1k",
        "level": "red",
    }


def test_wl108_build_context_usage_payload_returns_none_without_window() -> None:
    assert build_context_usage_payload(used=None, max_tokens=1000, ratio=0.5) is None


def test_wl108_build_context_usage_payload_returns_none_for_non_positive_window() -> None:
    assert build_context_usage_payload(used=123, max_tokens=0, ratio=0.1) is None


def test_wl108_build_context_usage_payload_ignores_invalid_ratio_values() -> None:
    payload = build_context_usage_payload(used=300, max_tokens=1000, ratio=float("nan"))
    assert payload is not None
    assert payload["ratio"] == 0.3


def test_wl108_build_context_usage_payload_ignores_inconsistent_ratio_values() -> None:
    payload = build_context_usage_payload(used=900, max_tokens=1000, ratio=0.1)
    assert payload is not None
    assert payload["ratio"] == 0.9


def test_wl108_build_context_usage_payload_ignores_boolean_ratio() -> None:
    payload = build_context_usage_payload(used=250, max_tokens=1000, ratio=True)  # type: ignore[arg-type]
    assert payload is not None
    assert payload["ratio"] == 0.25


def test_wl103_build_context_usage_payload_ignores_ratio_above_one() -> None:
    payload = build_context_usage_payload(used=250, max_tokens=1000, ratio=1.5)
    assert payload is not None
    assert payload["ratio"] == 0.25


def test_wl108_build_context_usage_payload_returns_none_for_negative_used() -> None:
    assert build_context_usage_payload(used=-1, max_tokens=1000, ratio=0.1) is None


def test_wl108_build_context_usage_payload_returns_none_when_used_exceeds_max() -> None:
    assert build_context_usage_payload(used=1001, max_tokens=1000, ratio=0.1) is None


def test_wl114_normalize_image_paths_accepts_https_and_local(tmp_path: Path) -> None:
    """WL-114 accepts HTTPS URLs and supported local image files."""
    local = tmp_path / "diagram.png"
    local.write_bytes(b"png")

    normalized = _normalize_image_paths(["https://example.com/a.png", str(local)])

    assert normalized[0] == "https://example.com/a.png"
    assert normalized[1] == str(local.resolve())


def test_wl114_normalize_image_paths_deduplicates_inputs(tmp_path: Path) -> None:
    local = tmp_path / "diagram.png"
    local.write_bytes(b"png")

    normalized = _normalize_image_paths(
        [
            "https://example.com/a.png",
            "https://example.com/a.png",
            str(local),
            str(local),
        ]
    )

    assert normalized == ["https://example.com/a.png", str(local.resolve())]


def test_wl114_normalize_image_paths_rejects_non_https_url() -> None:
    """WL-114 currently requires HTTPS image URLs."""
    with pytest.raises(ValueError, match="must use HTTPS"):
        _normalize_image_paths(["http://example.com/a.png"])


def test_wl114_normalize_image_paths_rejects_non_string_input() -> None:
    with pytest.raises(ValueError, match="must be strings"):
        _normalize_image_paths([123])  # type: ignore[list-item]


def test_wl114_normalize_image_paths_rejects_url_without_image_extension() -> None:
    with pytest.raises(ValueError, match="must end with a supported extension"):
        _normalize_image_paths(["https://example.com/download"])


def test_wl114_normalize_image_paths_rejects_unsupported_local_extension(tmp_path: Path) -> None:
    """WL-114 rejects unsupported local file extensions."""
    file_path = tmp_path / "notes.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="must use a supported extension"):
        _normalize_image_paths([str(file_path)])


def test_wl114_normalize_image_paths_rejects_directory_with_image_suffix(tmp_path: Path) -> None:
    folder = tmp_path / "frames.png"
    folder.mkdir()

    with pytest.raises(ValueError, match="must point to a file"):
        _normalize_image_paths([str(folder)])


def test_wl114_run_agent_bg_forwards_image_to_bg_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    """WL-114 bg run path passes --image values through to bg_cmd."""
    from thegent.cli.apps.run import run_agent

    captured: dict[str, object] = {}

    def _fake_bg_cmd(**kwargs):
        captured.update(kwargs)
        return "sess-1"

    monkeypatch.setattr("thegent.cli.commands.cli.bg_cmd", _fake_bg_cmd)

    run_agent(
        prompt="analyze image",
        agent="codex",
        no_auto_agent=True,
        bg=True,
        image=["https://example.com/a.png"],
    )

    assert captured["image"] == ["https://example.com/a.png"]


def test_wl114_validate_image_capability_rejects_non_vision_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("thegent.cli.commands.impl._model_supports_vision", lambda _model: False)
    with pytest.raises(ValueError, match="does not advertise vision capability"):
        _validate_image_capability("codex", "text-only-model")


def test_wl114_validate_image_capability_rejects_non_codex_agent() -> None:
    with pytest.raises(ValueError, match="not supported for agent"):
        _validate_image_capability("not-image-agent", "gpt-4.1")


def test_wl114_validate_image_capability_accepts_vision_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("thegent.cli.commands.impl._model_supports_vision", lambda _model: True)
    _validate_image_capability("codex", "gpt-5-codex")
