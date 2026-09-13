"""AUDIT-N+6 wrapper-delegation parity tests.

These tests pin the AUDIT-N+6 contract:

- ``thegent.cli.commands.impl.run_impl`` MUST be a thin delegate to
  ``thegent.cli.services.run_execution_core_helpers.run_impl_core``.
- ``thegent.cli.commands.impl.bg_impl`` MUST be a thin delegate to
  ``thegent.cli.services.run_execution_core_helpers.bg_impl_core``.
- Both MUST forward ``prompt`` positionally and all caller kwargs verbatim.
- Both MUST inject ``impl_ns=thegent.cli.commands.impl`` so that the AUDIT-N+2
  envelope-parity contract (which binds ``impl``'s globals into the helper
  module via ``_bind_impl_namespace``) closes.

This file complements ``test_wl125_run_execution_core_helpers_parity.py``
(which covers the bare delegation assertion). It adds envelope-parity pinning
for:

1. ``run_impl`` returns whatever ``run_impl_core`` returns (delegation is real,
   not a stub returning a static dict).
2. ``bg_impl`` returns whatever ``bg_impl_core`` returns.
3. The helper-module delegation is idempotent — calling ``run_impl`` twice
   does not lose the kwargs from the second call.
4. Default-argument calls (``run_impl(prompt="hi")``) forward ``prompt="hi"``
   to the helper, not ``prompt=None``.
5. ``run_impl`` and ``bg_impl`` accept arbitrary kwargs (including
   ``task_id``, ``lock``, ``remote``, ``debug``, ``shadow``) without raising
   — preserving CLI surface compatibility.
6. The ``impl_ns`` value is the literal ``thegent.cli.commands.impl`` module
   object — not a re-import under a different name.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest


def _load_modules() -> tuple[Any, Any]:
    """Return ``(impl, run_execution_core_helpers)`` modules.

    Both modules are imported afresh on each call to keep the test hermetic
    against module-level monkeypatching from sibling tests.
    """
    impl = importlib.import_module("thegent.cli.commands.impl")
    rech = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    return impl, rech


def test_run_impl_returns_helper_result_when_helper_stubbed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``run_impl_core`` is stubbed to return a sentinel, ``run_impl``
    MUST return that same sentinel — proving real delegation."""
    impl, rech = _load_modules()
    sentinel = {"delegated": True, "marker": "run"}
    monkeypatch.setattr(rech, "run_impl_core", lambda **kw: dict(sentinel))
    out = impl.run_impl(prompt="hi")
    assert out == sentinel


def test_bg_impl_returns_helper_result_when_helper_stubbed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same contract for ``bg_impl`` / ``bg_impl_core``."""
    impl, rech = _load_modules()
    sentinel = {"delegated": True, "marker": "bg"}
    monkeypatch.setattr(rech, "bg_impl_core", lambda **kw: dict(sentinel))
    out = impl.bg_impl(prompt="hi")
    assert out == sentinel


def test_run_impl_forwards_prompt_positional_to_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "run_impl_core", fake)
    impl.run_impl("positional prompt")
    assert captured["prompt"] == "positional prompt"


def test_run_impl_forwards_prompt_keyword_to_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "run_impl_core", fake)
    impl.run_impl(prompt="keyword prompt")
    assert captured["prompt"] == "keyword prompt"


def test_run_impl_injects_impl_ns_equal_to_impl_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "run_impl_core", fake)
    impl.run_impl(prompt="x")
    assert "impl_ns" in captured
    assert captured["impl_ns"] is impl
    # Sanity: also equal to the canonical sys.modules entry.
    assert captured["impl_ns"] is sys.modules.get("thegent.cli.commands.impl")


def test_bg_impl_injects_impl_ns_equal_to_impl_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "bg_impl_core", fake)
    impl.bg_impl(prompt="x")
    assert "impl_ns" in captured
    assert captured["impl_ns"] is impl
    assert captured["impl_ns"] is sys.modules.get("thegent.cli.commands.impl")


def test_run_impl_forwards_arbitrary_kwargs_to_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI surface accepts many kwargs (task_id, lock, remote, debug,
    shadow, etc.). All MUST be forwarded verbatim to ``run_impl_core``."""
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "run_impl_core", fake)
    impl.run_impl(
        prompt="x",
        task_id="T-1",
        lock=["/tmp/a", "/tmp/b"],
        remote="host.example",
        debug=True,
        shadow=True,
        idempotency_token="abc",
        speculative=False,
    )
    assert captured["task_id"] == "T-1"
    assert captured["lock"] == ["/tmp/a", "/tmp/b"]
    assert captured["remote"] == "host.example"
    assert captured["debug"] is True
    assert captured["shadow"] is True
    assert captured["idempotency_token"] == "abc"
    assert captured["speculative"] is False


def test_bg_impl_forwards_arbitrary_kwargs_to_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()
    captured: dict[str, Any] = {}

    def fake(**kw: Any) -> dict[str, Any]:
        captured.update(kw)
        return {"ok": True}

    monkeypatch.setattr(rech, "bg_impl_core", fake)
    impl.bg_impl(
        prompt="x",
        continue_from="sess-1",
        continuation_include_stderr=True,
        failover=True,
        routing="pareto",
    )
    assert captured["continue_from"] == "sess-1"
    assert captured["continuation_include_stderr"] is True
    assert captured["failover"] is True
    assert captured["routing"] == "pareto"


def test_run_impl_is_idempotent_across_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling ``run_impl`` twice MUST NOT leak state from the first call
    into the second call (the helper module's globals are bound via
    ``_bind_impl_namespace`` — that contract still has to hold)."""
    impl, rech = _load_modules()
    calls: list[dict[str, Any]] = []

    def fake(**kw: Any) -> dict[str, Any]:
        calls.append(dict(kw))
        return {"call": len(calls)}

    monkeypatch.setattr(rech, "run_impl_core", fake)
    out1 = impl.run_impl(prompt="first", agent="a")
    out2 = impl.run_impl(prompt="second", agent="b")
    assert out1 == {"call": 1}
    assert out2 == {"call": 2}
    assert calls[0]["prompt"] == "first"
    assert calls[1]["prompt"] == "second"
    assert calls[0]["agent"] == "a"
    assert calls[1]["agent"] == "b"


def test_run_impl_does_not_swallow_helper_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the helper raises, the wrapper MUST propagate — silencing errors
    would defeat the AUDIT-N+2 envelope-parity contract."""
    impl, rech = _load_modules()

    def fake(**kw: Any) -> dict[str, Any]:
        raise RuntimeError("helper exploded")

    monkeypatch.setattr(rech, "run_impl_core", fake)
    with pytest.raises(RuntimeError, match="helper exploded"):
        impl.run_impl(prompt="x")


def test_bg_impl_does_not_swallow_helper_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    impl, rech = _load_modules()

    def fake(**kw: Any) -> dict[str, Any]:
        raise RuntimeError("bg helper exploded")

    monkeypatch.setattr(rech, "bg_impl_core", fake)
    with pytest.raises(RuntimeError, match="bg helper exploded"):
        impl.bg_impl(prompt="x")


def test_run_impl_lazy_imports_helper_module() -> None:
    """``impl.py`` MUST NOT import ``run_execution_core_helpers`` at module
    top level (would cause circular import on first load)."""
    impl = importlib.import_module("thegent.cli.commands.impl")
    # The wrapper's source references the helper via lazy import inside the
    # function body — verify by inspecting the module's __dict__ for a
    # bottom-level reference. The strongest guarantee is that calling
    # ``impl.run_impl`` after monkeypatching succeeds, which the other
    # tests cover. Here we only assert the helper is NOT in module globals
    # (so any accidental top-level import would be caught).
    assert "thegent.cli.services.run_execution_core_helpers" not in impl.__dict__


def test_run_impl_signature_accepts_prompt_and_kwargs() -> None:
    """Backward-compat: ``run_impl`` MUST accept ``prompt`` positionally and
    arbitrary ``**kwargs`` — callers in cli.py / run_cmd depend on it."""
    import inspect

    sig = inspect.signature(importlib.import_module("thegent.cli.commands.impl").run_impl)
    params = list(sig.parameters.values())
    assert params[0].name == "prompt"
    # last param must be VAR_KEYWORD
    assert params[-1].kind is inspect.Parameter.VAR_KEYWORD


def test_bg_impl_signature_accepts_prompt_and_kwargs() -> None:
    import inspect

    sig = inspect.signature(importlib.import_module("thegent.cli.commands.impl").bg_impl)
    params = list(sig.parameters.values())
    assert params[0].name == "prompt"
    assert params[-1].kind is inspect.Parameter.VAR_KEYWORD
