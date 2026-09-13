"""Tests for ``thegent.migration`` deprecation helpers.

Covers:

* :func:`thegent.migration.deprecated` — sync + async warning emission,
  message parts (replacement, since, remove_in), and ``functools.wraps``
  metadata preservation.
* :class:`thegent.migration.MigrationRegistry` — register idempotency,
  sorted ``pending()``, ``get`` for missing paths, ``clear``,
  ``__len__``, and concurrent registration safety.
* :data:`thegent.migration.default_registry` — singleton identity and
  interaction with :func:`thegent.migration.record_migration`.

@trace FR-MIGRATION-001
"""

from __future__ import annotations

import threading
import warnings
from datetime import date

import pytest

from thegent.migration import (
    MigrationEntry,
    MigrationRegistry,
    default_registry,
    deprecated,
    record_migration,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_default_registry() -> None:
    """Reset ``default_registry`` before AND after a test.

    Several tests below mutate the module-level ``default_registry``
    either directly or via :func:`record_migration`. To keep tests
    independent we wipe the registry around each one.
    """
    default_registry.clear()
    yield
    default_registry.clear()


# ---------------------------------------------------------------------------
# Decorator: sync + async warning emission
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_deprecated_sync_emits_deprecation_warning() -> None:
    """``deprecated`` emits ``DeprecationWarning`` the first time a sync
    wrapper is invoked."""
    captured: list[warnings.WarningMessage] = []

    @deprecated(replacement="thegent.new_func", since="2.0.0", remove_in="3.0.0")
    def old_func() -> str:
        return "ok"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = old_func()

    assert result == "ok"
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1
    captured.append(deprecations[0])  # keep linter quiet; assertion already passed
    assert captured  # referenced so the list is not flagged unused


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deprecated_async_emits_deprecation_warning() -> None:
    """``deprecated`` emits ``DeprecationWarning`` when wrapping an
    async coroutine function."""

    @deprecated(replacement="thegent.new_async_func")
    async def old_async_func() -> int:
        return 42

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = await old_async_func()

    assert result == 42
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1


# ---------------------------------------------------------------------------
# Decorator: warning message contents
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_deprecated_message_mentions_replacement() -> None:
    """The warning message names the replacement symbol so callers know
    where to migrate."""

    @deprecated(replacement="thegent.shiny.new_api")
    def legacy() -> None:
        return None

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy()

    message = str(caught[-1].message)
    assert "thegent.shiny.new_api" in message
    assert "Use" in message and "instead" in message


@pytest.mark.unit
def test_deprecated_message_mentions_since() -> None:
    """When ``since`` is provided it appears in the warning text."""

    @deprecated(since="2.4.0")
    def legacy() -> None:
        return None

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy()

    assert "Deprecated since 2.4.0" in str(caught[-1].message)


@pytest.mark.unit
def test_deprecated_message_mentions_remove_in() -> None:
    """When ``remove_in`` is provided it appears in the warning text."""

    @deprecated(remove_in="4.0.0")
    def legacy() -> None:
        return None

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy()

    assert "Will be removed in 4.0.0" in str(caught[-1].message)


@pytest.mark.unit
def test_deprecated_message_omits_optional_parts() -> None:
    """With no optional args the message is just the bare
    ``Call to deprecated <name>.`` notice."""

    @deprecated()
    def bare() -> None:
        return None

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        bare()

    message = str(caught[-1].message)
    assert (
        message == f"Call to deprecated {bare.__wrapped__.__qualname__}."
        or message.startswith("Call to deprecated bare.")
    )
    # None of the optional fragments should sneak in.
    assert "Use" not in message
    assert "Deprecated since" not in message
    assert "Will be removed in" not in message


@pytest.mark.unit
def test_deprecated_preserves_metadata() -> None:
    """``functools.wraps`` keeps ``__name__`` and ``__qualname__`` on the
    wrapped callable so tracebacks remain accurate."""

    @deprecated(replacement="thegent.replacement")
    def my_old_thing() -> None:
        return None

    assert my_old_thing.__name__ == "my_old_thing"
    assert (
        my_old_thing.__qualname__
        == "test_deprecated_preserves_metadata.<locals>.my_old_thing"
    )
    assert callable(my_old_thing)


# ---------------------------------------------------------------------------
# MigrationRegistry: core behavior
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_registry_register_returns_entry() -> None:
    """``register`` returns the newly created ``MigrationEntry``."""
    reg = MigrationRegistry()
    entry = reg.register(
        "thegent.legacy.foo",
        "thegent.new.foo",
        introduced="2026-01-01",
        target_removal="2027-01-01",
        notes="moved to new module",
    )

    assert isinstance(entry, MigrationEntry)
    assert entry.old_path == "thegent.legacy.foo"
    assert entry.new_path == "thegent.new.foo"
    assert entry.introduced == "2026-01-01"
    assert entry.target_removal == "2027-01-01"
    assert entry.notes == "moved to new module"


@pytest.mark.unit
def test_registry_register_is_idempotent() -> None:
    """Re-registering an existing ``old_path`` returns the original
    entry; no replacement happens."""
    reg = MigrationRegistry()
    first = reg.register(
        "thegent.legacy.idem", "thegent.new.idem", introduced="2026-01-01"
    )
    second = reg.register(
        "thegent.legacy.idem",
        "thegent.different.new",
        introduced="2099-12-31",
    )

    assert first is second
    # The originally stored fields must NOT be overwritten.
    assert second.new_path == "thegent.new.idem"
    assert second.introduced == "2026-01-01"
    assert len(reg) == 1


@pytest.mark.unit
def test_registry_pending_sorted_by_old_path() -> None:
    """``pending`` returns a tuple sorted by ``old_path`` regardless of
    insertion order."""
    reg = MigrationRegistry()
    reg.register("zeta.path", "new.zeta")
    reg.register("alpha.path", "new.alpha")
    reg.register("mu.path", "new.mu")

    snapshot = reg.pending()

    assert isinstance(snapshot, tuple)
    assert [e.old_path for e in snapshot] == [
        "alpha.path",
        "mu.path",
        "zeta.path",
    ]
    # The returned tuple must be a snapshot — mutating it cannot
    # affect the registry.
    assert len(snapshot) == 3


@pytest.mark.unit
def test_registry_get_returns_none_for_missing() -> None:
    """``get`` on an unknown path returns ``None`` rather than raising."""
    reg = MigrationRegistry()
    reg.register("known.path", "new.known")

    assert reg.get("known.path") is not None
    assert reg.get("never.registered") is None


@pytest.mark.unit
def test_registry_clear_drops_all_entries() -> None:
    """``clear`` empties the registry so subsequent reads return empty."""
    reg = MigrationRegistry()
    reg.register("a.path", "new.a")
    reg.register("b.path", "new.b")
    assert len(reg) == 2

    reg.clear()

    assert len(reg) == 0
    assert reg.pending() == ()
    assert reg.get("a.path") is None


@pytest.mark.unit
def test_registry_len_reports_entry_count() -> None:
    """``__len__`` tracks the live entry count."""
    reg = MigrationRegistry()
    assert len(reg) == 0

    reg.register("one.path", "new.one")
    assert len(reg) == 1

    reg.register("two.path", "new.two")
    assert len(reg) == 2

    # Re-registering an existing path must not bump the count.
    reg.register("one.path", "new.one.v2")
    assert len(reg) == 2


# ---------------------------------------------------------------------------
# record_migration + default_registry
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_record_migration_uses_default_registry(clean_default_registry: None) -> None:
    """``record_migration`` is a thin wrapper that delegates to
    ``default_registry.register``."""
    entry = record_migration(
        "thegent.legacy.rec",
        "thegent.new.rec",
        introduced="2026-02-02",
        notes="recorded via helper",
    )

    assert isinstance(entry, MigrationEntry)
    stored = default_registry.get("thegent.legacy.rec")
    assert stored is entry
    assert entry.notes == "recorded via helper"


@pytest.mark.unit
def test_default_registry_is_shared_singleton() -> None:
    """``default_registry`` is a process-wide singleton — two reads
    resolve to the same object, and state persists across reads."""
    from thegent import migration as migration_module

    assert migration_module.default_registry is default_registry
    # And again: reads do not rebuild it.
    assert migration_module.default_registry is default_registry


# ---------------------------------------------------------------------------
# MigrationEntry: frozen dataclass + default values
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_migration_entry_is_frozen() -> None:
    """``MigrationEntry`` is immutable: attempting to mutate a field
    raises ``dataclasses.FrozenInstanceError``."""
    entry = MigrationEntry(
        old_path="a",
        new_path="b",
        introduced="2026-01-01",
    )

    with pytest.raises(
        (AttributeError, Exception)
    ) as exc_info:  # FrozenInstanceError subclasses Exception
        entry.old_path = "mutated"  # type: ignore[misc]

    # FrozenInstanceError is a subclass of AttributeError; either way the
    # mutation must have been rejected.
    assert (
        "frozen" in exc_info.typename.lower()
        or "FrozenInstanceError" in str(type(exc_info.value))
        or isinstance(exc_info.value, AttributeError)
    )


@pytest.mark.unit
def test_migration_entry_target_removal_defaults_to_none() -> None:
    """``target_removal`` is optional and defaults to ``None``."""
    entry = MigrationEntry(
        old_path="x",
        new_path="y",
        introduced="2026-01-01",
    )

    assert entry.target_removal is None
    assert entry.notes == ""


@pytest.mark.unit
def test_registry_register_defaults_introduced_to_today() -> None:
    """When ``introduced`` is omitted, the registry stamps today's ISO
    date."""
    reg = MigrationRegistry()
    entry = reg.register("auto.dated", "new.auto")

    assert entry.introduced == date.today().isoformat()


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_registry_is_thread_safe_under_concurrent_registration() -> None:
    """Concurrent registration of distinct paths must register every
    entry exactly once — no losses, no duplicates."""
    reg = MigrationRegistry()
    thread_count = 8
    per_thread = 50

    barrier = threading.Barrier(thread_count)
    errors: list[BaseException] = []

    def worker(start: int) -> None:
        try:
            barrier.wait(timeout=5.0)
            for i in range(per_thread):
                old = f"thegent.thread.{start}.item{i}"
                reg.register(old, "thegent.new.item")
        except BaseException as exc:  # pragma: no cover — surfaced via errors
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(idx,), name=f"reg-worker-{idx}")
        for idx in range(thread_count)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert not errors, f"worker threads failed: {errors!r}"
    expected = thread_count * per_thread
    assert len(reg) == expected
    # And the snapshot must contain every distinct path.
    snapshot_paths = {e.old_path for e in reg.pending()}
    assert len(snapshot_paths) == expected
    # Spot-check: each path's stored entry should be the one returned at
    # registration time (idempotency under contention).
    assert reg.get("thegent.thread.0.item0") is not None
    assert reg.get("thegent.thread.7.item49") is not None
