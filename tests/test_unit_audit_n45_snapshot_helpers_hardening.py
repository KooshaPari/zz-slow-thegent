"""Spec-only hardening tests for the SessionSnapshotCLIHelpers cluster (AUDIT-N+45).

Covers a single dormant orchestration/state module that has never
been audited in the dormant-core chain:

  * ``thegent.orchestration.state.session_snapshot_cli_helpers``
    — ``SessionSnapshotCLIHelpers`` class, ``format_snapshot``,
    ``parse_snapshot_args``, ``snapshot_daily_export_payload``,
    ``snapshot_daily_index_payload``, ``snapshot_daily_totals_payload``,
    ``snapshot_export_payload``, ``snapshot_index_payload``,
    ``snapshot_prune_payload``, ``snapshot_list_payload``,
    ``snapshot_triggers_tags_payload`` helpers (FR-ORC-SV-001..015).

This file is the AUDIT-N+45 contract spec.  It is committed first
(spec-first pattern, mirrors AUDIT-N+39) so the next step is to make
every assertion here pass without breaking the dormant corridor or any
other SOTA audit-N+ invariant cluster.

@trace FR-ORC-SV-001 -- ``format_snapshot(snapshot)`` returns ``str``
                       regardless of the snapshot's input type so the
                       CLI display layer always receives renderable text.
@trace FR-ORC-SV-002 -- ``format_snapshot(None)`` returns ``str``
                       (the literal string ``"None"``) so callers
                       never receive ``NoneType`` from the formatter.
@trace FR-ORC-SV-003 -- ``format_snapshot`` with a ``dict`` argument
                       returns a string representation of that dict
                       (via ``str()``) so structured snapshots are
                       representable in CLI output.
@trace FR-ORC-SV-004 -- ``parse_snapshot_args(args)`` returns ``dict``
                       so downstream code can unpack the result as
                       keyword arguments without type-checking.
@trace FR-ORC-SV-005 -- ``parse_snapshot_args([])`` returns an empty
                       ``dict`` so callers never receive ``None`` or
                       ``KeyError`` when no arguments are supplied.
@trace FR-ORC-SV-006 -- ``snapshot_daily_export_payload(date)`` returns
                       a ``dict`` containing a ``'date'`` key whose
                       value equals the supplied ``date`` parameter.
@trace FR-ORC-SV-007 -- ``snapshot_daily_export_payload(date)`` returns
                       a ``dict`` containing a ``'snapshots'`` key
                       whose value is a ``list``.
@trace FR-ORC-SV-008 -- ``snapshot_daily_index_payload(date)`` returns
                       a ``dict`` containing a ``'date'`` key whose
                       value equals the supplied ``date`` parameter.
@trace FR-ORC-SV-009 -- ``snapshot_daily_index_payload(date)`` returns
                       a ``dict`` containing an ``'index'`` key whose
                       value is a ``list``.
@trace FR-ORC-SV-010 -- ``snapshot_daily_totals_payload(date)`` returns
                       a ``dict`` containing a ``'date'`` key whose
                       value equals the supplied ``date`` parameter.
@trace FR-ORC-SV-011 -- ``snapshot_daily_totals_payload(date)`` returns
                       a ``dict`` containing a ``'totals'`` key whose
                       value is a ``dict``.
@trace FR-ORC-SV-012 -- ``snapshot_export_payload(date, session_id)``
                       returns a ``dict`` containing both ``'date'``
                       and ``'data'`` keys so the export contract is
                       satisfied regardless of ``session_id``.
@trace FR-ORC-SV-013 -- ``snapshot_index_payload(date, session_id)``
                       returns a ``dict`` containing both ``'date'``
                       and ``'index'`` keys so the index contract is
                       satisfied regardless of ``session_id``.
@trace FR-ORC-SV-014 -- ``snapshot_prune_payload(date, session_ids)``
                       returns a ``dict`` whose ``'action'`` key is
                       the literal string ``'prune'`` so dispatchers
                       can rely on the action discriminator.
@trace FR-ORC-SV-015 -- ``snapshot_list_payload(snapshots)`` returns
                       a ``dict`` whose ``'count'`` key equals
                       ``len(snapshots)`` so callers can verify list
                       integrity without re-counting.
"""

from __future__ import annotations

from thegent.orchestration.state.session_snapshot_cli_helpers import (
    SessionSnapshotCLIHelpers,
    format_snapshot,
    parse_snapshot_args,
    snapshot_daily_export_payload,
    snapshot_daily_index_payload,
    snapshot_daily_totals_payload,
    snapshot_export_payload,
    snapshot_index_payload,
    snapshot_list_payload,
    snapshot_prune_payload,
    snapshot_triggers_tags_payload,
)

# ---------------------------------------------------------------------------
# FR-ORC-SV-001 / FR-ORC-SV-002 / FR-ORC-SV-003 -- format_snapshot contract
# ---------------------------------------------------------------------------


class TestFormatSnapshotReturnsString:
    """@trace FR-ORC-SV-001"""

    def test_string_input_returns_str(self) -> None:
        """A plain string snapshot must round-trip as ``str``."""
        result = format_snapshot("hello")
        assert isinstance(result, str)
        assert result == "hello"

    def test_int_input_returns_str(self) -> None:
        """An integer snapshot must be coerced to ``str``."""
        result = format_snapshot(42)
        assert isinstance(result, str)
        assert result == "42"

    def test_float_input_returns_str(self) -> None:
        result = format_snapshot(3.14)
        assert isinstance(result, str)
        assert result == "3.14"

    def test_bool_input_returns_str(self) -> None:
        result = format_snapshot(True)
        assert isinstance(result, str)
        assert result == "True"

    def test_empty_string_returns_empty_str(self) -> None:
        result = format_snapshot("")
        assert isinstance(result, str)
        assert result == ""


class TestFormatSnapshotWithNone:
    """@trace FR-ORC-SV-002"""

    def test_none_returns_str(self) -> None:
        """``format_snapshot(None)`` must return ``str("None")``."""
        result = format_snapshot(None)
        assert isinstance(result, str)
        assert result == "None"


class TestFormatSnapshotWithDict:
    """@trace FR-ORC-SV-003"""

    def test_empty_dict_returns_str(self) -> None:
        result = format_snapshot({})
        assert isinstance(result, str)
        assert result == "{}"

    def test_nonempty_dict_returns_str(self) -> None:
        snapshot = {"key": "value", "count": 5}
        result = format_snapshot(snapshot)
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result

    def test_nested_dict_returns_str(self) -> None:
        snapshot = {"outer": {"inner": 1}}
        result = format_snapshot(snapshot)
        assert isinstance(result, str)
        assert "outer" in result

    def test_list_input_returns_str(self) -> None:
        """Lists must also be representable via ``str()``."""
        result = format_snapshot([1, 2, 3])
        assert isinstance(result, str)
        assert "1" in result


# ---------------------------------------------------------------------------
# FR-ORC-SV-004 / FR-ORC-SV-005 -- parse_snapshot_args contract
# ---------------------------------------------------------------------------


class TestParseSnapshotArgsReturnsDict:
    """@trace FR-ORC-SV-004"""

    def test_returns_dict_type(self) -> None:
        """``parse_snapshot_args`` must always return a ``dict``."""
        result = parse_snapshot_args(["--flag"])
        assert isinstance(result, dict)

    def test_nonempty_list_returns_dict(self) -> None:
        result = parse_snapshot_args(["--verbose", "--format=json"])
        assert isinstance(result, dict)

    def test_single_element_list_returns_dict(self) -> None:
        result = parse_snapshot_args(["one"])
        assert isinstance(result, dict)


class TestParseSnapshotArgsEmptyList:
    """@trace FR-ORC-SV-005"""

    def test_empty_list_returns_empty_dict(self) -> None:
        """An empty args list must yield an empty ``dict``."""
        result = parse_snapshot_args([])
        assert isinstance(result, dict)
        assert result == {}

    def test_empty_list_return_value_is_not_none(self) -> None:
        result = parse_snapshot_args([])
        assert result is not None


# ---------------------------------------------------------------------------
# FR-ORC-SV-006 / FR-ORC-SV-007 -- snapshot_daily_export_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotDailyExportPayload:
    """@trace FR-ORC-SV-006 / FR-ORC-SV-007"""

    def test_returns_dict(self) -> None:
        result = snapshot_daily_export_payload("2025-01-15")
        assert isinstance(result, dict)

    def test_contains_date_key(self) -> None:
        """The payload must include a ``'date'`` key (FR-ORC-SV-006)."""
        result = snapshot_daily_export_payload("2025-01-15")
        assert "date" in result

    def test_date_value_matches_input(self) -> None:
        result = snapshot_daily_export_payload("2025-01-15")
        assert result["date"] == "2025-01-15"

    def test_contains_snapshots_key(self) -> None:
        """The payload must include a ``'snapshots'`` key (FR-ORC-SV-007)."""
        result = snapshot_daily_export_payload("2025-01-15")
        assert "snapshots" in result

    def test_snapshots_value_is_list(self) -> None:
        result = snapshot_daily_export_payload("2025-01-15")
        assert isinstance(result["snapshots"], list)

    def test_snapshots_defaults_to_empty(self) -> None:
        result = snapshot_daily_export_payload("2025-01-15")
        assert result["snapshots"] == []

    def test_idempotent_call(self) -> None:
        """Calling twice with the same date yields identical payloads."""
        a = snapshot_daily_export_payload("2025-01-15")
        b = snapshot_daily_export_payload("2025-01-15")
        assert a == b


# ---------------------------------------------------------------------------
# FR-ORC-SV-008 / FR-ORC-SV-009 -- snapshot_daily_index_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotDailyIndexPayload:
    """@trace FR-ORC-SV-008 / FR-ORC-SV-009"""

    def test_returns_dict(self) -> None:
        result = snapshot_daily_index_payload("2025-03-01")
        assert isinstance(result, dict)

    def test_contains_date_key(self) -> None:
        """The payload must include a ``'date'`` key (FR-ORC-SV-008)."""
        result = snapshot_daily_index_payload("2025-03-01")
        assert "date" in result

    def test_date_value_matches_input(self) -> None:
        result = snapshot_daily_index_payload("2025-03-01")
        assert result["date"] == "2025-03-01"

    def test_contains_index_key(self) -> None:
        """The payload must include an ``'index'`` key (FR-ORC-SV-009)."""
        result = snapshot_daily_index_payload("2025-03-01")
        assert "index" in result

    def test_index_value_is_list(self) -> None:
        result = snapshot_daily_index_payload("2025-03-01")
        assert isinstance(result["index"], list)

    def test_index_defaults_to_empty(self) -> None:
        result = snapshot_daily_index_payload("2025-03-01")
        assert result["index"] == []


# ---------------------------------------------------------------------------
# FR-ORC-SV-010 / FR-ORC-SV-011 -- snapshot_daily_totals_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotDailyTotalsPayload:
    """@trace FR-ORC-SV-010 / FR-ORC-SV-011"""

    def test_returns_dict(self) -> None:
        result = snapshot_daily_totals_payload("2025-06-21")
        assert isinstance(result, dict)

    def test_contains_date_key(self) -> None:
        """The payload must include a ``'date'`` key (FR-ORC-SV-010)."""
        result = snapshot_daily_totals_payload("2025-06-21")
        assert "date" in result

    def test_date_value_matches_input(self) -> None:
        result = snapshot_daily_totals_payload("2025-06-21")
        assert result["date"] == "2025-06-21"

    def test_contains_totals_key(self) -> None:
        """The payload must include a ``'totals'`` key (FR-ORC-SV-011)."""
        result = snapshot_daily_totals_payload("2025-06-21")
        assert "totals" in result

    def test_totals_value_is_dict(self) -> None:
        result = snapshot_daily_totals_payload("2025-06-21")
        assert isinstance(result["totals"], dict)

    def test_totals_defaults_to_empty(self) -> None:
        result = snapshot_daily_totals_payload("2025-06-21")
        assert result["totals"] == {}


# ---------------------------------------------------------------------------
# FR-ORC-SV-012 -- snapshot_export_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotExportPayload:
    """@trace FR-ORC-SV-012"""

    def test_returns_dict(self) -> None:
        result = snapshot_export_payload("2025-07-01")
        assert isinstance(result, dict)

    def test_contains_date_key(self) -> None:
        result = snapshot_export_payload("2025-07-01")
        assert "date" in result

    def test_contains_data_key(self) -> None:
        """The payload must include a ``'data'`` key (FR-ORC-SV-012)."""
        result = snapshot_export_payload("2025-07-01")
        assert "data" in result

    def test_date_value_matches_input(self) -> None:
        result = snapshot_export_payload("2025-07-01")
        assert result["date"] == "2025-07-01"

    def test_data_value_is_dict(self) -> None:
        result = snapshot_export_payload("2025-07-01")
        assert isinstance(result["data"], dict)

    def test_session_id_none_by_default(self) -> None:
        result = snapshot_export_payload("2025-07-01")
        assert result["session_id"] is None

    def test_session_id_forwarded_when_provided(self) -> None:
        result = snapshot_export_payload("2025-07-01", session_id="sess-abc")
        assert result["session_id"] == "sess-abc"

    def test_with_session_id_still_has_date_and_data(self) -> None:
        """FR-ORC-SV-012 invariants must hold regardless of session_id."""
        result = snapshot_export_payload("2025-07-01", session_id="sess-xyz")
        assert "date" in result
        assert "data" in result


# ---------------------------------------------------------------------------
# FR-ORC-SV-013 -- snapshot_index_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotIndexPayload:
    """@trace FR-ORC-SV-013"""

    def test_returns_dict(self) -> None:
        result = snapshot_index_payload("2025-08-10")
        assert isinstance(result, dict)

    def test_contains_date_key(self) -> None:
        result = snapshot_index_payload("2025-08-10")
        assert "date" in result

    def test_contains_index_key(self) -> None:
        """The payload must include an ``'index'`` key (FR-ORC-SV-013)."""
        result = snapshot_index_payload("2025-08-10")
        assert "index" in result

    def test_date_value_matches_input(self) -> None:
        result = snapshot_index_payload("2025-08-10")
        assert result["date"] == "2025-08-10"

    def test_index_value_is_list(self) -> None:
        result = snapshot_index_payload("2025-08-10")
        assert isinstance(result["index"], list)

    def test_session_id_none_by_default(self) -> None:
        result = snapshot_index_payload("2025-08-10")
        assert result["session_id"] is None

    def test_session_id_forwarded_when_provided(self) -> None:
        result = snapshot_index_payload("2025-08-10", session_id="sess-42")
        assert result["session_id"] == "sess-42"

    def test_with_session_id_still_has_date_and_index(self) -> None:
        """FR-ORC-SV-013 invariants must hold regardless of session_id."""
        result = snapshot_index_payload("2025-08-10", session_id="sess-42")
        assert "date" in result
        assert "index" in result


# ---------------------------------------------------------------------------
# FR-ORC-SV-014 -- snapshot_prune_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotPrunePayload:
    """@trace FR-ORC-SV-014"""

    def test_returns_dict(self) -> None:
        result = snapshot_prune_payload("2025-09-01")
        assert isinstance(result, dict)

    def test_action_is_prune(self) -> None:
        """The payload must set ``'action'`` to ``'prune'`` (FR-ORC-SV-014)."""
        result = snapshot_prune_payload("2025-09-01")
        assert result["action"] == "prune"

    def test_contains_date_key(self) -> None:
        result = snapshot_prune_payload("2025-09-01")
        assert "date" in result
        assert result["date"] == "2025-09-01"

    def test_session_ids_none_defaults_to_empty_list(self) -> None:
        result = snapshot_prune_payload("2025-09-01")
        assert result["session_ids"] == []

    def test_session_ids_forwarded_when_provided(self) -> None:
        ids = ["s1", "s2", "s3"]
        result = snapshot_prune_payload("2025-09-01", session_ids=ids)
        assert result["session_ids"] == ids

    def test_empty_session_ids_list_preserved(self) -> None:
        result = snapshot_prune_payload("2025-09-01", session_ids=[])
        assert result["session_ids"] == []

    def test_action_always_prune_regardless_of_session_ids(self) -> None:
        """FR-ORC-SV-014 invariant must hold for any session_ids value."""
        result_with_ids = snapshot_prune_payload("2025-09-01", session_ids=["a"])
        result_without = snapshot_prune_payload("2025-09-01")
        assert result_with_ids["action"] == "prune"
        assert result_without["action"] == "prune"


# ---------------------------------------------------------------------------
# FR-ORC-SV-015 -- snapshot_list_payload contract
# ---------------------------------------------------------------------------


class TestSnapshotListPayload:
    """@trace FR-ORC-SV-015"""

    def test_returns_dict(self) -> None:
        result = snapshot_list_payload([])
        assert isinstance(result, dict)

    def test_count_matches_length(self) -> None:
        """``'count'`` must equal ``len(snapshots)`` (FR-ORC-SV-015)."""
        snapshots = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        result = snapshot_list_payload(snapshots)
        assert result["count"] == len(snapshots)

    def test_count_is_zero_for_empty_list(self) -> None:
        result = snapshot_list_payload([])
        assert result["count"] == 0

    def test_count_is_one_for_single_element(self) -> None:
        result = snapshot_list_payload(["only"])
        assert result["count"] == 1

    def test_snapshots_key_preserves_input(self) -> None:
        snapshots = ["a", "b"]
        result = snapshot_list_payload(snapshots)
        assert result["snapshots"] == snapshots

    def test_count_with_large_list(self) -> None:
        snapshots = list(range(1000))
        result = snapshot_list_payload(snapshots)
        assert result["count"] == 1000


# ---------------------------------------------------------------------------
# snapshot_triggers_tags_payload contract (extending the FR surface)
# ---------------------------------------------------------------------------


class TestSnapshotTriggersTagsPayload:
    """Extends AUDIT-N+45 coverage for ``snapshot_triggers_tags_payload``."""

    def test_returns_dict(self) -> None:
        result = snapshot_triggers_tags_payload(["tag1"])
        assert isinstance(result, dict)

    def test_contains_tags_key(self) -> None:
        result = snapshot_triggers_tags_payload(["important", "urgent"])
        assert "tags" in result
        assert result["tags"] == ["important", "urgent"]

    def test_count_matches_length(self) -> None:
        tags = ["a", "b", "c"]
        result = snapshot_triggers_tags_payload(tags)
        assert result["count"] == len(tags)

    def test_empty_tags_list(self) -> None:
        result = snapshot_triggers_tags_payload([])
        assert result["tags"] == []
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# SessionSnapshotCLIHelpers class contract
# ---------------------------------------------------------------------------


class TestSessionSnapshotCLIHelpersClass:
    """Verify the class itself is importable and instantiable."""

    def test_class_is_importable(self) -> None:
        assert SessionSnapshotCLIHelpers is not None

    def test_class_is_instantiable(self) -> None:
        instance = SessionSnapshotCLIHelpers()
        assert instance is not None

    def test_class_is_not_abstract(self) -> None:
        """The class must be concrete enough to instantiate."""
        instance = SessionSnapshotCLIHelpers()
        assert isinstance(instance, SessionSnapshotCLIHelpers)


# ---------------------------------------------------------------------------
# Module-level surface area (mirrors FR-ORC-SS-015 pattern)
# ---------------------------------------------------------------------------


class TestModuleSurfaceArea:
    """Verify every public function is importable from the module."""

    def test_format_snapshot_importable(self) -> None:
        assert callable(format_snapshot)

    def test_parse_snapshot_args_importable(self) -> None:
        assert callable(parse_snapshot_args)

    def test_snapshot_daily_export_payload_importable(self) -> None:
        assert callable(snapshot_daily_export_payload)

    def test_snapshot_daily_index_payload_importable(self) -> None:
        assert callable(snapshot_daily_index_payload)

    def test_snapshot_daily_totals_payload_importable(self) -> None:
        assert callable(snapshot_daily_totals_payload)

    def test_snapshot_export_payload_importable(self) -> None:
        assert callable(snapshot_export_payload)

    def test_snapshot_index_payload_importable(self) -> None:
        assert callable(snapshot_index_payload)

    def test_snapshot_prune_payload_importable(self) -> None:
        assert callable(snapshot_prune_payload)

    def test_snapshot_list_payload_importable(self) -> None:
        assert callable(snapshot_list_payload)

    def test_snapshot_triggers_tags_payload_importable(self) -> None:
        assert callable(snapshot_triggers_tags_payload)
