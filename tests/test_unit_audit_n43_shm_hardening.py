"""AUDIT-N+43 contract spec: SHMSystem hardening (SOTA pass-27).

Spec-only hardening tests for the dormant orchestration Shared Memory
cluster.  This file defines the *target* contract surface for
``src/thegent/orchestration/state/shm.py`` and verifies it purely via
source-level introspection (no imports from the module under test) so
the spec is committed first and the source patch follows.

Covers a single dormant orchestration state module that has never been
audited in the dormant-core chain:

  * ``thegent.orchestration.state.shm``
    — ``SHMSystem(session_dir)`` singleton that wraps a native shared-
    memory extension with graceful fallback, exposes a circuit-breaker
    ``is_open`` API, an XP / level progression system, and a
    ``get_shm_system(session_dir)`` factory.

The dormant corridor is ``tests/orchestration/test_shm.py`` (32 tests,
8 test classes).  That corridor expects every invariant below to hold.

@trace FR-ORC-SH-001 — ``SHMSystem`` is a class with a singleton
                       pattern implemented via a ``_instance`` class
                       variable that is set to ``None`` at module
                       scope and lazily assigned on first call so
                       every subsequent ``SHMSystem(session_dir)``
                       returns the same object.

@trace FR-ORC-SH-002 — ``SHMSystem.__init__`` accepts a ``session_dir``
                       parameter (positional-or-keyword) so callers
                       can pass a ``Path`` and the instance stores it
                       as ``self.session_dir``.

@trace FR-ORC-SH-003 — ``SHMSystem.__init__`` sets ``self.shm_path`` to
                       ``session_dir / "state.shm"`` so the shared-
                       memory file is always co-located with the
                       session directory.

@trace FR-ORC-SH-004 — ``SHMSystem`` has a ``_interface`` class variable
                       (or instance attribute) that defaults to
                       ``None`` and is assigned an
                       ``SHMInterface(...)`` when the native extension
                       is successfully loaded, or left as ``None``
                       otherwise.

@trace FR-ORC-SH-005 — ``SHMSystem`` has a ``use_native`` boolean
                       attribute set during ``__init__`` reflecting
                       whether ``ThegentSettings().use_native_shm`` is
                       ``True``; when ``False`` the native extension
                       is never attempted.

@trace FR-ORC-SH-006 — When ``use_native`` is ``True`` but the
                       ``thegent_shm`` extension is not installed
                       (``ImportError``), ``__init__`` catches the
                       exception and leaves ``_interface`` as
                       ``None`` instead of propagating.

@trace FR-ORC-SH-007 — When ``use_native`` is ``True`` and the
                       ``thegent_shm`` extension raises an exception
                       during ``py_init_shm`` or ``SHMInterface``
                       construction, ``__init__`` catches the
                       exception and leaves ``_interface`` as
                       ``None``.

@trace FR-ORC-SH-008 — ``SHMSystem.is_native_active()`` is a method
                       that returns ``True`` when ``_interface`` is
                       not ``None`` and ``False`` when it is
                       ``None``, so callers can branch on native
                       availability.

@trace FR-ORC-SH-009 — ``SHMSystem.record_failure(target, category)``
                       accepts a ``target`` string and a ``category``
                       string; when ``category`` is ``"agent"`` it
                       delegates to ``_interface.record_failure(target,
                       0)`` and when ``category`` is anything else it
                       delegates with index ``1``.

@trace FR-ORC-SH-010 — ``SHMSystem.record_failure`` is a no-op (does
                       not raise) when ``_interface`` is ``None`` so
                       the circuit breaker degrades gracefully without
                       a native extension.

@trace FR-ORC-SH-011 — ``SHMSystem.is_open(target, category, threshold,
                       window_s, recovery_s)`` is a method with
                       default parameters ``category="agent"``,
                       ``threshold=5``, ``window_s=300``,
                       ``recovery_s=60`` and returns the boolean
                       result from ``_interface.is_open(...)`` with
                       the category mapped to an integer index (0 for
                       ``"agent"``, 1 for anything else).

@trace FR-ORC-SH-012 — ``SHMSystem.is_open`` returns ``False`` when
                       ``_interface`` is ``None`` so the circuit
                       breaker is never open without a native
                       back-end.

@trace FR-ORC-SH-013 — ``SHMSystem.award_xp(amount)`` accepts an
                       integer amount and delegates to
                       ``_interface.award_xp(amount)``; it is a
                       no-op when ``_interface`` is ``None``.

@trace FR-ORC-SH-014 — ``SHMSystem.get_xp_state()`` returns the result
                       of ``_interface.get_xp_state()`` when the
                       interface exists, or ``None`` when it does
                       not.

@trace FR-ORC-SH-015 — ``SHMSystem.set_level(level)`` accepts an
                       integer level and delegates to
                       ``_interface.set_level(level)``; it is a
                       no-op when ``_interface`` is ``None``.
                       ``get_shm_system(session_dir)`` is a module-
                       level factory that returns a ``SHMSystem``
                       singleton, and ``__all__`` exposes the
                       canonical public surface.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Helpers — read the source once at module level so every test can
# inspect it without re-reading.
# ---------------------------------------------------------------------------

_SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "thegent"
    / "orchestration"
    / "state"
    / "shm.py"
)


def _read_source() -> str:
    """Return the raw source text of shm.py."""
    return _SOURCE_PATH.read_text()


def _parse_source() -> ast.Module:
    """Return the AST of shm.py."""
    return ast.parse(_read_source())


def _source_has(pattern: str) -> bool:
    """Check whether the source text contains *pattern*."""
    return pattern in _read_source()


def _find_class(name: str) -> ast.ClassDef | None:
    """Return the ``ast.ClassDef`` node for *name*, or ``None``."""
    tree = _parse_source()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _class_methods(cls: ast.ClassDef) -> dict[str, ast.FunctionDef]:
    """Return a dict of method-name → ``ast.FunctionDef`` for *cls*."""
    methods: dict[str, ast.FunctionDef] = {}
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node  # type: ignore[assignment]
    return methods


def _function_defaults(fn: ast.FunctionDef) -> dict[str, Any]:
    """Return a mapping of parameter-name → default-value for *fn*,
    inspecting AST constant nodes."""
    args = fn.args
    defaults = {}
    # Pair defaults with the last N parameters
    num_defaults = len(args.defaults)
    if num_defaults == 0:
        return defaults
    all_args = args.args  # positional-or-keyword params
    param_names = [a.arg for a in all_args]
    for i, default in enumerate(args.defaults):
        param_idx = len(param_names) - num_defaults + i
        if param_idx >= 0 and param_idx < len(param_names):
            if isinstance(default, ast.Constant):
                defaults[param_names[param_idx]] = default.value
    return defaults


def _function_params(fn: ast.FunctionDef) -> list[str]:
    """Return the list of positional-or-keyword parameter names for *fn*."""
    return [a.arg for a in fn.args.args]


# ---------------------------------------------------------------------------
# FR-ORC-SH-001 — Singleton pattern
# ---------------------------------------------------------------------------


class TestSingletonPattern:
    """@trace FR-ORC-SH-001"""

    def test_source_defines_shm_system_class(self) -> None:
        """The module defines a ``SHMSystem`` class."""
        cls = _find_class("SHMSystem")
        assert cls is not None, "SHMSystem class not found in shm.py"

    def test_singleton_has_instance_class_var(self) -> None:
        """``SHMSystem`` references ``_instance`` for the singleton."""
        assert _source_has("_instance"), (
            "SHMSystem must define _instance for singleton pattern"
        )

    def test_singleton_init_takes_session_dir(self) -> None:
        """``__init__`` accepts a ``session_dir`` parameter."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "__init__" in methods, "SHMSystem.__init__ not found"
        params = _function_params(methods["__init__"])
        # self is params[0]; session_dir should be params[1]
        assert len(params) >= 2, (
            f"__init__ must accept at least (self, session_dir), got {params}"
        )
        assert params[1] == "session_dir", (
            f"Second param must be 'session_dir', got {params[1]!r}"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-002 — Init stores session_dir
# ---------------------------------------------------------------------------


class TestInitSessionDir:
    """@trace FR-ORC-SH-002"""

    def test_session_dir_stored_in_init(self) -> None:
        """``__init__`` assigns ``self.session_dir = session_dir``."""
        assert _source_has("self.session_dir"), (
            "__init__ must store session_dir as self.session_dir"
        )

    def test_init_is_method_not_static(self) -> None:
        """``__init__`` is an instance method (not ``@staticmethod``)."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                decorators = [
                    d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list
                ]
                assert "staticmethod" not in decorators
                return
        pytest.fail("__init__ not found")


# ---------------------------------------------------------------------------
# FR-ORC-SH-003 — shm_path = session_dir / "state.shm"
# ---------------------------------------------------------------------------


class TestShmPath:
    """@trace FR-ORC-SH-003"""

    def test_shm_path_attribute_exists(self) -> None:
        """The source references ``self.shm_path``."""
        assert _source_has("self.shm_path"), "shm_path must be stored as self.shm_path"

    def test_shm_path_uses_state_shm(self) -> None:
        """The shm_path is ``session_dir / 'state.shm'``."""
        assert _source_has("state.shm"), "shm_path must reference 'state.shm'"


# ---------------------------------------------------------------------------
# FR-ORC-SH-004 — _interface attribute
# ---------------------------------------------------------------------------


class TestInterfaceAttribute:
    """@trace FR-ORC-SH-004"""

    def test_interface_attribute_exists(self) -> None:
        """The source references ``_interface``."""
        assert _source_has("_interface"), "SHMSystem must define _interface attribute"

    def test_interface_defaults_to_none(self) -> None:
        """``_interface`` is initialized to ``None``."""
        assert _source_has("_interface") and (
            "_interface = None" in _read_source()
            or "_interface: None" in _read_source()
            or "_interface =  None" in _read_source()
        ), "_interface must default to None"


# ---------------------------------------------------------------------------
# FR-ORC-SH-005 — use_native attribute
# ---------------------------------------------------------------------------


class TestUseNative:
    """@trace FR-ORC-SH-005"""

    def test_use_native_attribute_exists(self) -> None:
        """The source references ``self.use_native``."""
        assert _source_has("self.use_native"), "SHMSystem must define self.use_native"

    def test_use_native_read_from_settings(self) -> None:
        """``use_native`` is derived from
        ``ThegentSettings().use_native_shm``."""
        assert _source_has("use_native_shm"), (
            "use_native must read from ThegentSettings().use_native_shm"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-006 — ImportError fallback for native extension
# ---------------------------------------------------------------------------


class TestNativeImportErrorFallback:
    """@trace FR-ORC-SH-006"""

    def test_importerror_is_caught(self) -> None:
        """The source catches ``ImportError`` when loading the native
        extension."""
        assert _source_has("ImportError"), (
            "Must catch ImportError when importing thegentshm extension"
        )

    def test_thegent_shm_import_attempted(self) -> None:
        """The source attempts to import ``thegent_shm``."""
        assert _source_has("thegent_shm"), (
            "Must attempt to import thegentshm native extension"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-007 — Exception handling during native init
# ---------------------------------------------------------------------------


class TestNativeInitExceptionHandling:
    """@trace FR-ORC-SH-007"""

    def test_broad_exception_caught(self) -> None:
        """The source catches ``Exception`` during native init so that
        *any* failure leaves ``_interface`` as ``None``."""
        assert _source_has("except Exception") or _source_has("except (Exception"), (
            "Must catch Exception during native SHM init"
        )

    def test_py_init_shm_called(self) -> None:
        """The source calls ``py_init_shm`` from the native module."""
        assert _source_has("py_init_shm"), (
            "Must call py_init_shm() from thegentshm module"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-008 — is_native_active method
# ---------------------------------------------------------------------------


class TestIsNativeActive:
    """@trace FR-ORC-SH-008"""

    def test_method_exists(self) -> None:
        """``is_native_active`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "is_native_active" in methods, "is_native_active method not found"

    def test_method_signature(self) -> None:
        """``is_native_active(self)`` takes no extra parameters."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["is_native_active"])
        assert params == ["self"], f"is_native_active must be (self), got {params}"

    def test_method_checks_interface(self) -> None:
        """``is_native_active`` returns a truthy check on
        ``_interface``."""
        assert _source_has("is_native_active"), (
            "is_native_active method must be defined"
        )
        # The method body should reference _interface to decide the
        # return value — we verify the source has both.
        src = _read_source()
        idx_active = src.index("is_native_active")
        # Find the next method after is_native_active to bound our search
        next_def = src.find("def ", idx_active + 20)
        body_chunk = src[idx_active:next_def] if next_def > 0 else src[idx_active:]
        assert "_interface" in body_chunk, "is_native_active must check _interface"


# ---------------------------------------------------------------------------
# FR-ORC-SH-009 — record_failure method with category mapping
# ---------------------------------------------------------------------------


class TestRecordFailure:
    """@trace FR-ORC-SH-009"""

    def test_method_exists(self) -> None:
        """``record_failure`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "record_failure" in methods, "record_failure not found"

    def test_method_signature(self) -> None:
        """``record_failure(self, target, category)``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["record_failure"])
        assert params == ["self", "target", "category"], (
            f"record_failure signature must be (self, target, category), got {params}"
        )

    def test_agent_category_maps_to_index_zero(self) -> None:
        """The ``"agent"`` category maps to index 0."""
        src = _read_source()
        idx = src.index("record_failure")
        next_def = src.find("\ndef ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert '"agent"' in body or "'agent'" in body, (
            "record_failure must handle 'agent' category"
        )
        assert "0)" in body or ", 0" in body or "== 0" in body, (
            "record_failure must map 'agent' to index 0"
        )

    def test_non_agent_category_maps_to_index_one(self) -> None:
        """Non-``"agent"`` categories map to index 1."""
        src = _read_source()
        idx = src.index("record_failure")
        next_def = src.find("\ndef ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "1)" in body or ", 1" in body or "else" in body, (
            "record_failure must map non-agent categories to index 1"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-010 — record_failure no-op without interface
# ---------------------------------------------------------------------------


class TestRecordFailureNoop:
    """@trace FR-ORC-SH-010"""

    def test_noop_when_interface_is_none(self) -> None:
        """``record_failure`` must not raise when ``_interface`` is
        ``None`` — verified by the source guarding with an ``if``
        check on ``_interface``."""
        src = _read_source()
        idx = src.index("record_failure")
        next_def = src.find("\ndef ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "if" in body and "_interface" in body, (
            "record_failure must guard with 'if _interface' to be a no-op"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-011 / FR-ORC-SH-012 — is_open circuit breaker
# ---------------------------------------------------------------------------


class TestIsOpenCircuitBreaker:
    """@trace FR-ORC-SH-011 / FR-ORC-SH-012"""

    def test_method_exists(self) -> None:
        """``is_open`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "is_open" in methods, "is_open not found"

    def test_default_parameters(self) -> None:
        """``is_open`` has defaults: ``category="agent"``,
        ``threshold=5``, ``window_s=300``, ``recovery_s=60``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        defaults = _function_defaults(methods["is_open"])
        assert defaults.get("category") == "agent", (
            f"category default must be 'agent', got {defaults.get('category')!r}"
        )
        assert defaults.get("threshold") == 5, (
            f"threshold default must be 5, got {defaults.get('threshold')!r}"
        )
        assert defaults.get("window_s") == 300, (
            f"window_s default must be 300, got {defaults.get('window_s')!r}"
        )
        assert defaults.get("recovery_s") == 60, (
            f"recovery_s default must be 60, got {defaults.get('recovery_s')!r}"
        )

    def test_method_signature(self) -> None:
        """``is_open(self, target, category, threshold, window_s,
        recovery_s)``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["is_open"])
        assert params == [
            "self",
            "target",
            "category",
            "threshold",
            "window_s",
            "recovery_s",
        ], (
            f"is_open params must be (self, target, category, threshold, window_s, recovery_s), got {params}"
        )

    def test_returns_false_without_interface(self) -> None:
        """``is_open`` returns ``False`` when ``_interface`` is
        ``None``."""
        src = _read_source()
        idx = src.index("\n    def is_open")
        next_def = src.find("\n    def ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "False" in body, "is_open must return False when interface is None"
        assert "_interface" in body, "is_open must check _interface"

    def test_category_index_mapping(self) -> None:
        """``is_open`` maps ``"agent"`` → 0 and other → 1."""
        src = _read_source()
        idx = src.index("\n    def is_open")
        next_def = src.find("\n    def ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert '"agent"' in body or "'agent'" in body, (
            "is_open must reference 'agent' category"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-013 — award_xp method
# ---------------------------------------------------------------------------


class TestAwardXp:
    """@trace FR-ORC-SH-013"""

    def test_method_exists(self) -> None:
        """``award_xp`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "award_xp" in methods, "award_xp not found"

    def test_method_signature(self) -> None:
        """``award_xp(self, amount)``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["award_xp"])
        assert params == ["self", "amount"], (
            f"award_xp must be (self, amount), got {params}"
        )

    def test_noop_when_interface_is_none(self) -> None:
        """``award_xp`` is a no-op when ``_interface`` is ``None``."""
        src = _read_source()
        idx = src.index("def award_xp")
        next_def = src.find("\n    def ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "if" in body and "_interface" in body, (
            "award_xp must guard with 'if _interface'"
        )


# ---------------------------------------------------------------------------
# FR-ORC-SH-014 — get_xp_state method
# ---------------------------------------------------------------------------


class TestGetXpState:
    """@trace FR-ORC-SH-014"""

    def test_method_exists(self) -> None:
        """``get_xp_state`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "get_xp_state" in methods, "get_xp_state not found"

    def test_method_signature(self) -> None:
        """``get_xp_state(self)`` takes no extra parameters."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["get_xp_state"])
        assert params == ["self"], f"get_xp_state must be (self), got {params}"

    def test_returns_none_without_interface(self) -> None:
        """``get_xp_state`` returns ``None`` when ``_interface`` is
        ``None``."""
        src = _read_source()
        idx = src.index("def get_xp_state")
        next_def = src.find("\n    def ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "None" in body, "get_xp_state must return None without interface"
        assert "_interface" in body, "get_xp_state must check _interface"


# ---------------------------------------------------------------------------
# FR-ORC-SH-015 — set_level + get_shm_system factory + __all__
# ---------------------------------------------------------------------------


class TestSetLevelAndFactory:
    """@trace FR-ORC-SH-015"""

    def test_set_level_exists(self) -> None:
        """``set_level`` is defined on ``SHMSystem``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        assert "set_level" in methods, "set_level not found"

    def test_set_level_signature(self) -> None:
        """``set_level(self, level)``."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        params = _function_params(methods["set_level"])
        assert params == ["self", "level"], (
            f"set_level must be (self, level), got {params}"
        )

    def test_set_level_noop_without_interface(self) -> None:
        """``set_level`` is a no-op when ``_interface`` is ``None``."""
        src = _read_source()
        idx = src.index("def set_level")
        next_def = src.find("\ndef ", idx + 20)
        body = src[idx:next_def] if next_def > 0 else src[idx:]
        assert "if" in body and "_interface" in body, (
            "set_level must guard with 'if _interface'"
        )

    def test_get_shm_system_factory_exists(self) -> None:
        """Module-level ``get_shm_system(session_dir)`` factory."""
        assert _source_has("def get_shm_system"), (
            "get_shm_system factory function not found"
        )

    def test_get_shm_system_accepts_session_dir(self) -> None:
        """``get_shm_system`` accepts a ``session_dir`` parameter."""
        tree = _parse_source()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_shm_system":
                params = _function_params(node)
                assert "session_dir" in params, (
                    f"get_shm_system must accept session_dir, got {params}"
                )
                return
        pytest.fail("get_shm_system function not found in AST")

    def test_module_all_exposes_canonical_surface(self) -> None:
        """``__all__`` exposes ``SHMSystem`` and ``get_shm_system``."""
        assert _source_has("__all__"), "Module must define __all__"
        src = _read_source()
        idx = src.index("__all__")
        block = src[idx : idx + 200]
        assert "SHMSystem" in block, "__all__ must include SHMSystem"
        assert "get_shm_system" in block, "__all__ must include get_shm_system"

    def test_source_has_all_expected_methods(self) -> None:
        """Smoke check: every expected method name appears in the
        source so no critical method was accidentally omitted."""
        cls = _find_class("SHMSystem")
        assert cls is not None
        methods = _class_methods(cls)
        expected = [
            "__init__",
            "is_native_active",
            "record_failure",
            "is_open",
            "award_xp",
            "get_xp_state",
            "set_level",
        ]
        missing = [m for m in expected if m not in methods]
        assert not missing, f"Missing methods on SHMSystem: {missing}"
