"""Unit tests for the dependency-free i18n translation stub."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from thegent import i18n


@pytest.fixture(autouse=True)
def reset_i18n_state() -> Iterator[None]:
    """Keep process-global locale and catalog state isolated per test."""
    i18n.set_locale("en")
    i18n.reset_catalogs()
    yield
    i18n.set_locale("en")
    i18n.reset_catalogs()


def test_default_locale_is_english() -> None:
    reloaded_i18n = importlib.reload(i18n)

    assert reloaded_i18n.get_locale() == "en"


def test_set_locale_switches_current_locale() -> None:
    i18n.set_locale("fr")

    assert i18n.get_locale() == "fr"


def test_set_locale_preserves_an_unknown_locale() -> None:
    i18n.set_locale("pt-BR")

    assert i18n.get_locale() == "pt-BR"
    assert i18n.validate_locale(i18n.get_locale()) is False


def test_translation_lookup_uses_current_locale_catalog() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})
    i18n.set_locale("fr")

    assert i18n._("Hello") == "Bonjour"


def test_translation_alias_points_to_gettext_function() -> None:
    assert i18n._ is i18n._gettext_gettext


def test_translation_lookup_is_scoped_to_current_locale() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})
    i18n.register_catalog("de", {"Hello": "Hallo"})

    i18n.set_locale("fr")
    assert i18n._("Hello") == "Bonjour"

    i18n.set_locale("de")
    assert i18n._("Hello") == "Hallo"


def test_translation_falls_back_for_missing_key() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})
    i18n.set_locale("fr")

    assert i18n._("Goodbye") == "Goodbye"


def test_translation_falls_back_when_locale_has_no_catalog() -> None:
    i18n.set_locale("ja")

    assert i18n._("Hello") == "Hello"


def test_available_locales_is_empty_without_registered_catalogs() -> None:
    assert i18n.available_locales() == ()


def test_available_locales_returns_registered_locales_sorted() -> None:
    i18n.register_catalog("ja", {"Hello": "こんにちは"})
    i18n.register_catalog("de", {"Hello": "Hallo"})
    i18n.register_catalog("fr", {"Hello": "Bonjour"})

    assert i18n.available_locales() == ("de", "fr", "ja")


def test_supported_locales_returns_sorted_recognized_locales() -> None:
    assert i18n.supported_locales() == (
        "de",
        "en",
        "en-GB",
        "en-US",
        "es",
        "fr",
        "ja",
    )


@pytest.mark.parametrize("locale", i18n.supported_locales())
def test_validate_locale_accepts_every_supported_locale(locale: str) -> None:
    assert i18n.validate_locale(locale) is True


@pytest.mark.parametrize("locale", ["", "EN", "pt-BR", "fr-FR"])
def test_validate_locale_rejects_unsupported_locales(locale: str) -> None:
    assert i18n.validate_locale(locale) is False


def test_register_catalog_returns_number_of_new_message_ids() -> None:
    added = i18n.register_catalog(
        "fr",
        {"Hello": "Bonjour", "Goodbye": "Au revoir"},
    )

    assert added == 2


def test_register_catalog_merge_counts_only_new_message_ids() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})

    added = i18n.register_catalog(
        "fr",
        {"Hello": "Salut", "Goodbye": "Au revoir"},
    )

    assert added == 1


def test_register_catalog_is_idempotent_for_identical_catalog() -> None:
    catalog = {"Hello": "Bonjour", "Goodbye": "Au revoir"}

    first_added = i18n.register_catalog("fr", catalog)
    second_added = i18n.register_catalog("fr", catalog)

    assert first_added == 2
    assert second_added == 0
    assert i18n.available_locales() == ("fr",)


def test_register_catalog_updates_existing_translation_without_counting_it() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})

    added = i18n.register_catalog("fr", {"Hello": "Salut"})
    i18n.set_locale("fr")

    assert added == 0
    assert i18n._("Hello") == "Salut"


def test_register_catalog_copies_values_from_input_mapping() -> None:
    catalog = {"Hello": "Bonjour"}
    i18n.register_catalog("fr", catalog)

    catalog["Hello"] = "Salut"
    i18n.set_locale("fr")

    assert i18n._("Hello") == "Bonjour"


def test_reset_catalogs_removes_catalogs_and_translations() -> None:
    i18n.register_catalog("fr", {"Hello": "Bonjour"})
    i18n.set_locale("fr")

    i18n.reset_catalogs()

    assert i18n.available_locales() == ()
    assert i18n._("Hello") == "Hello"


def test_reset_catalogs_does_not_change_current_locale() -> None:
    i18n.set_locale("de")
    i18n.register_catalog("de", {"Hello": "Hallo"})

    i18n.reset_catalogs()

    assert i18n.get_locale() == "de"


def test_concurrent_catalog_registration_preserves_every_translation() -> None:
    start = Event()

    def register_translation(index: int) -> int:
        start.wait()
        return i18n.register_catalog(
            "fr",
            {f"message-{index}": f"traduction-{index}"},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(register_translation, index) for index in range(64)]
        start.set()
        added_counts = [future.result() for future in futures]

    i18n.set_locale("fr")

    assert added_counts == [1] * 64
    assert all(i18n._(f"message-{index}") == f"traduction-{index}" for index in range(64))


def test_concurrent_duplicate_registration_counts_message_once() -> None:
    start = Event()

    def register_same_translation() -> int:
        start.wait()
        return i18n.register_catalog("de", {"Hello": "Hallo"})

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(register_same_translation) for _ in range(32)]
        start.set()
        added_counts = [future.result() for future in futures]

    assert sum(added_counts) == 1
    assert added_counts.count(0) == 31
