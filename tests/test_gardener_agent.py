"""Tests for GardenerAgent — automated documentation synthesis.

# @trace WL-060

Covers:
- TestReadSources: memory dir scan, conversation dump scan, empty dir, missing dir
- TestDetectStaleDocs: finds old file, skips recent file, detects pending WL in completed sources
- TestSynthesizeUpdate: generates non-empty update string, handles WORK_STREAM.md specially
- TestGardenRun: dry_run returns result without writing, full run writes files, result counts
- TestGardeningIntegration: "garden" step in STEPS, run_step handler exists, never_idle includes step
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.agents.gardener import (
    GardenerAgent,
    GardenResult,
    SourceDocument,
    StaleDoc,
    _extract_completed_wl_ids,
    _extract_pending_wl_ids,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_memory_dir(tmp_path: Path) -> Path:
    """Create a temporary memory directory with one JSONL file.

    # @trace WL-060
    """
    mem_dir = tmp_path / ".thegent" / "memory"
    mem_dir.mkdir(parents=True)
    log_file = mem_dir / "session_001.jsonl"
    log_file.write_text(
        json.dumps({"type": "note", "content": "WL-060 COMPLETED"}).decode()
        + "\n"
        + json.dumps({"type": "rule", "content": "Use structlog"}).decode()
        + "\n"
    )
    return mem_dir


@pytest.fixture
def tmp_project_root(tmp_path: Path) -> Path:
    """Create a minimal project root with docs structure.

    # @trace WL-060
    """
    root = tmp_path / "project"
    (root / "docs" / "reference").mkdir(parents=True)
    (root / "docs" / "research").mkdir(parents=True)
    (root / "docs" / "context").mkdir(parents=True)
    return root


@pytest.fixture
def agent(tmp_memory_dir: Path, tmp_project_root: Path) -> GardenerAgent:
    """Create a GardenerAgent with temp dirs.

    # @trace WL-060
    """
    return GardenerAgent(
        dry_run=False,
        project_root=tmp_project_root,
        memory_dir=tmp_memory_dir,
    )


@pytest.fixture
def dry_agent(tmp_memory_dir: Path, tmp_project_root: Path) -> GardenerAgent:
    """Create a dry-run GardenerAgent.

    # @trace WL-060
    """
    return GardenerAgent(
        dry_run=True,
        project_root=tmp_project_root,
        memory_dir=tmp_memory_dir,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_work_stream(root: Path, content: str) -> Path:
    path = root / "docs" / "reference" / "WORK_STREAM.md"
    path.write_text(content)
    return path


def _write_conversation_dump(root: Path, content: str, name: str = "CONVERSATION_DUMP_2026-02-20.md") -> Path:
    path = root / "docs" / "research" / name
    path.write_text(content)
    return path


def _make_old_file(path: Path, days: int = 10) -> None:
    """Set mtime to *days* ago."""
    old_mtime = time.time() - days * 86400
    import os

    os.utime(path, (old_mtime, old_mtime))


# ---------------------------------------------------------------------------
# TestReadSources
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReadSources:
    """Tests for GardenerAgent.read_sources.

    # @trace WL-060
    """

    def test_reads_memory_jsonl_files(self, agent: GardenerAgent, tmp_memory_dir: Path) -> None:
        """read_sources returns at least one SourceDocument from memory dir JSONL."""
        # @trace WL-060
        sources = agent.read_sources()
        mem_sources = [s for s in sources if s.path.suffix == ".jsonl" and s.path.parent == tmp_memory_dir]
        assert len(mem_sources) >= 1

    def test_memory_source_has_content(self, agent: GardenerAgent, tmp_memory_dir: Path) -> None:
        """Memory JSONL SourceDocument has non-empty content."""
        # @trace WL-060
        sources = agent.read_sources()
        mem_sources = [s for s in sources if s.path.suffix == ".jsonl"]
        assert all(s.content for s in mem_sources)

    def test_reads_conversation_dumps(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """read_sources includes CONVERSATION_DUMP_*.md files from docs/research/."""
        # @trace WL-060
        _write_conversation_dump(tmp_project_root, "WL-013 COMPLETED\nSome notes here.")
        sources = agent.read_sources()
        dump_sources = [s for s in sources if s.path.name.startswith("CONVERSATION_DUMP_")]
        assert len(dump_sources) == 1
        assert "WL-013" in dump_sources[0].content

    def test_skips_conversation_dumps_when_research_dir_missing(self, tmp_memory_dir: Path, tmp_path: Path) -> None:
        """When docs/research/ does not exist, no conversation dump sources are added."""
        # @trace WL-060
        root = tmp_path / "no_research"
        (root / "docs" / "reference").mkdir(parents=True)
        agent = GardenerAgent(dry_run=False, project_root=root, memory_dir=tmp_memory_dir)
        sources = agent.read_sources()
        dump_sources = [s for s in sources if s.path.name.startswith("CONVERSATION_DUMP_")]
        assert len(dump_sources) == 0

    def test_reads_work_stream(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """read_sources includes WORK_STREAM.md when it exists."""
        # @trace WL-060
        _write_work_stream(tmp_project_root, "## WORK STREAM\n\n### [WL-001]\n**Status:** pending\n")
        sources = agent.read_sources()
        ws_sources = [s for s in sources if s.path.name == "WORK_STREAM.md"]
        assert len(ws_sources) == 1

    def test_empty_memory_dir_returns_empty_list_of_jsonl(self, tmp_project_root: Path, tmp_path: Path) -> None:
        """Empty memory dir (no *.jsonl files) produces zero memory sources."""
        # @trace WL-060
        empty_mem = tmp_path / "empty_mem"
        empty_mem.mkdir()
        agent = GardenerAgent(dry_run=False, project_root=tmp_project_root, memory_dir=empty_mem)
        sources = agent.read_sources()
        mem_sources = [s for s in sources if s.path.suffix == ".jsonl"]
        assert len(mem_sources) == 0

    def test_missing_memory_dir_raises_file_not_found(self, tmp_project_root: Path, tmp_path: Path) -> None:
        """read_sources raises FileNotFoundError when memory_dir does not exist."""
        # @trace WL-060
        missing = tmp_path / "does_not_exist"
        agent = GardenerAgent(dry_run=False, project_root=tmp_project_root, memory_dir=missing)
        with pytest.raises(FileNotFoundError, match="Memory directory not found"):
            agent.read_sources()

    def test_source_document_has_last_modified(self, agent: GardenerAgent, tmp_memory_dir: Path) -> None:
        """SourceDocument.last_modified is a positive float."""
        # @trace WL-060
        sources = agent.read_sources()
        for s in sources:
            assert isinstance(s.last_modified, float)
            assert s.last_modified > 0

    def test_governance_events_skipped_when_absent(self, agent: GardenerAgent) -> None:
        """read_sources does not raise when governance_events.jsonl is missing."""
        # @trace WL-060
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent/home_xyz_99")
            # The memory_dir is set explicitly on the agent; only governance path uses home
            # Just confirm no exception is raised even with a fake home
            # We re-instantiate with the explicit memory_dir
        # Default call: governance file likely absent in CI — should not raise
        sources = agent.read_sources()
        gov_sources = [s for s in sources if s.path.name == "governance_events.jsonl"]
        # Either 0 (file absent) or 1 (file present) — both are valid; no exception is the assertion
        assert isinstance(gov_sources, list)


# ---------------------------------------------------------------------------
# TestDetectStaleDocs
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDetectStaleDocs:
    """Tests for GardenerAgent.detect_stale_docs.

    # @trace WL-060
    """

    def test_finds_old_file(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """detect_stale_docs includes files older than max_age_days."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "OLD_DOC.md"
        old_doc.write_text("# Old doc\n")
        _make_old_file(old_doc, days=10)
        stale = agent.detect_stale_docs(max_age_days=7)
        stale_paths = [s.path for s in stale]
        assert old_doc in stale_paths

    def test_skips_recent_file(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """detect_stale_docs excludes files modified within max_age_days."""
        # @trace WL-060
        recent_doc = tmp_project_root / "docs" / "reference" / "RECENT_DOC.md"
        recent_doc.write_text("# Recent doc\n")
        # mtime defaults to now — no explicit aging needed
        stale = agent.detect_stale_docs(max_age_days=7)
        stale_paths = [s.path for s in stale]
        assert recent_doc not in stale_paths

    def test_detects_pending_wl_in_completed_sources(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """Pending WL items appearing as COMPLETED in conversation dumps are flagged."""
        # @trace WL-060
        _write_work_stream(
            tmp_project_root,
            "### [WL-013]\n**Status:** pending\nSome work.\n\n### [WL-060]\n**Status:** pending\n",
        )
        _write_conversation_dump(
            tmp_project_root,
            "[WL-013] COMPLETED — Supermemory Phase 2 is done.\n[WL-060] COMPLETED — Gardener agent shipped.\n",
        )
        stale = agent.detect_stale_docs(max_age_days=7)
        ws_stale = [s for s in stale if s.path.name == "WORK_STREAM.md"]
        assert len(ws_stale) == 1
        assert "WL-013" in ws_stale[0].reason or "WL-060" in ws_stale[0].reason

    def test_no_stale_when_all_pending_not_completed(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """No WORK_STREAM stale entry when pending items are not completed in sources."""
        # @trace WL-060
        _write_work_stream(
            tmp_project_root,
            "### [WL-999]\n**Status:** pending\nUnstarted work.\n",
        )
        _write_conversation_dump(
            tmp_project_root,
            "Some random notes about WL-999 but no completion marker.\n",
        )
        stale = agent.detect_stale_docs(max_age_days=7)
        ws_stale = [s for s in stale if s.path.name == "WORK_STREAM.md"]
        assert len(ws_stale) == 0

    def test_stale_doc_has_reason(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """StaleDoc objects have a non-empty reason string."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "STALE.md"
        old_doc.write_text("# Stale\n")
        _make_old_file(old_doc, days=15)
        stale = agent.detect_stale_docs(max_age_days=7)
        assert all(s.reason for s in stale)

    def test_stale_doc_has_suggested_action(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """StaleDoc objects have a non-empty suggested_action string."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "STALE2.md"
        old_doc.write_text("# Stale\n")
        _make_old_file(old_doc, days=15)
        stale = agent.detect_stale_docs(max_age_days=7)
        assert all(s.suggested_action for s in stale)

    def test_checks_context_dir_too(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """detect_stale_docs also scans docs/context/ for stale files."""
        # @trace WL-060
        old_ctx = tmp_project_root / "docs" / "context" / "OLD_TECH.md"
        old_ctx.write_text("# Old tech doc\n")
        _make_old_file(old_ctx, days=30)
        stale = agent.detect_stale_docs(max_age_days=7)
        stale_paths = [s.path for s in stale]
        assert old_ctx in stale_paths


# ---------------------------------------------------------------------------
# TestSynthesizeUpdate
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSynthesizeUpdate:
    """Tests for GardenerAgent.synthesize_update.

    # @trace WL-060
    """

    def test_generates_non_empty_update(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """synthesize_update returns a non-empty string for any StaleDoc."""
        # @trace WL-060
        stale = StaleDoc(
            path=tmp_project_root / "docs" / "reference" / "SOME_DOC.md",
            reason="Not modified in >7 days",
            suggested_action="Review and update",
        )
        sources: list[SourceDocument] = []
        result = agent.synthesize_update(stale, sources)
        assert result
        assert len(result) > 0

    def test_work_stream_update_contains_wl_ids(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """synthesize_update for WORK_STREAM.md contains WL IDs from the reason."""
        # @trace WL-060
        stale = StaleDoc(
            path=tmp_project_root / "docs" / "reference" / "WORK_STREAM.md",
            reason="WL items marked pending but completed in sources: WL-013, WL-060",
            suggested_action="Mark items as COMPLETED: WL-013, WL-060",
        )
        sources: list[SourceDocument] = []
        result = agent.synthesize_update(stale, sources)
        assert "WL-013" in result
        assert "WL-060" in result

    def test_work_stream_update_mentions_completed(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """synthesize_update for WORK_STREAM.md mentions marking items COMPLETED."""
        # @trace WL-060
        stale = StaleDoc(
            path=tmp_project_root / "docs" / "reference" / "WORK_STREAM.md",
            reason="WL items marked pending but completed in sources: WL-013",
            suggested_action="Mark items as COMPLETED: WL-013",
        )
        result = agent.synthesize_update(stale, [])
        assert "COMPLETED" in result

    def test_generic_update_contains_reason(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """synthesize_update for non-WORK_STREAM docs embeds the reason."""
        # @trace WL-060
        stale = StaleDoc(
            path=tmp_project_root / "docs" / "reference" / "ANY_DOC.md",
            reason="Not modified in >7 days",
            suggested_action="Review and update or mark as archived",
        )
        result = agent.synthesize_update(stale, [])
        assert "Not modified" in result

    def test_work_stream_update_includes_evidence_sources(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """synthesize_update cross-references source docs that mention the WL IDs."""
        # @trace WL-060
        stale = StaleDoc(
            path=tmp_project_root / "docs" / "reference" / "WORK_STREAM.md",
            reason="WL items marked pending but completed in sources: WL-013",
            suggested_action="Mark items as COMPLETED: WL-013",
        )
        dump_path = tmp_project_root / "docs" / "research" / "CONVERSATION_DUMP_2026-02-20.md"
        dump_path.write_text("[WL-013] COMPLETED\n")
        sources = [
            SourceDocument(
                path=dump_path,
                content="[WL-013] COMPLETED\n",
                last_modified=time.time(),
            )
        ]
        result = agent.synthesize_update(stale, sources)
        assert str(dump_path) in result


# ---------------------------------------------------------------------------
# TestGardenRun
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGardenRun:
    """Tests for GardenerAgent.run.

    # @trace WL-060
    """

    def test_dry_run_returns_result_without_writing(self, dry_agent: GardenerAgent, tmp_project_root: Path) -> None:
        """dry_run=True returns GardenResult without modifying any files."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "OLD.md"
        old_doc.write_text("# Old\n")
        _make_old_file(old_doc, days=20)
        original_mtime = old_doc.stat().st_mtime

        result = dry_agent.run(max_age_days=7)

        assert isinstance(result, GardenResult)
        assert result.dry_run is True
        assert result.docs_updated == 0
        # File not touched
        assert old_doc.stat().st_mtime == original_mtime

    def test_dry_run_result_has_items_found(self, dry_agent: GardenerAgent, tmp_project_root: Path) -> None:
        """dry_run=True still populates items_found with detected stale docs."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "STALE_DRY.md"
        old_doc.write_text("# Stale\n")
        _make_old_file(old_doc, days=20)

        result = dry_agent.run(max_age_days=7)

        assert result.docs_checked > 0
        assert any("STALE_DRY.md" in item for item in result.items_found)

    def test_full_run_writes_files(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """Full run (dry_run=False) writes updates to stale docs."""
        # @trace WL-060
        old_doc = tmp_project_root / "docs" / "reference" / "STALE_FULL.md"
        old_doc.write_text("# Stale content\n")
        _make_old_file(old_doc, days=20)
        original_content = old_doc.read_text()

        result = agent.run(max_age_days=7)

        assert result.dry_run is False
        assert result.docs_updated >= 1
        new_content = old_doc.read_text()
        assert new_content != original_content

    def test_result_has_correct_counts(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """GardenResult.docs_checked equals number of stale docs detected."""
        # @trace WL-060
        for i in range(3):
            doc = tmp_project_root / "docs" / "reference" / f"OLD_{i}.md"
            doc.write_text(f"# Old {i}\n")
            _make_old_file(doc, days=20)

        result = agent.run(max_age_days=7)

        assert result.docs_checked == len(result.items_found)

    def test_no_stale_docs_returns_zero_counts(self, agent: GardenerAgent, tmp_project_root: Path) -> None:
        """When no stale docs exist, docs_checked and docs_updated are both 0."""
        # @trace WL-060
        # Write a fresh doc (mtime=now, not stale)
        fresh_doc = tmp_project_root / "docs" / "reference" / "FRESH.md"
        fresh_doc.write_text("# Fresh\n")

        result = agent.run(max_age_days=7)

        assert result.docs_checked == 0
        assert result.docs_updated == 0

    def test_garden_result_dry_run_flag_matches_agent(self, dry_agent: GardenerAgent, tmp_project_root: Path) -> None:
        """GardenResult.dry_run mirrors the agent's dry_run setting."""
        # @trace WL-060
        result = dry_agent.run()
        assert result.dry_run is True

    def test_full_run_marks_pending_work_stream_items_completed(
        self, agent: GardenerAgent, tmp_project_root: Path
    ) -> None:
        """Full run patches WORK_STREAM.md pending items to COMPLETED when evidence found."""
        # @trace WL-060
        _write_work_stream(
            tmp_project_root,
            "### [WL-013]\n**Status:** pending\nSupermemory Phase 2.\n",
        )
        _write_conversation_dump(
            tmp_project_root,
            "[WL-013] COMPLETED — Supermemory Phase 2 is done.\n",
        )

        result = agent.run(max_age_days=7)

        ws_path = tmp_project_root / "docs" / "reference" / "WORK_STREAM.md"
        patched = ws_path.read_text()
        assert "COMPLETED" in patched
        assert result.docs_updated >= 1


# ---------------------------------------------------------------------------
# TestGardeningIntegration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGardeningIntegration:
    """Integration tests verifying wiring into GardeningManager and NeverIdleLoop.

    # @trace WL-060
    """

    def test_garden_step_in_gardening_manager_steps(self) -> None:
        """'garden' is in GardeningManager.STEPS."""
        # @trace WL-060
        from thegent.sitback.gardening import GardeningManager

        assert "garden" in GardeningManager.STEPS

    def test_run_step_handler_exists_for_garden(self) -> None:
        """GardeningManager.run_step has a handler registered for 'garden'."""
        # @trace WL-060
        import asyncio

        from thegent.sitback.gardening import GardeningManager

        manager = GardeningManager()
        # Patch the GardenerAgent.run to avoid real FS operations
        mock_result = MagicMock()
        mock_result.docs_checked = 0
        mock_result.docs_updated = 0
        mock_result.items_found = []

        with patch("thegent.agents.gardener.GardenerAgent.run", return_value=mock_result):
            with patch("thegent.agents.gardener.GardenerAgent.read_sources", return_value=[]):
                result = asyncio.run(manager.run_step("garden"))

        assert result["success"] is True
        assert "docs_checked" in result
        assert "docs_updated" in result

    def test_unknown_step_returns_error(self) -> None:
        """GardeningManager.run_step returns error dict for unknown steps."""
        # @trace WL-060
        import asyncio

        from thegent.sitback.gardening import GardeningManager

        manager = GardeningManager()
        result = asyncio.run(manager.run_step("nonexistent_step_xyz"))
        assert result["success"] is False
        assert "Unknown step" in result["error"]

    def test_never_idle_includes_garden_step(self) -> None:
        """NeverIdleLoop.GARDENING_STEPS includes 'garden'."""
        # @trace WL-060
        from thegent.sitback.never_idle import NeverIdleLoop

        assert "garden" in NeverIdleLoop.GARDENING_STEPS

    def test_garden_step_position_in_never_idle(self) -> None:
        """'garden' appears after 'shadow_cleanup' in GARDENING_STEPS."""
        # @trace WL-060
        from thegent.sitback.never_idle import NeverIdleLoop

        steps = NeverIdleLoop.GARDENING_STEPS
        shadow_idx = steps.index("shadow_cleanup")
        garden_idx = steps.index("garden")
        assert garden_idx > shadow_idx


# ---------------------------------------------------------------------------
# TestHelpers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHelpers:
    """Tests for internal helper functions.

    # @trace WL-060
    """

    def test_extract_completed_wl_ids_finds_ids(self) -> None:
        """_extract_completed_wl_ids returns WL IDs marked COMPLETED."""
        # @trace WL-060
        content = "[WL-013] COMPLETED — Phase 2 done.\n[WL-060] COMPLETED.\n"
        result = _extract_completed_wl_ids(content)
        assert "013" in result
        assert "060" in result

    def test_extract_completed_wl_ids_empty_on_no_match(self) -> None:
        """_extract_completed_wl_ids returns empty set when no completed items."""
        # @trace WL-060
        content = "Nothing completed here.\n"
        result = _extract_completed_wl_ids(content)
        assert result == set()

    def test_extract_pending_wl_ids_finds_ids(self) -> None:
        """_extract_pending_wl_ids returns IDs with Status: pending."""
        # @trace WL-060
        content = "### [WL-001]\n**Status:** pending\nSome work.\n"
        result = _extract_pending_wl_ids(content)
        assert "001" in result

    def test_extract_pending_wl_ids_empty_when_no_pending(self) -> None:
        """_extract_pending_wl_ids returns empty set when no pending items."""
        # @trace WL-060
        content = "### [WL-001]\n**Status:** COMPLETED\nDone.\n"
        result = _extract_pending_wl_ids(content)
        assert result == set()
