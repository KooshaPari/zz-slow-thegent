"""Unit tests for cli_impl.py coverage gaps.

Covers uncovered branches and edge cases in:
- _resolve_cwd cache exception path
- _resolve_agent_model for all providers
- _normalize_output_format edge cases
- _run_background_session_observer deeper paths
- _session_scope_dirs fallback / empty-owner
- _session_status_for various states
- _ensure_evidence_header / _ensure_contract_version_header
- _dag_update_task all fields
- _resolve_prompt file-based resolution
- _parse_observe_summary_timestamp edge cases
- _parse_observe_summary_env_float / _parse_observe_summary_env_int
- _observe_summary_freshness_bucket all buckets
- _load_observe_summary_snapshots matching logic
- _classify_observe_summary_trend_health all penalty paths
- _append_observe_summary_snapshot OSError path
- _compact_health_snapshot_log trimming
- _health_snapshot_max_lines env parsing
- _coerce_issue_types all input types
- _load_previous_health_snapshot matching and errors
- _append_health_snapshot for report and gate payloads
- _resolve_health_policy all profiles
- _health_scope_key payload types
- _hash_health_payload / _hash_observe_summary_payload
- _build_observe_summary_trend_scope
- _hash_observe_summary_trend_scope
- _parse_dag_full with no frontmatter / empty table
- _validate_dag done-without-evidence
- _get_ready_task_ids with cancelled/skipped deps
- _check_dag_cycles unknown dep / cycle detection
- _atomic_write with backup
- get_server_meta_impl
- get_data_protection_status_impl
"""

import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest
import typer

from thegent.cli.commands.impl import (
    DagDocument,
    _append_health_snapshot,
    _append_observe_summary_snapshot,
    _atomic_write,
    _build_observe_summary_trend_scope,
    _check_dag_cycles,
    _classify_observe_summary_trend_health,
    _coerce_issue_types,
    _compact_health_snapshot_log,
    _dag_update_task,
    _ensure_contract_version_header,
    _ensure_dag_file,
    _ensure_evidence_header,
    _escape_cell,
    _get_ready_task_ids,
    _hash_health_payload,
    _hash_observe_summary_payload,
    _hash_observe_summary_trend_scope,
    _health_scope_key,
    _health_snapshot_max_lines,
    _load_observe_summary_snapshots,
    _load_previous_health_snapshot,
    _normalize_output_format,
    _observe_summary_freshness_bucket,
    _parse_dag_full,
    _parse_depends_on,
    _parse_observe_summary_env_float,
    _parse_observe_summary_env_int,
    _parse_observe_summary_timestamp,
    _resolve_agent_model,
    _resolve_cwd,
    _resolve_health_policy,
    _resolve_prompt,
    _run_background_session_observer,
    _serialize_dag,
    _session_scope_dirs,
    _session_status_for,
    _validate_dag,
    _validate_task_id,
    get_server_meta_impl,
)


# ---------------------------------------------------------------------------
# _resolve_cwd: cache exception fallback (lines 79-85)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdCacheException:
    # @trace FR-CLI-400
    def test_cache_hit_returns_cached_value(self, tmp_path) -> None:
        """When the cache has a non-expired entry, the cached value is returned."""
        from thegent.cli.commands.impl import _CWD_CACHE

        project = tmp_path / "proj"
        project.mkdir()
        (project / ".git").mkdir()
        # Prime cache
        _resolve_cwd(project)
        cache_key = str(project.resolve())
        assert cache_key in _CWD_CACHE
        # Second call should hit cache
        result = _resolve_cwd(project)
        assert result == project.resolve()

    # @trace FR-CLI-401
    def test_expired_cache_is_refreshed(self, tmp_path) -> None:
        """When the cache entry is expired (TTL passed), the resolution runs again."""
        from thegent.cli.commands.impl import _CWD_CACHE

        project = tmp_path / "proj2"
        project.mkdir()
        (project / ".git").mkdir()
        _resolve_cwd(project)
        cache_key = str(project.resolve())
        # With TTLCache, we simulate expiration by removing the key
        # TTLCache automatically expires entries after TTL
        del _CWD_CACHE[cache_key]
        result = _resolve_cwd(project)
        assert result == project.resolve()


# ---------------------------------------------------------------------------
# _resolve_agent_model: all provider branches (lines 114-143)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveAgentModel:
    # @trace FR-CLI-402
    def test_explicit_model_returned_as_is(self) -> None:
        settings = MagicMock()
        result = _resolve_agent_model("claude", "my-model", "write", settings)
        assert result == "my-model"

    # @trace FR-CLI-403
    def test_cursor_agent_uses_default_cursor_model(self) -> None:
        settings = MagicMock()
        settings.default_cursor_model = "cursor-model-x"
        assert _resolve_agent_model("cursor-agent", None, "write", settings) == "cursor-model-x"

    # @trace FR-CLI-404
    def test_cursor_alias_uses_default_cursor_model(self) -> None:
        settings = MagicMock()
        settings.default_cursor_model = "cursor-model-y"
        assert _resolve_agent_model("cursor", None, "write", settings) == "cursor-model-y"

    # @trace FR-CLI-405
    def test_gemini_uses_default_gemini_model(self) -> None:
        settings = MagicMock()
        settings.default_gemini_model = "gemini-2.0"
        assert _resolve_agent_model("gemini", None, "write", settings) == "gemini-2.0"

    # @trace FR-CLI-406
    def test_copilot_uses_default_copilot_model(self) -> None:
        settings = MagicMock()
        settings.default_copilot_model = "copilot-m"
        assert _resolve_agent_model("copilot", None, "write", settings) == "copilot-m"

    # @trace FR-CLI-407
    def test_claude_uses_default_claude_model(self) -> None:
        settings = MagicMock()
        settings.default_claude_model = "haiku"
        assert _resolve_agent_model("claude", None, "write", settings) == "haiku"

    # @trace FR-CLI-408
    def test_codex_uses_default_codex_model(self) -> None:
        settings = MagicMock()
        settings.default_codex_model = "gpt-5.3-codex"
        assert _resolve_agent_model("codex", None, "write", settings) == "gpt-5.3-codex"

    # @trace FR-CLI-409
    def test_codex_full_mode_uses_high_model(self) -> None:
        settings = MagicMock()
        settings.default_codex_model_high = "gpt-5.3-codex-high"
        assert _resolve_agent_model("codex", None, "full", settings) == "gpt-5.3-codex-high"

    # @trace FR-CLI-410
    def test_antigravity_uses_default_antigravity_model(self) -> None:
        settings = MagicMock()
        settings.default_antigravity_model = "ag-model"
        assert _resolve_agent_model("antigravity", None, "write", settings) == "ag-model"

    # @trace FR-CLI-411
    def test_minimax_returns_hardcoded(self) -> None:
        settings = MagicMock()
        assert _resolve_agent_model("minimax", None, "write", settings) == "minimax-m2.5"

    # @trace FR-CLI-412
    def test_glm_returns_hardcoded(self) -> None:
        settings = MagicMock()
        assert _resolve_agent_model("glm", None, "write", settings) == "glm-5"

    # @trace FR-CLI-413
    def test_roo_returns_hardcoded(self) -> None:
        settings = MagicMock()
        assert _resolve_agent_model("roo", None, "write", settings) == "roo-default"

    # @trace FR-CLI-414
    def test_kilo_returns_hardcoded(self) -> None:
        settings = MagicMock()
        assert _resolve_agent_model("kilo", None, "write", settings) == "kilo-default"

    # @trace FR-CLI-415
    def test_unknown_agent_returns_none(self) -> None:
        settings = MagicMock()
        assert _resolve_agent_model("nonexistent-agent", None, "write", settings) is None


# ---------------------------------------------------------------------------
# _normalize_output_format edge cases (lines 271-277)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeOutputFormat:
    # @trace FR-CLI-416
    def test_json_format(self) -> None:
        assert _normalize_output_format("json") == "json"

    # @trace FR-CLI-417
    def test_md_format(self) -> None:
        assert _normalize_output_format("md") == "md"

    # @trace FR-CLI-418
    def test_rich_format(self) -> None:
        assert _normalize_output_format("rich") == "rich"

    # @trace FR-CLI-419
    def test_unknown_nonempty_falls_back_to_rich(self) -> None:
        assert _normalize_output_format("csv") == "rich"

    # @trace FR-CLI-420
    def test_none_uses_default(self) -> None:
        assert _normalize_output_format(None) == "rich"

    # @trace FR-CLI-421
    def test_none_with_custom_default(self) -> None:
        assert _normalize_output_format(None, default="json") == "json"

    # @trace FR-CLI-422
    def test_env_override(self) -> None:
        with patch.dict(os.environ, {"THGENT_OUTPUT_FORMAT": "md"}):
            assert _normalize_output_format(None) == "md"


# ---------------------------------------------------------------------------
# _run_background_session_observer deeper paths (lines 298-333)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunBackgroundSessionObserver:
    # @trace FR-CLI-423
    def test_no_meta_path_env_returns_early(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("THGENT_SESSION_META_PATH", None)
            _run_background_session_observer(0)

    # @trace FR-CLI-424
    def test_meta_path_not_exists_returns_early(self, tmp_path) -> None:
        meta = tmp_path / "nonexistent.json"
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            _run_background_session_observer(0)

    # @trace FR-CLI-425
    def test_updates_meta_and_rc_on_success(self, tmp_path) -> None:
        meta = tmp_path / "sess.json"
        rc = tmp_path / "sess.rc"
        started = datetime.now(UTC).isoformat()
        meta.write_text(json.dumps({"status": "running", "started_at_utc": started}).decode())
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta),
                "THGENT_SESSION_RC_PATH": str(rc),
            },
        ):
            _run_background_session_observer(0, timed_out=False)
        updated = json.loads(meta.read_text())
        assert updated["status"] == "exited"
        assert updated["exit_code"] == 0
        assert updated["timed_out"] is False
        assert "duration_seconds" in updated
        assert rc.read_text().strip() == "0"

    # @trace FR-CLI-426
    def test_timed_out_flag_preserved(self, tmp_path) -> None:
        meta = tmp_path / "sess2.json"
        meta.write_text(json.dumps({"status": "running"}).decode())
        with patch.dict(os.environ, {"THGENT_SESSION_META_PATH": str(meta)}):
            _run_background_session_observer(137, timed_out=True)
        updated = json.loads(meta.read_text())
        assert updated["timed_out"] is True
        assert updated["exit_code"] == 137

    # @trace FR-CLI-427
    def test_rc_write_oserror_ignored(self, tmp_path) -> None:
        meta = tmp_path / "sess3.json"
        meta.write_text(json.dumps({"status": "running"}).decode())
        rc_path = tmp_path / "readonly_dir" / "sess3.rc"
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta),
                "THGENT_SESSION_RC_PATH": str(rc_path),
            },
        ):
            # Should not raise even though rc_path parent does not exist
            _run_background_session_observer(1)


# ---------------------------------------------------------------------------
# _session_scope_dirs edge cases (lines 209-222)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionScopeDirs:
    # @trace FR-CLI-428
    def test_empty_owner_returns_empty(self, tmp_path) -> None:
        assert _session_scope_dirs(tmp_path, "") == []

    # @trace FR-CLI-429
    def test_fallback_when_no_glob_match(self, tmp_path) -> None:
        fallback = tmp_path / "mykey"
        fallback.mkdir()
        result = _session_scope_dirs(tmp_path, "my:key")
        # _scope_key("my:key") -> "my_key" but fallback dir is "mykey"
        # This tests the glob-miss + fallback-exists path
        from thegent.cli.commands.impl import _scope_key

        key = _scope_key("my:key")
        fb = tmp_path / key
        fb.mkdir(exist_ok=True)
        result = _session_scope_dirs(tmp_path, "my:key")
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# _session_status_for (lines 594-605)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionStatusFor:
    # @trace FR-CLI-430
    def test_not_found_on_missing_session(self) -> None:
        settings = MagicMock()
        settings.session_dir = Path("/tmp/nonexistent_thegent_test")
        with patch(
            "thegent.cli.commands.impl._find_session_meta",
            side_effect=typer.BadParameter("not found"),
        ):
            result = _session_status_for("nonexistent", settings)
        assert result == "not_found"

    # @trace FR-CLI-431
    def test_running_status(self, tmp_path) -> None:
        settings = MagicMock()
        meta = tmp_path / "sess.json"
        meta.write_text(json.dumps({"pid": 99999}).decode())
        tmp_path / "sess.rc"
        with patch("thegent.cli.commands.impl._find_session_meta", return_value=meta):
            with patch("thegent.cli.commands.impl._is_pid_running", return_value=True):
                result = _session_status_for("sess", settings)
        assert result == "running"

    # @trace FR-CLI-432
    def test_exited_with_rc(self, tmp_path) -> None:
        settings = MagicMock()
        meta = tmp_path / "sess.json"
        meta.write_text(json.dumps({"pid": 12345}).decode())
        rc = tmp_path / "sess.rc"
        rc.write_text("42\n")
        with patch("thegent.cli.commands.impl._find_session_meta", return_value=meta):
            with patch("thegent.cli.commands.impl._is_pid_running", return_value=False):
                result = _session_status_for("sess", settings)
        assert result == "exited:42"

    # @trace FR-CLI-433
    def test_exited_no_rc(self, tmp_path) -> None:
        settings = MagicMock()
        meta = tmp_path / "sess.json"
        meta.write_text(json.dumps({"pid": 12345}).decode())
        with patch("thegent.cli.commands.impl._find_session_meta", return_value=meta):
            with patch("thegent.cli.commands.impl._is_pid_running", return_value=False):
                result = _session_status_for("sess", settings)
        assert result == "exited"


# ---------------------------------------------------------------------------
# _ensure_evidence_header / _ensure_contract_version_header (lines 608-631)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEnsureHeaders:
    # @trace FR-CLI-434
    def test_evidence_header_added_after_status(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done", "evidence": "s1"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        _ensure_evidence_header(doc)
        assert "evidence" in doc.table_headers
        assert doc.table_headers.index("evidence") == doc.table_headers.index("status") + 1

    # @trace FR-CLI-435
    def test_evidence_header_not_added_when_already_present(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done", "evidence": "s1"}],
            before_table="",
            after_table="",
            table_headers=["id", "status", "evidence"],
        )
        _ensure_evidence_header(doc)
        assert doc.table_headers.count("evidence") == 1

    # @trace FR-CLI-436
    def test_evidence_header_appended_when_no_status_column(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "evidence": "s1"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent"],
        )
        _ensure_evidence_header(doc)
        assert doc.table_headers[-1] == "evidence"

    # @trace FR-CLI-437
    def test_evidence_header_empty_headers_initialized(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "evidence": "s1"}],
            before_table="",
            after_table="",
            table_headers=[],
        )
        _ensure_evidence_header(doc)
        assert "id" in doc.table_headers

    # @trace FR-CLI-438
    def test_contract_version_header_added(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done", "contract_version": "v2"}],
            before_table="",
            after_table="",
            table_headers=["id", "status"],
        )
        _ensure_contract_version_header(doc)
        assert "contract_version" in doc.table_headers

    # @trace FR-CLI-439
    def test_contract_version_header_not_added_when_no_tasks_have_it(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done"}],
            before_table="",
            after_table="",
            table_headers=["id", "status"],
        )
        _ensure_contract_version_header(doc)
        assert "contract_version" not in doc.table_headers

    # @trace FR-CLI-440
    def test_contract_version_appended_when_no_status(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "contract_version": "v2"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent"],
        )
        _ensure_contract_version_header(doc)
        assert doc.table_headers[-1] == "contract_version"

    # @trace FR-CLI-441
    def test_contract_version_empty_headers_returns_early(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "contract_version": "v2"}],
            before_table="",
            after_table="",
            table_headers=[],
        )
        _ensure_contract_version_header(doc)
        assert doc.table_headers == []


# ---------------------------------------------------------------------------
# _dag_update_task all fields (lines 633-667)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDagUpdateTask:
    # @trace FR-CLI-442
    def test_update_all_fields(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "pending", "agent": "claude", "prompt": "old"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        result = _dag_update_task(
            doc,
            "T1",
            status="running",
            session_id="sess-123",
            prompt="new prompt",
            agent="gemini",
            depends_on="T0",
            retry_count=2,
            contract_version="v3",
        )
        assert result is True
        t = doc.tasks[0]
        assert t["status"] == "running"
        assert t["evidence"] == "sess-123"
        assert t["prompt"] == "new prompt"
        assert t["agent"] == "gemini"
        assert t["depends_on"] == "T0"
        assert t["retry_count"] == "2"
        assert t["contract_version"] == "v3"

    # @trace FR-CLI-443
    def test_update_nonexistent_task_returns_false(self) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "pending"}],
            before_table="",
            after_table="",
            table_headers=["id", "status"],
        )
        assert _dag_update_task(doc, "NONEXISTENT", status="done") is False


# ---------------------------------------------------------------------------
# _resolve_prompt file-based resolution (lines 697-703)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolvePrompt:
    # @trace FR-CLI-444
    def test_inline_prompt_returned(self, tmp_path) -> None:
        assert _resolve_prompt("T1", "do the thing", tmp_path) == "do the thing"

    # @trace FR-CLI-445
    def test_file_reference_resolved(self, tmp_path) -> None:
        prompt_file = tmp_path / ".factory" / "prompts" / "T1.md"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("file-based prompt content")
        result = _resolve_prompt("T1", "@.factory/prompts/T1.md", tmp_path)
        assert result == "file-based prompt content"

    # @trace FR-CLI-446
    def test_file_reference_missing_returns_raw(self, tmp_path) -> None:
        result = _resolve_prompt("T1", "@.factory/prompts/missing.md", tmp_path)
        assert result == "@.factory/prompts/missing.md"


# ---------------------------------------------------------------------------
# _parse_observe_summary_timestamp edge cases (lines 765-778)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestParseObserveSummaryTimestamp:
    # @trace FR-CLI-447
    def test_none_returns_none(self) -> None:
        assert _parse_observe_summary_timestamp(None) is None

    # @trace FR-CLI-448
    def test_empty_returns_none(self) -> None:
        assert _parse_observe_summary_timestamp("") is None

    # @trace FR-CLI-449
    def test_valid_iso_parsed(self) -> None:
        result = _parse_observe_summary_timestamp("2025-01-15T10:30:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    # @trace FR-CLI-450
    def test_z_suffix_handled(self) -> None:
        result = _parse_observe_summary_timestamp("2025-01-15T10:30:00Z")
        assert result is not None

    # @trace FR-CLI-451
    def test_naive_datetime_gets_utc(self) -> None:
        result = _parse_observe_summary_timestamp("2025-01-15T10:30:00")
        assert result is not None
        assert result.tzinfo == UTC

    # @trace FR-CLI-452
    def test_invalid_returns_none(self) -> None:
        assert _parse_observe_summary_timestamp("not-a-date") is None


# ---------------------------------------------------------------------------
# _parse_observe_summary_env_float / _parse_observe_summary_env_int
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestParseObserveSummaryEnvHelpers:
    # @trace FR-CLI-453
    def test_env_float_missing_returns_default(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("THGENT_TEST_FLOAT", None)
            assert _parse_observe_summary_env_float("THGENT_TEST_FLOAT", 3.14) == 3.14

    # @trace FR-CLI-454
    def test_env_float_invalid_returns_default(self) -> None:
        with patch.dict(os.environ, {"THGENT_TEST_FLOAT": "abc"}):
            assert _parse_observe_summary_env_float("THGENT_TEST_FLOAT", 2.0) == 2.0

    # @trace FR-CLI-455
    def test_env_float_valid(self) -> None:
        with patch.dict(os.environ, {"THGENT_TEST_FLOAT": "9.5"}):
            assert _parse_observe_summary_env_float("THGENT_TEST_FLOAT", 0.0) == 9.5

    # @trace FR-CLI-456
    def test_env_int_missing_returns_default(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("THGENT_TEST_INT", None)
            assert _parse_observe_summary_env_int("THGENT_TEST_INT", 42) == 42

    # @trace FR-CLI-457
    def test_env_int_invalid_returns_default(self) -> None:
        with patch.dict(os.environ, {"THGENT_TEST_INT": "xyz"}):
            assert _parse_observe_summary_env_int("THGENT_TEST_INT", 10) == 10

    # @trace FR-CLI-458
    def test_env_int_valid(self) -> None:
        with patch.dict(os.environ, {"THGENT_TEST_INT": "77"}):
            assert _parse_observe_summary_env_int("THGENT_TEST_INT", 0) == 77


# ---------------------------------------------------------------------------
# _observe_summary_freshness_bucket all branches (lines 803-820)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryFreshnessBucket:
    # @trace FR-CLI-459
    def test_none_returns_unknown(self) -> None:
        result = _observe_summary_freshness_bucket(
            None,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "unknown"

    # @trace FR-CLI-460
    def test_negative_returns_future(self) -> None:
        result = _observe_summary_freshness_bucket(
            -10,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "future"

    # @trace FR-CLI-461
    def test_within_fresh(self) -> None:
        result = _observe_summary_freshness_bucket(
            30,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "fresh"

    # @trace FR-CLI-462
    def test_within_warm(self) -> None:
        result = _observe_summary_freshness_bucket(
            100,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "warm"

    # @trace FR-CLI-463
    def test_within_stale(self) -> None:
        result = _observe_summary_freshness_bucket(
            400,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "stale"

    # @trace FR-CLI-464
    def test_beyond_stale_is_critical(self) -> None:
        result = _observe_summary_freshness_bucket(
            1000,
            fresh_seconds=60,
            warm_seconds=300,
            stale_seconds=600,
        )
        assert result == "critical"


# ---------------------------------------------------------------------------
# _classify_observe_summary_trend_health (lines 858-1040)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestClassifyObserveSummaryTrendHealth:
    # @trace FR-CLI-465
    def test_disabled_returns_disabled_health(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=False,
            baseline_available=False,
            trend_snapshot_coverage_pct=None,
            trend_snapshot_deficit=0,
            trend_snapshot_invalid_timestamps=0,
            trend_snapshot_freshness_bucket="unknown",
            trend_snapshot_gap_count=0,
            trend_sampling_mode="disabled",
        )
        assert result["trend_snapshot_health"] == "disabled"
        assert result["trend_snapshot_health_score"] is None

    # @trace FR-CLI-466
    def test_good_health_with_full_coverage(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=True,
            trend_snapshot_coverage_pct=100.0,
            trend_snapshot_deficit=0,
            trend_snapshot_invalid_timestamps=0,
            trend_snapshot_freshness_bucket="fresh",
            trend_snapshot_gap_count=0,
            trend_sampling_mode="enabled",
        )
        assert result["trend_snapshot_health"] == "good"
        assert result["trend_snapshot_health_score"] >= 95

    # @trace FR-CLI-467
    def test_degraded_health_with_penalties(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=False,
            trend_snapshot_coverage_pct=50.0,
            trend_snapshot_deficit=2,
            trend_snapshot_invalid_timestamps=1,
            trend_snapshot_freshness_bucket="stale",
            trend_snapshot_gap_count=1,
            trend_sampling_mode="enabled",
        )
        # Missing baseline + low coverage + deficit = many penalties
        assert result["trend_snapshot_health"] in ("degraded", "critical")
        assert result["trend_snapshot_health_score"] is not None

    # @trace FR-CLI-468
    def test_critical_freshness_penalty(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=True,
            trend_snapshot_coverage_pct=100.0,
            trend_snapshot_deficit=0,
            trend_snapshot_invalid_timestamps=0,
            trend_snapshot_freshness_bucket="critical",
            trend_snapshot_gap_count=0,
            trend_sampling_mode="enabled",
        )
        breakdown = result["trend_snapshot_health_breakdown"]
        assert breakdown["freshness"]["penalty"] > 0

    # @trace FR-CLI-469
    def test_future_freshness_penalty(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=True,
            trend_snapshot_coverage_pct=100.0,
            trend_snapshot_deficit=0,
            trend_snapshot_invalid_timestamps=0,
            trend_snapshot_freshness_bucket="future",
            trend_snapshot_gap_count=0,
            trend_sampling_mode="enabled",
        )
        breakdown = result["trend_snapshot_health_breakdown"]
        assert breakdown["freshness"]["penalty"] > 0

    # @trace FR-CLI-470
    def test_coverage_none_no_penalty(self) -> None:
        result = _classify_observe_summary_trend_health(
            enabled=True,
            baseline_available=True,
            trend_snapshot_coverage_pct=None,
            trend_snapshot_deficit=0,
            trend_snapshot_invalid_timestamps=0,
            trend_snapshot_freshness_bucket="fresh",
            trend_snapshot_gap_count=0,
            trend_sampling_mode="enabled",
        )
        breakdown = result["trend_snapshot_health_breakdown"]
        assert breakdown["coverage"]["coverage_penalty"] == 0


# ---------------------------------------------------------------------------
# _load_observe_summary_snapshots matching logic (lines 823-855)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadObserveSummarySnapshots:
    # @trace FR-CLI-471
    def test_no_file_returns_empty(self) -> None:
        with patch(
            "thegent.cli.commands.impl._health_snapshot_log_path",
            return_value=Path("/nonexistent"),
        ):
            result = _load_observe_summary_snapshots("sig1", "{}", 5)
        assert result == []

    # @trace FR-CLI-472
    def test_matching_by_trend_scope_signature(self, tmp_path) -> None:
        log_path = tmp_path / "snapshots.jsonl"
        rec = {
            "record_type": "observe_summary_snapshot",
            "trend_scope_signature": "sig-abc",
            "captured_at_utc": "2025-01-01T00:00:00Z",
        }
        log_path.write_text(json.dumps(rec).decode() + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_observe_summary_snapshots("sig-abc", "{}", 5)
        assert len(result) == 1

    # @trace FR-CLI-473
    def test_matching_by_scope_signature(self, tmp_path) -> None:
        log_path = tmp_path / "snapshots.jsonl"
        rec = {
            "record_type": "observe_summary_snapshot",
            "scope_signature": "sig-def",
            "captured_at_utc": "2025-01-01T00:00:00Z",
        }
        log_path.write_text(json.dumps(rec).decode() + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_observe_summary_snapshots("sig-def", "{}", 5)
        assert len(result) == 1

    # @trace FR-CLI-474
    def test_matching_by_scope_key_json(self, tmp_path) -> None:
        log_path = tmp_path / "snapshots.jsonl"
        key_json = json.dumps({"payload_type": "test"}, sort_keys=True).decode()
        rec = {
            "record_type": "observe_summary_snapshot",
            "scope_key_json": key_json,
            "captured_at_utc": "2025-01-01T00:00:00Z",
        }
        log_path.write_text(json.dumps(rec).decode() + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_observe_summary_snapshots("no-match", key_json, 5)
        assert len(result) == 1

    # @trace FR-CLI-475
    def test_limit_respected(self, tmp_path) -> None:
        log_path = tmp_path / "snapshots.jsonl"
        lines = []
        for i in range(10):
            rec = {
                "record_type": "observe_summary_snapshot",
                "trend_scope_signature": "sig-x",
                "captured_at_utc": f"2025-01-{i + 1:02d}T00:00:00Z",
            }
            lines.append(json.dumps(rec).decode())
        log_path.write_text("\n".join(lines) + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_observe_summary_snapshots("sig-x", "{}", 3)
        assert len(result) == 3

    # @trace FR-CLI-476
    def test_non_matching_records_skipped(self, tmp_path) -> None:
        log_path = tmp_path / "snapshots.jsonl"
        lines = [
            json.dumps({"record_type": "health_snapshot", "scope_key": {}}).decode(),
            json.dumps(
                {
                    "record_type": "observe_summary_snapshot",
                    "trend_scope_signature": "other",
                }
            ).decode(),
            "invalid-json",
            "",
        ]
        log_path.write_text("\n".join(lines) + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_observe_summary_snapshots("sig-z", "{}", 5)
        assert result == []


# ---------------------------------------------------------------------------
# _compact_health_snapshot_log (lines 1196-1211)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCompactHealthSnapshotLog:
    # @trace FR-CLI-477
    def test_no_file_returns_early(self, tmp_path) -> None:
        with patch(
            "thegent.cli.commands.impl._health_snapshot_log_path",
            return_value=tmp_path / "missing.jsonl",
        ):
            _compact_health_snapshot_log()

    # @trace FR-CLI-478
    def test_under_limit_no_trim(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        log_path.write_text("line1\nline2\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=100):
                _compact_health_snapshot_log()
        assert len(log_path.read_text().splitlines()) == 2

    # @trace FR-CLI-479
    def test_over_limit_trims_to_tail(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        lines = [f"line{i}" for i in range(20)]
        log_path.write_text("\n".join(lines) + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5):
                _compact_health_snapshot_log()
        remaining = log_path.read_text().splitlines()
        assert len(remaining) == 5
        assert remaining[-1] == "line19"


# ---------------------------------------------------------------------------
# _health_snapshot_max_lines (lines 1185-1193)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthSnapshotMaxLines:
    # @trace FR-CLI-480
    def test_default_5000(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("THGENT_HEALTH_SNAPSHOT_MAX_LINES", None)
            assert _health_snapshot_max_lines() == 5000

    # @trace FR-CLI-481
    def test_custom_value(self) -> None:
        with patch.dict(os.environ, {"THGENT_HEALTH_SNAPSHOT_MAX_LINES": "200"}):
            assert _health_snapshot_max_lines() == 200

    # @trace FR-CLI-482
    def test_invalid_falls_back_to_5000(self) -> None:
        with patch.dict(os.environ, {"THGENT_HEALTH_SNAPSHOT_MAX_LINES": "abc"}):
            assert _health_snapshot_max_lines() == 5000

    # @trace FR-CLI-483
    def test_below_minimum_clamped_to_100(self) -> None:
        with patch.dict(os.environ, {"THGENT_HEALTH_SNAPSHOT_MAX_LINES": "10"}):
            assert _health_snapshot_max_lines() == 100


# ---------------------------------------------------------------------------
# _coerce_issue_types all input types (lines 1230-1238)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCoerceIssueTypes:
    # @trace FR-CLI-484
    def test_none_returns_empty(self) -> None:
        assert _coerce_issue_types(None) == []

    # @trace FR-CLI-485
    def test_dict_returns_keys(self) -> None:
        result = _coerce_issue_types({"misalign:provider": 2, "missing:model": 1})
        assert set(result) == {"misalign:provider", "missing:model"}

    # @trace FR-CLI-486
    def test_list_returns_strings(self) -> None:
        assert _coerce_issue_types(["a", "b"]) == ["a", "b"]

    # @trace FR-CLI-487
    def test_tuple_returns_strings(self) -> None:
        assert _coerce_issue_types(("x", "y")) == ["x", "y"]

    # @trace FR-CLI-488
    def test_set_returns_strings(self) -> None:
        result = _coerce_issue_types({"one"})
        assert result == ["one"]

    # @trace FR-CLI-489
    def test_scalar_returns_single_item(self) -> None:
        assert _coerce_issue_types("single") == ["single"]
        assert _coerce_issue_types(42) == ["42"]


# ---------------------------------------------------------------------------
# _load_previous_health_snapshot (lines 1241-1261)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadPreviousHealthSnapshot:
    # @trace FR-CLI-490
    def test_no_file_returns_none(self) -> None:
        with patch(
            "thegent.cli.commands.impl._health_snapshot_log_path",
            return_value=Path("/nonexistent"),
        ):
            assert _load_previous_health_snapshot({"type": "test"}) is None

    # @trace FR-CLI-491
    def test_matching_scope_key_found(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        scope = {"type": "gate", "owner": "alice"}
        rec = {
            "record_type": "health_snapshot",
            "scope_key": scope,
            "blocked_ratio": 0.1,
        }
        log_path.write_text(json.dumps(rec).decode() + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_previous_health_snapshot(scope)
        assert result is not None
        assert result["blocked_ratio"] == 0.1

    # @trace FR-CLI-492
    def test_no_matching_scope_returns_none(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        rec = {"record_type": "health_snapshot", "scope_key": {"type": "other"}}
        log_path.write_text(json.dumps(rec).decode() + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            assert _load_previous_health_snapshot({"type": "gate"}) is None

    # @trace FR-CLI-493
    def test_invalid_json_lines_skipped(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        scope = {"type": "gate"}
        lines = [
            "invalid json",
            "",
            json.dumps({"record_type": "health_snapshot", "scope_key": scope, "val": 1}).decode(),
        ]
        log_path.write_text("\n".join(lines) + "\n")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_previous_health_snapshot(scope)
        assert result is not None
        assert result["val"] == 1


# ---------------------------------------------------------------------------
# _resolve_health_policy all profiles (lines 1145-1172)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveHealthPolicy:
    # @trace FR-CLI-494
    def test_strict_ci_profile(self) -> None:
        policy = _resolve_health_policy("strict_ci", False, 0.5)
        assert policy["profile"] == "strict_ci"
        assert policy["strict"] is True
        assert policy["min_healthy_ratio"] == 1.0

    # @trace FR-CLI-495
    def test_warn_only_profile(self) -> None:
        policy = _resolve_health_policy("warn_only", True, 0.9)
        assert policy["profile"] == "warn_only"
        assert policy["strict"] is False
        assert policy["min_healthy_ratio"] == 0.0

    # @trace FR-CLI-496
    def test_prod_release_profile(self) -> None:
        policy = _resolve_health_policy("prod_release", False, 0.5)
        assert policy["profile"] == "prod_release"
        assert policy["min_healthy_ratio"] == 0.98

    # @trace FR-CLI-497
    def test_unknown_profile_uses_custom(self) -> None:
        policy = _resolve_health_policy("nonexistent_profile", True, 0.7)
        assert policy["profile"] == "custom"
        assert policy["profile_exists"] is False
        assert policy["strict"] is True
        assert policy["min_healthy_ratio"] == 0.7

    # @trace FR-CLI-498
    def test_no_profile_uses_custom(self) -> None:
        policy = _resolve_health_policy(None, False, 0.8)
        assert policy["profile"] == "custom"
        assert policy["profile_exists"] is True
        assert policy["min_healthy_ratio"] == 0.8

    # @trace FR-CLI-499
    def test_negative_ratio_clamped_to_zero(self) -> None:
        policy = _resolve_health_policy(None, False, -0.5)
        assert policy["min_healthy_ratio"] == 0.0

    # @trace FR-CLI-500
    def test_ratio_above_one_clamped_to_one(self) -> None:
        policy = _resolve_health_policy(None, False, 1.5)
        assert policy["min_healthy_ratio"] == 1.0


# ---------------------------------------------------------------------------
# _health_scope_key payload types (lines 1214-1227)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthScopeKey:
    # @trace FR-CLI-401
    def test_gate_includes_min_healthy_ratio(self) -> None:
        payload = {
            "payload_type": "session_contract_health_gate",
            "policy_profile": "strict_ci",
            "generated_query": {
                "owner": "alice",
                "all": False,
                "strict": True,
                "min_healthy_ratio": 0.95,
            },
        }
        scope = _health_scope_key(payload)
        assert "min_healthy_ratio" in scope
        assert scope["min_healthy_ratio"] == 0.95

    # @trace FR-CLI-402
    def test_report_includes_top_blocked(self) -> None:
        payload = {
            "payload_type": "session_contract_health_report",
            "policy_profile": "custom",
            "generated_query": {
                "owner": None,
                "all": True,
                "strict": False,
                "top_blocked": 10,
            },
        }
        scope = _health_scope_key(payload)
        assert "top_blocked" in scope
        assert scope["top_blocked"] == 10

    # @trace FR-CLI-403
    def test_other_type_has_no_extra_keys(self) -> None:
        payload = {
            "payload_type": "session_contract_health_trend",
            "policy_profile": "custom",
            "generated_query": {"owner": None, "all": False, "strict": False},
        }
        scope = _health_scope_key(payload)
        assert "min_healthy_ratio" not in scope
        assert "top_blocked" not in scope


# ---------------------------------------------------------------------------
# _hash_health_payload / _hash_observe_summary_payload
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHashPayload:
    # @trace FR-CLI-404
    def test_hash_health_payload_ignores_timestamp(self) -> None:
        p1 = {
            "key": "val",
            "generated_at_utc": "2025-01-01T00:00:00Z",
            "payload_signature": {},
        }
        p2 = {
            "key": "val",
            "generated_at_utc": "2025-12-31T23:59:59Z",
            "payload_signature": {"old": "sig"},
        }
        h1 = _hash_health_payload(p1)
        h2 = _hash_health_payload(p2)
        assert h1["value"] == h2["value"]
        assert h1["algorithm"] == "sha256"

    # @trace FR-CLI-405
    def test_hash_observe_summary_payload_ignores_timestamp(self) -> None:
        p1 = {"data": 1, "generated_at_utc": "a", "payload_signature": {}}
        p2 = {"data": 1, "generated_at_utc": "b", "payload_signature": {"x": 1}}
        h1 = _hash_observe_summary_payload(p1)
        h2 = _hash_observe_summary_payload(p2)
        assert h1["value"] == h2["value"]


# ---------------------------------------------------------------------------
# _build_observe_summary_trend_scope / _hash_observe_summary_trend_scope
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryTrendScope:
    # @trace FR-CLI-406
    def test_scope_structure(self) -> None:
        scope = _build_observe_summary_trend_scope(
            provider="claude",
            drift_window=50,
            structural_budget_pct=5.0,
            semantic_budget_pct=10.0,
            limit=500,
            top_escalations=10,
        )
        assert scope["payload_type"] == "observe_summary"
        assert scope["provider"] == "claude"
        assert scope["drift_window"] == 50

    # @trace FR-CLI-407
    def test_hash_is_deterministic(self) -> None:
        scope = _build_observe_summary_trend_scope(
            provider=None,
            drift_window=50,
            structural_budget_pct=5.0,
            semantic_budget_pct=10.0,
            limit=500,
            top_escalations=10,
        )
        h1 = _hash_observe_summary_trend_scope(scope)
        h2 = _hash_observe_summary_trend_scope(scope)
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex digest


# ---------------------------------------------------------------------------
# _append_health_snapshot (lines 1264-1298)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAppendHealthSnapshot:
    # @trace FR-CLI-408
    def test_report_payload_extracts_issue_types(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch("thegent.cli.commands.impl._compact_health_snapshot_log"):
                payload = {
                    "payload_type": "session_contract_health_report",
                    "issue_counts": {"misalign:provider": 2, "missing:model": 1},
                    "generated_at_utc": "2025-01-01T00:00:00Z",
                }
                _append_health_snapshot(payload, {"type": "report"})
        rec = json.loads(log_path.read_text().strip())
        assert rec["record_type"] == "health_snapshot"
        assert "misalign:provider" in rec["issue_types"]
        assert "missing:model" in rec["issue_types"]

    # @trace FR-CLI-409
    def test_gate_payload_extracts_from_blocked_sessions(self, tmp_path) -> None:
        log_path = tmp_path / "snap.jsonl"
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch("thegent.cli.commands.impl._compact_health_snapshot_log"):
                payload = {
                    "payload_type": "session_contract_health_gate",
                    "blocked_sessions": [
                        {"issues": ["issue_a", "issue_b"]},
                        {"issues": ["issue_b", "issue_c"]},
                    ],
                    "generated_at_utc": "2025-01-01T00:00:00Z",
                }
                _append_health_snapshot(payload, {"type": "gate"})
        rec = json.loads(log_path.read_text().strip())
        assert set(rec["issue_types"]) == {"issue_a", "issue_b", "issue_c"}


# ---------------------------------------------------------------------------
# _append_observe_summary_snapshot OSError path (lines 1043-1110)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAppendObserveSummarySnapshot:
    # @trace FR-CLI-410
    def test_oserror_on_write_handled(self) -> None:
        bad_path = Path("/nonexistent/dir/snap.jsonl")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=bad_path):
            # Should not raise
            _append_observe_summary_snapshot(
                payload={"generated_at_utc": "2025-01-01T00:00:00Z"},
                trend_scope_key={"payload_type": "observe_summary"},
                trend_scope_signature="sig",
                scope_key_json="{}",
                trend_snapshot_ids=[],
                trend_summary={},
            )


# ---------------------------------------------------------------------------
# _parse_dag_full edge cases (lines 391-436)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestParseDagFullEdgeCases:
    # @trace FR-CLI-411
    def test_no_frontmatter(self, tmp_path) -> None:
        dag_file = tmp_path / "dag.md"
        dag_file.write_text(
            "## Tasks\n\n"
            "| ID | Agent | Prompt | Depends_on | Status |\n"
            "|---|---|---|---|---|\n"
            "| T1 | claude | do stuff | - | pending |\n"
        )
        doc = _parse_dag_full(dag_file)
        assert doc.frontmatter == {}
        assert len(doc.tasks) == 1
        assert doc.tasks[0]["id"] == "T1"

    # @trace FR-CLI-412
    def test_empty_table(self, tmp_path) -> None:
        dag_file = tmp_path / "dag.md"
        dag_file.write_text("---\nversion: 1\n---\n## Tasks\n\n| ID | Status |\n|---|---|\n")
        doc = _parse_dag_full(dag_file)
        assert doc.tasks == []
        assert len(doc.table_headers) == 2

    # @trace FR-CLI-413
    def test_after_table_content_preserved(self, tmp_path) -> None:
        dag_file = tmp_path / "dag.md"
        dag_file.write_text("## Tasks\n\n| ID | Status |\n|---|---|\n| T1 | done |\n\n## Notes\n\nSome notes here.\n")
        doc = _parse_dag_full(dag_file)
        assert "Notes" in doc.after_table


# ---------------------------------------------------------------------------
# _validate_dag: done-without-evidence (lines 563-567)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateDagDoneWithoutEvidence:
    # @trace FR-CLI-414
    @patch("thegent.cli.commands.impl._validate_agent", return_value=None)
    def test_done_without_evidence_flagged(self, mock_agent) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "done",
                }
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        errors = _validate_dag(doc)
        assert any("evidence" in e.lower() or "session_id" in e.lower() for e in errors)

    # @trace FR-CLI-415
    @patch("thegent.cli.commands.impl._validate_agent", return_value=None)
    def test_done_with_evidence_passes(self, mock_agent) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "done",
                    "evidence": "sess-1",
                }
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status", "evidence"],
        )
        errors = _validate_dag(doc)
        evidence_errors = [e for e in errors if "evidence" in e.lower()]
        assert len(evidence_errors) == 0


# ---------------------------------------------------------------------------
# _get_ready_task_ids with cancelled/skipped deps (lines 677-694)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetReadyTaskIds:
    # @trace FR-CLI-416
    def test_pending_with_satisfied_deps(self) -> None:
        tasks = [
            {"id": "T1", "status": "done", "depends_on": "-"},
            {"id": "T2", "status": "pending", "depends_on": "T1"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert "T2" in ready

    # @trace FR-CLI-417
    def test_pending_with_unsatisfied_deps(self) -> None:
        tasks = [
            {"id": "T1", "status": "running", "depends_on": "-"},
            {"id": "T2", "status": "pending", "depends_on": "T1"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert "T2" not in ready

    # @trace FR-CLI-418
    def test_cancelled_dep_satisfies(self) -> None:
        tasks = [
            {"id": "T1", "status": "cancelled", "depends_on": "-"},
            {"id": "T2", "status": "pending", "depends_on": "T1"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert "T2" in ready

    # @trace FR-CLI-419
    def test_skipped_dep_satisfies(self) -> None:
        tasks = [
            {"id": "T1", "status": "skipped", "depends_on": "-"},
            {"id": "T2", "status": "pending", "depends_on": "T1"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert "T2" in ready

    # @trace FR-CLI-420
    def test_no_deps_is_ready(self) -> None:
        tasks = [
            {"id": "T1", "status": "pending", "depends_on": ""},
        ]
        ready = _get_ready_task_ids(tasks)
        assert "T1" in ready

    # @trace FR-CLI-421
    def test_non_pending_not_included(self) -> None:
        tasks = [
            {"id": "T1", "status": "done", "depends_on": ""},
            {"id": "T2", "status": "running", "depends_on": ""},
        ]
        ready = _get_ready_task_ids(tasks)
        assert ready == []


# ---------------------------------------------------------------------------
# _check_dag_cycles (lines 498-536)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCheckDagCycles:
    # @trace FR-CLI-422
    def test_no_cycle(self) -> None:
        tasks = [
            {"id": "A", "depends_on": "-"},
            {"id": "B", "depends_on": "A"},
            {"id": "C", "depends_on": "B"},
        ]
        errors = _check_dag_cycles(tasks)
        assert not any("cycle" in e.lower() for e in errors)

    # @trace FR-CLI-423
    def test_simple_cycle_detected(self) -> None:
        tasks = [
            {"id": "A", "depends_on": "B"},
            {"id": "B", "depends_on": "A"},
        ]
        errors = _check_dag_cycles(tasks)
        assert any("cycle" in e.lower() for e in errors)

    # @trace FR-CLI-424
    def test_unknown_dep_reported(self) -> None:
        tasks = [
            {"id": "A", "depends_on": "MISSING"},
        ]
        errors = _check_dag_cycles(tasks)
        assert any("unknown" in e.lower() for e in errors)

    # @trace FR-CLI-425
    def test_self_cycle_detected(self) -> None:
        tasks = [
            {"id": "A", "depends_on": "A"},
        ]
        errors = _check_dag_cycles(tasks)
        assert any("cycle" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# _atomic_write with backup (lines 456-466)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAtomicWrite:
    # @trace FR-CLI-426
    def test_write_creates_file(self, tmp_path) -> None:
        target = tmp_path / "output.md"
        _atomic_write(target, "content here")
        assert target.read_text() == "content here"

    # @trace FR-CLI-427
    def test_write_with_backup(self, tmp_path) -> None:
        target = tmp_path / "output.md"
        target.write_text("original content")
        _atomic_write(target, "new content", backup=True)
        assert target.read_text() == "new content"
        backup = target.with_suffix(".md.bak")
        assert backup.exists()
        assert backup.read_text() == "original content"

    # @trace FR-CLI-428
    def test_write_without_backup_no_bak_file(self, tmp_path) -> None:
        target = tmp_path / "output.md"
        target.write_text("original")
        _atomic_write(target, "updated", backup=False)
        assert target.read_text() == "updated"
        assert not target.with_suffix(".md.bak").exists()


# ---------------------------------------------------------------------------
# _ensure_dag_file (lines 581-591)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEnsureDagFile:
    # @trace FR-CLI-429
    def test_existing_file_parsed(self, tmp_path) -> None:
        dag = tmp_path / "dag.md"
        dag.write_text("## Tasks\n\n| ID | Status |\n|---|---|\n| T1 | pending |\n")
        doc = _ensure_dag_file(dag)
        assert len(doc.tasks) == 1

    # @trace FR-CLI-430
    def test_missing_file_creates_empty_doc(self, tmp_path) -> None:
        dag = tmp_path / "nonexistent.md"
        doc = _ensure_dag_file(dag)
        assert doc.tasks == []
        assert doc.frontmatter["version"] == "1"
        assert "id" in doc.table_headers


# ---------------------------------------------------------------------------
# _serialize_dag round-trip (lines 444-453)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSerializeDag:
    # @trace FR-CLI-431
    def test_round_trip_preserves_tasks(self, tmp_path) -> None:
        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "do stuff",
                    "depends_on": "-",
                    "status": "pending",
                },
            ],
            before_table="## Tasks\n",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        md = _serialize_dag(doc)
        dag_path = tmp_path / "out.md"
        dag_path.write_text(md)
        doc2 = _parse_dag_full(dag_path)
        assert len(doc2.tasks) == 1
        assert doc2.tasks[0]["id"] == "T1"


# ---------------------------------------------------------------------------
# _escape_cell (line 439-441)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEscapeCell:
    # @trace FR-CLI-432
    def test_pipe_escaped(self) -> None:
        assert _escape_cell("a|b") == "a\\|b"

    # @trace FR-CLI-433
    def test_newline_replaced_with_space(self) -> None:
        assert _escape_cell("line1\nline2") == "line1 line2"


# ---------------------------------------------------------------------------
# _validate_task_id (lines 478-484)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateTaskId:
    # @trace FR-CLI-434
    def test_valid_id(self) -> None:
        assert _validate_task_id("T1") is None
        assert _validate_task_id("task-01_v2") is None

    # @trace FR-CLI-435
    def test_empty_id(self) -> None:
        assert _validate_task_id("") is not None
        assert _validate_task_id("   ") is not None

    # @trace FR-CLI-436
    def test_invalid_id_chars(self) -> None:
        result = _validate_task_id("@bad!")
        assert result is not None
        assert "Invalid" in result


# ---------------------------------------------------------------------------
# _parse_depends_on (lines 670-674)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestParseDependsOn:
    # @trace FR-CLI-437
    def test_dash_returns_empty(self) -> None:
        assert _parse_depends_on("-") == []
        assert _parse_depends_on("\u2014") == []

    # @trace FR-CLI-438
    def test_csv_parsed(self) -> None:
        assert _parse_depends_on("T1, T2, T3") == ["T1", "T2", "T3"]

    # @trace FR-CLI-439
    def test_empty_returns_empty(self) -> None:
        assert _parse_depends_on("") == []
        assert _parse_depends_on(None) == []


# ---------------------------------------------------------------------------
# get_server_meta_impl (lines 1113-1129)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetServerMetaImpl:
    # @trace FR-CLI-440
    def test_returns_expected_keys(self) -> None:
        meta = get_server_meta_impl()
        assert meta["server"] == "thegent"
        assert "tools" in meta["capabilities"]
        assert "health_payload_schema_version" in meta
        assert "observe_summary_payload_schema_version" in meta
        assert "operations" in meta
        assert "orchestration_modes" in meta
        assert "contract_schema_version" in meta


# ---------------------------------------------------------------------------
# get_data_protection_status_impl (lines 1753-1774)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGetDataProtectionStatusImpl:
    # @trace FR-CLI-441
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_returns_status_dict(self, mock_settings_cls, tmp_path) -> None:
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        os.chmod(session_dir, 0o700)
        settings = MagicMock()
        settings.session_dir = session_dir
        settings.retention_days_sessions = 30
        settings.retention_days_registry = 90
        settings.retention_days_health = 365
        mock_settings_cls.return_value = settings

        from thegent.cli.commands.impl import get_data_protection_status_impl

        result = get_data_protection_status_impl()
        assert result["session_dir_exists"] is True
        assert result["permissions_restricted"] is True
        assert result["masking_enabled"] is True

    # @trace FR-CLI-442
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_nonexistent_dir_reports_no_restriction(self, mock_settings_cls, tmp_path) -> None:
        session_dir = tmp_path / "nonexistent"
        settings = MagicMock()
        settings.session_dir = session_dir
        settings.retention_days_sessions = 30
        settings.retention_days_registry = 90
        settings.retention_days_health = 365
        mock_settings_cls.return_value = settings

        from thegent.cli.commands.impl import get_data_protection_status_impl

        result = get_data_protection_status_impl()
        assert result["session_dir_exists"] is False
        assert result["permissions_restricted"] is False


# ---------------------------------------------------------------------------
# _health_snapshot_log_path (lines 1175-1182)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthSnapshotLogPath:
    # @trace FR-CLI-443
    def test_env_override(self, tmp_path) -> None:
        custom_path = tmp_path / "custom" / "snaps.jsonl"
        with patch.dict(os.environ, {"THGENT_HEALTH_SNAPSHOT_PATH": str(custom_path)}):
            from thegent.cli.commands.impl import _health_snapshot_log_path

            result = _health_snapshot_log_path()
        assert result == custom_path
        assert custom_path.parent.exists()

    # @trace FR-CLI-444
    def test_default_path(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("THGENT_HEALTH_SNAPSHOT_PATH", None)
            from thegent.cli.commands.impl import _health_snapshot_log_path

            result = _health_snapshot_log_path()
        assert str(result).endswith("health-snapshots.jsonl")
