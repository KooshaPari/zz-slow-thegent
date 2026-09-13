from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_normalize_image_paths_wrapper_delegates(monkeypatch) -> None:
    called: dict[str, object] = {}

    def _fake(paths, *, supported_image_suffixes):
        called["paths"] = paths
        called["suffixes"] = supported_image_suffixes
        return ["ok"]

    monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.normalize_image_paths", _fake)

    result = impl._normalize_image_paths(["https://example.com/a.png"])

    assert result == ["ok"]
    assert called["paths"] == ["https://example.com/a.png"]
    assert isinstance(called["suffixes"], set)


def test_wl125_validate_image_capability_wrapper_delegates(monkeypatch) -> None:
    called: dict[str, object] = {}

    def _fake(*, agent, model, model_supports_vision_impl):
        called["agent"] = agent
        called["model"] = model
        called["impl"] = model_supports_vision_impl

    monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.validate_image_capability", _fake)

    impl._validate_image_capability("codex", "model-x")

    assert called["agent"] == "codex"
    assert called["model"] == "model-x"
    assert callable(called["impl"])
