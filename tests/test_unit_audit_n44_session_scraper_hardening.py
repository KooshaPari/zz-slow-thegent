"""AUDIT-N+44 contract spec: SessionScraper hardening (SOTA pass-28).

Spec + runtime hardening tests for the dormant orchestration state
SessionScraper cluster.  This file defines the *target* contract surface
for ``src/thegent/orchestration/state/session_scraper.py`` and verifies
it via direct runtime imports with ``tmp_path`` fixtures so every
assertion exercises the actual production stub.

Covers a single dormant orchestration state module that has never been
audited in the dormant-core chain:

  * ``thegent.orchestration.state.session_scraper``
    — ``SessionScraper(session_dir)`` class that exposes
    ``scrape_session(session_id)``, ``scrape_all_sessions()``,
    ``get_session_summary(session_id)`` and ``scrape_turns(session_id)``
    public surface for extracting session data from the orchestration
    state layer (WP-1006, FR-ORC-SS-001..015).

This spec is committed first (spec-first pattern, mirrors AUDIT-N+42 /
N+43 / N+33..N+41) so the next step is to make every assertion here
pass without breaking the dormant corridor or any other SOTA
audit-N+ invariant cluster.

The tests import from the module under test directly and use
``tmp_path`` fixtures for filesystem isolation.

@trace FR-ORC-SS-001 -- SessionScraper can be initialized with default
                       path when no session_dir argument is supplied;
                       the default path is ``/tmp/thegent/sessions``.
@trace FR-ORC-SS-002 -- SessionScraper can be initialized with a
                       custom path supplied as a ``Path`` or ``str``
                       and the instance stores it as ``self.session_dir``
                       as a ``Path`` object.
@trace FR-ORC-SS-003 -- ``scrape_session(session_id)`` returns a dict
                       containing a ``session_id`` key whose value
                       matches the supplied session_id.
@trace FR-ORC-SS-004 -- ``scrape_session(session_id)`` returns a dict
                       containing a ``status`` key whose value is a
                       string.
@trace FR-ORC-SS-005 -- ``scrape_session(session_id)`` returns a dict
                       containing a ``turns`` key whose value is a
                       list.
@trace FR-ORC-SS-006 -- ``scrape_session`` with an unknown / arbitrary
                       session ID returns ``status`` equal to
                       ``"unknown"``.
@trace FR-ORC-SS-007 -- ``scrape_all_sessions()`` returns a list
                       (regardless of the session directory contents).
@trace FR-ORC-SS-008 -- ``scrape_all_sessions()`` returns an empty
                       list when the session directory is empty or
                       contains no session subdirectories.
@trace FR-ORC-SS-009 -- ``get_session_summary(session_id)`` returns a
                       dict containing a ``session_id`` key.
@trace FR-ORC-SS-010 -- ``get_session_summary(session_id)`` returns a
                       dict containing a ``turn_count`` key whose
                       value is an ``int``.
@trace FR-ORC-SS-011 -- ``get_session_summary(session_id)`` returns a
                       dict containing a ``last_activity`` key.
@trace FR-ORC-SS-012 -- ``scrape_turns(session_id)`` returns a list
                       (possibly empty).
@trace FR-ORC-SS-013 -- ``scrape_turns`` with an unknown / arbitrary
                       session ID returns an empty list.
@trace FR-ORC-SS-014 -- SessionScraper handles an invalid (non-existent
                       or non-directory) session_dir path gracefully
                       during ``__init__`` without raising an exception.
@trace FR-ORC-SS-015 -- SessionScraper methods are deterministic:
                       consecutive calls with identical arguments return
                       identical results.
"""

from __future__ import annotations

from pathlib import Path

from thegent.orchestration.state.session_scraper import SessionScraper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_SESSION_DIR = "/tmp/thegent/sessions"


# ---------------------------------------------------------------------------
# FR-ORC-SS-001 -- Default path initialisation
# ---------------------------------------------------------------------------


class TestDefaultPathInit:
    """@trace FR-ORC-SS-001"""

    def test_default_session_dir_is_tmp(self) -> None:
        """``SessionScraper()`` uses ``/tmp/thegent/sessions`` as default."""
        scraper = SessionScraper()
        assert scraper.session_dir == Path(_DEFAULT_SESSION_DIR)

    def test_default_session_dir_is_path_instance(self) -> None:
        """Default ``session_dir`` is a ``pathlib.Path`` instance."""
        scraper = SessionScraper()
        assert isinstance(scraper.session_dir, Path)

    def test_default_init_no_args(self) -> None:
        """``SessionScraper()`` can be called with zero arguments."""
        scraper = SessionScraper()
        assert scraper is not None


# ---------------------------------------------------------------------------
# FR-ORC-SS-002 -- Custom path initialisation
# ---------------------------------------------------------------------------


class TestCustomPathInit:
    """@trace FR-ORC-SS-002"""

    def test_custom_path_as_path_object(self, tmp_path: Path) -> None:
        """``SessionScraper(Path(...))`` stores the custom path."""
        custom = tmp_path / "my_sessions"
        scraper = SessionScraper(custom)
        assert scraper.session_dir == custom

    def test_custom_path_as_string(self, tmp_path: Path) -> None:
        """``SessionScraper(str)`` converts string to ``Path``."""
        custom_str = str(tmp_path / "string_sessions")
        scraper = SessionScraper(custom_str)
        assert scraper.session_dir == Path(custom_str)

    def test_custom_path_stored_as_path_type(self, tmp_path: Path) -> None:
        """``session_dir`` is always a ``Path`` even when a string is passed."""
        scraper = SessionScraper(str(tmp_path))
        assert isinstance(scraper.session_dir, Path)

    def test_custom_path_not_mutated(self, tmp_path: Path) -> None:
        """Passing a ``Path`` does not mutate the original object."""
        original = tmp_path / "immutable"
        scraper = SessionScraper(original)
        assert scraper.session_dir == original


# ---------------------------------------------------------------------------
# FR-ORC-SS-003 -- scrape_session returns session_id key
# ---------------------------------------------------------------------------


class TestScrapeSessionSessionId:
    """@trace FR-ORC-SS-003"""

    def test_returns_dict_with_session_id_key(self, tmp_path: Path) -> None:
        """``scrape_session`` result contains ``session_id`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-001")
        assert isinstance(result, dict)
        assert "session_id" in result

    def test_session_id_matches_input(self, tmp_path: Path) -> None:
        """``session_id`` value equals the supplied argument."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-001")
        assert result["session_id"] == "sess-001"

    def test_session_id_is_string_type(self, tmp_path: Path) -> None:
        """``session_id`` value is a ``str``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-001")
        assert isinstance(result["session_id"], str)


# ---------------------------------------------------------------------------
# FR-ORC-SS-004 -- scrape_session returns status key
# ---------------------------------------------------------------------------


class TestScrapeSessionStatus:
    """@trace FR-ORC-SS-004"""

    def test_returns_dict_with_status_key(self, tmp_path: Path) -> None:
        """``scrape_session`` result contains ``status`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-002")
        assert "status" in result

    def test_status_is_string_type(self, tmp_path: Path) -> None:
        """``status`` value is a ``str``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-002")
        assert isinstance(result["status"], str)


# ---------------------------------------------------------------------------
# FR-ORC-SS-005 -- scrape_session returns turns key
# ---------------------------------------------------------------------------


class TestScrapeSessionTurns:
    """@trace FR-ORC-SS-005"""

    def test_returns_dict_with_turns_key(self, tmp_path: Path) -> None:
        """``scrape_session`` result contains ``turns`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-003")
        assert "turns" in result

    def test_turns_is_list_type(self, tmp_path: Path) -> None:
        """``turns`` value is a ``list``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("sess-003")
        assert isinstance(result["turns"], list)


# ---------------------------------------------------------------------------
# FR-ORC-SS-006 -- scrape_session unknown ID returns status "unknown"
# ---------------------------------------------------------------------------


class TestScrapeSessionUnknownId:
    """@trace FR-ORC-SS-006"""

    def test_unknown_id_returns_status_unknown(self, tmp_path: Path) -> None:
        """Arbitrary session ID yields ``status == "unknown"``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("nonexistent-id-xyz")
        assert result["status"] == "unknown"

    def test_empty_id_returns_status_unknown(self, tmp_path: Path) -> None:
        """Empty session ID yields ``status == "unknown"``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("")
        assert result["status"] == "unknown"

    def test_numeric_id_returns_status_unknown(self, tmp_path: Path) -> None:
        """Numeric-string session ID yields ``status == "unknown"``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("12345")
        assert result["status"] == "unknown"


# ---------------------------------------------------------------------------
# FR-ORC-SS-007 -- scrape_all_sessions returns list
# ---------------------------------------------------------------------------


class TestScrapeAllSessionsReturnType:
    """@trace FR-ORC-SS-007"""

    def test_returns_list(self, tmp_path: Path) -> None:
        """``scrape_all_sessions()`` returns a ``list``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_all_sessions()
        assert isinstance(result, list)

    def test_default_dir_returns_list(self) -> None:
        """``scrape_all_sessions()`` on default dir returns a list."""
        scraper = SessionScraper()
        result = scraper.scrape_all_sessions()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# FR-ORC-SS-008 -- scrape_all_sessions empty dir returns empty list
# ---------------------------------------------------------------------------


class TestScrapeAllSessionsEmptyDir:
    """@trace FR-ORC-SS-008"""

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        """Empty session directory yields an empty list."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_all_sessions()
        assert result == []

    def test_empty_dir_returns_length_zero(self, tmp_path: Path) -> None:
        """Empty session directory yields a list with length 0."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_all_sessions()
        assert len(result) == 0

    def test_nonexistent_dir_returns_empty_list(self, tmp_path: Path) -> None:
        """Non-existent session directory yields an empty list."""
        missing = tmp_path / "does_not_exist"
        scraper = SessionScraper(missing)
        result = scraper.scrape_all_sessions()
        assert result == []


# ---------------------------------------------------------------------------
# FR-ORC-SS-009 -- get_session_summary returns session_id key
# ---------------------------------------------------------------------------


class TestGetSessionSummarySessionId:
    """@trace FR-ORC-SS-009"""

    def test_returns_dict_with_session_id_key(self, tmp_path: Path) -> None:
        """``get_session_summary`` result contains ``session_id`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-004")
        assert isinstance(result, dict)
        assert "session_id" in result

    def test_session_id_matches_input(self, tmp_path: Path) -> None:
        """``session_id`` value equals the supplied argument."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-004")
        assert result["session_id"] == "sess-004"

    def test_session_id_is_string_type(self, tmp_path: Path) -> None:
        """``session_id`` value is a ``str``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-004")
        assert isinstance(result["session_id"], str)


# ---------------------------------------------------------------------------
# FR-ORC-SS-010 -- get_session_summary returns turn_count key (int)
# ---------------------------------------------------------------------------


class TestGetSessionSummaryTurnCount:
    """@trace FR-ORC-SS-010"""

    def test_returns_dict_with_turn_count_key(self, tmp_path: Path) -> None:
        """``get_session_summary`` result contains ``turn_count`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-005")
        assert "turn_count" in result

    def test_turn_count_is_int_type(self, tmp_path: Path) -> None:
        """``turn_count`` value is an ``int``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-005")
        assert isinstance(result["turn_count"], int)

    def test_turn_count_default_is_zero(self, tmp_path: Path) -> None:
        """Stub returns ``turn_count == 0``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-005")
        assert result["turn_count"] == 0


# ---------------------------------------------------------------------------
# FR-ORC-SS-011 -- get_session_summary returns last_activity key
# ---------------------------------------------------------------------------


class TestGetSessionSummaryLastActivity:
    """@trace FR-ORC-SS-011"""

    def test_returns_dict_with_last_activity_key(self, tmp_path: Path) -> None:
        """``get_session_summary`` result contains ``last_activity`` key."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-006")
        assert "last_activity" in result

    def test_last_activity_default_is_none(self, tmp_path: Path) -> None:
        """Stub returns ``last_activity == None``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("sess-006")
        assert result["last_activity"] is None


# ---------------------------------------------------------------------------
# FR-ORC-SS-012 -- scrape_turns returns list
# ---------------------------------------------------------------------------


class TestScrapeTurnsReturnType:
    """@trace FR-ORC-SS-012"""

    def test_returns_list(self, tmp_path: Path) -> None:
        """``scrape_turns`` returns a ``list``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_turns("sess-007")
        assert isinstance(result, list)

    def test_returns_empty_list_for_stub(self, tmp_path: Path) -> None:
        """Stub returns an empty list."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_turns("sess-007")
        assert result == []


# ---------------------------------------------------------------------------
# FR-ORC-SS-013 -- scrape_turns unknown ID returns empty list
# ---------------------------------------------------------------------------


class TestScrapeTurnsUnknownId:
    """@trace FR-ORC-SS-013"""

    def test_unknown_id_returns_empty_list(self, tmp_path: Path) -> None:
        """Arbitrary session ID yields an empty list of turns."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_turns("nonexistent-xyz")
        assert result == []

    def test_empty_id_returns_empty_list(self, tmp_path: Path) -> None:
        """Empty session ID yields an empty list of turns."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_turns("")
        assert result == []


# ---------------------------------------------------------------------------
# FR-ORC-SS-014 -- Invalid session_dir handled gracefully
# ---------------------------------------------------------------------------


class TestInvalidSessionDirGraceful:
    """@trace FR-ORC-SS-014"""

    def test_nonexistent_path_does_not_raise(self, tmp_path: Path) -> None:
        """``SessionScraper`` does not raise for a non-existent path."""
        nonexistent = tmp_path / "no" / "such" / "path"
        scraper = SessionScraper(nonexistent)
        assert scraper.session_dir == nonexistent

    def test_file_as_session_dir_does_not_raise(self, tmp_path: Path) -> None:
        """``SessionScraper`` does not raise when a file is passed as dir."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("placeholder")
        scraper = SessionScraper(file_path)
        assert scraper.session_dir == file_path

    def test_empty_string_path_does_not_raise(self) -> None:
        """``SessionScraper("")`` does not raise."""
        scraper = SessionScraper("")
        assert isinstance(scraper.session_dir, Path)

    def test_none_path_uses_default(self) -> None:
        """``SessionScraper(None)`` falls back to default path."""
        scraper = SessionScraper(None)
        assert scraper.session_dir == Path(_DEFAULT_SESSION_DIR)

    def test_scrape_methods_work_with_invalid_dir(self, tmp_path: Path) -> None:
        """Methods remain callable after initialising with invalid dir."""
        nonexistent = tmp_path / "nonexistent"
        scraper = SessionScraper(nonexistent)
        assert scraper.scrape_session("x") == {
            "session_id": "x",
            "status": "unknown",
            "turns": [],
        }
        assert scraper.scrape_all_sessions() == []
        assert scraper.get_session_summary("x") == {
            "session_id": "x",
            "turn_count": 0,
            "last_activity": None,
        }
        assert scraper.scrape_turns("x") == []


# ---------------------------------------------------------------------------
# FR-ORC-SS-015 -- Deterministic behaviour
# ---------------------------------------------------------------------------


class TestDeterministicBehaviour:
    """@trace FR-ORC-SS-015"""

    def test_scrape_session_deterministic(self, tmp_path: Path) -> None:
        """Consecutive ``scrape_session`` calls return identical dicts."""
        scraper = SessionScraper(tmp_path)
        first = scraper.scrape_session("sess-det-1")
        second = scraper.scrape_session("sess-det-1")
        assert first == second

    def test_scrape_all_sessions_deterministic(self, tmp_path: Path) -> None:
        """Consecutive ``scrape_all_sessions`` calls return identical lists."""
        scraper = SessionScraper(tmp_path)
        first = scraper.scrape_all_sessions()
        second = scraper.scrape_all_sessions()
        assert first == second

    def test_get_session_summary_deterministic(self, tmp_path: Path) -> None:
        """Consecutive ``get_session_summary`` calls return identical dicts."""
        scraper = SessionScraper(tmp_path)
        first = scraper.get_session_summary("sess-det-2")
        second = scraper.get_session_summary("sess-det-2")
        assert first == second

    def test_scrape_turns_deterministic(self, tmp_path: Path) -> None:
        """Consecutive ``scrape_turns`` calls return identical lists."""
        scraper = SessionScraper(tmp_path)
        first = scraper.scrape_turns("sess-det-3")
        second = scraper.scrape_turns("sess-det-3")
        assert first == second

    def test_scrape_session_returns_new_dict_each_call(self, tmp_path: Path) -> None:
        """Each call returns a fresh dict (not the same object)."""
        scraper = SessionScraper(tmp_path)
        first = scraper.scrape_session("sess-obj")
        second = scraper.scrape_session("sess-obj")
        assert first == second
        assert first is not second


# ---------------------------------------------------------------------------
# Cross-cutting: overall shape and __all__ contract
# ---------------------------------------------------------------------------


class TestModuleContract:
    """Verify module-level export and class surface."""

    def test_session_scraper_is_importable(self) -> None:
        """``SessionScraper`` can be imported from the module."""
        from thegent.orchestration.state.session_scraper import (
            SessionScraper as _ScraperImport,
        )

        assert _ScraperImport is not None

    def test_all_method_names_present(self, tmp_path: Path) -> None:
        """All expected public methods are callable."""
        scraper = SessionScraper(tmp_path)
        assert callable(scraper.scrape_session)
        assert callable(scraper.scrape_all_sessions)
        assert callable(scraper.get_session_summary)
        assert callable(scraper.scrape_turns)

    def test_scrape_session_full_shape(self, tmp_path: Path) -> None:
        """``scrape_session`` returns exactly the keys ``session_id``,
        ``status``, ``turns``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.scrape_session("shape-check")
        assert set(result.keys()) == {"session_id", "status", "turns"}

    def test_get_session_summary_full_shape(self, tmp_path: Path) -> None:
        """``get_session_summary`` returns exactly the keys
        ``session_id``, ``turn_count``, ``last_activity``."""
        scraper = SessionScraper(tmp_path)
        result = scraper.get_session_summary("shape-check")
        assert set(result.keys()) == {"session_id", "turn_count", "last_activity"}
