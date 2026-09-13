from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_retry_if_eagain_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(exc: BaseException) -> bool:
        captured["exc"] = exc
        return True

    monkeypatch.setattr("thegent.cli.commands.impl.spawn_retry_helpers.retry_if_eagain", _fake)

    result = impl._retry_if_eagain(RuntimeError("boom"))

    assert result is True
    assert isinstance(captured["exc"], RuntimeError)
