from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from thegent.config import ThegentSettings
from thegent.planning.work_stream import WorkStreamManager


def _write_coordination_files(base: Path) -> None:
    docs_ref = base / "docs" / "reference"
    docs_plans = base / "docs" / "plans"
    docs_ref.mkdir(parents=True, exist_ok=True)
    docs_plans.mkdir(parents=True, exist_ok=True)

    (docs_ref / "WORK_STREAM.md").write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title |",
                "|----|-------|",
                "| wp-1 | Test item |",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| *(none)*",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (docs_ref / "WBS_AGENT_PROGRESS.md").write_text(
        "\n".join(
            [
                "# Agent Progress",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| *(none)*",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed | Notes |",
                "|----|-------|-----------|-------|",
                "| *(append when done)*",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (docs_plans / "02-UNIFIED-WBS.md").write_text(
        "\n".join(
            [
                "| WP ID | Description | Status | Owner |",
                "|-------|-------------|--------|-------|",
                "| wp-1 | Test item | NOT DONE | team |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_claim_fails_if_any_coordination_write_fails(tmp_path: Path, monkeypatch) -> None:
    _write_coordination_files(tmp_path)
    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)

    from thegent.utils import helpers

    def _fake_safe_write(
        path: str | Path, content: str, expected_version: str | None = None, encoding: str = "utf-8"
    ) -> bool:
        return Path(path).name != "WORK_STREAM.md"

    monkeypatch.setattr(helpers, "safe_write_file", _fake_safe_write)

    result = manager.claim("wp-1", "agent-1")
    work_stream_action = next(a for a in result["actions"] if a["file"] == "WORK_STREAM.md")

    assert work_stream_action["success"] is False
    assert result["success"] is False


def test_complete_fails_when_remove_step_write_fails(tmp_path: Path, monkeypatch) -> None:
    _write_coordination_files(tmp_path)
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title |",
                "|----|-------|",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| wp-1 | agent-1 | 2026-01-01T00:00:00Z |",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)

    from thegent.utils import helpers

    calls = {"work_stream": 0}

    def _fake_safe_write(
        path: str | Path, content: str, expected_version: str | None = None, encoding: str = "utf-8"
    ) -> bool:
        if Path(path).name == "WORK_STREAM.md":
            calls["work_stream"] += 1
            return calls["work_stream"] != 1
        return True

    monkeypatch.setattr(helpers, "safe_write_file", _fake_safe_write)

    result = manager.complete("wp-1", "agent-1")
    work_stream_action = next(a for a in result["actions"] if a["file"] == "WORK_STREAM.md")

    assert calls["work_stream"] >= 2
    assert work_stream_action["success"] is False
    assert result["success"] is False


# ---------------------------------------------------------------------------
# OCC concurrent-claim tests (the key regression tests)
# ---------------------------------------------------------------------------


def test_sequential_duplicate_claim_rejected(tmp_path: Path) -> None:
    """Second sequential claim for the same item must fail with success=False.

    Regression test: previously both claims returned success=True because
    any() was used instead of all() and _update_section did not detect the
    duplicate item already present in the CLAIMED section.

    # @trace TGNT-OCC-1
    """
    _write_coordination_files(tmp_path)
    settings = ThegentSettings()

    manager_a = WorkStreamManager(settings, base_dir=tmp_path)
    result_a = manager_a.claim("wp-1", "agent-a")
    assert result_a["success"] is True, "First claim must succeed"

    manager_b = WorkStreamManager(settings, base_dir=tmp_path)
    result_b = manager_b.claim("wp-1", "agent-b")
    assert result_b["success"] is False, "Second claim for same item must fail (OCC duplicate check)"

    # Verify the item appears exactly once in CLAIMED section.
    content = (tmp_path / "docs" / "reference" / "WORK_STREAM.md").read_text(encoding="utf-8")
    in_claimed = False
    claim_count = 0
    for line in content.splitlines():
        if "## CLAIMED" in line:
            in_claimed = True
        elif line.startswith("##"):
            in_claimed = False
        elif in_claimed and "| wp-1 |" in line:
            claim_count += 1
    assert claim_count == 1, f"Expected exactly 1 CLAIMED entry for wp-1, got {claim_count}"


def test_concurrent_duplicate_claim_only_one_succeeds(tmp_path: Path) -> None:
    """When two agents claim the same item concurrently, exactly one must succeed.

    The winning agent's write is accepted; the losing agent must receive
    success=False either via OCC hash mismatch (file changed) or via the
    duplicate-item guard in _update_section.

    # @trace TGNT-OCC-2
    """
    _write_coordination_files(tmp_path)
    settings = ThegentSettings()
    results: list[tuple[str, dict]] = []
    lock = threading.Lock()

    def do_claim(agent_id: str) -> None:
        manager = WorkStreamManager(settings, base_dir=tmp_path)
        result = manager.claim("wp-1", agent_id)
        with lock:
            results.append((agent_id, result))

    t1 = threading.Thread(target=do_claim, args=("agent-t1",))
    t2 = threading.Thread(target=do_claim, args=("agent-t2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [agent for agent, r in results if r["success"]]
    assert len(successes) == 1, (
        f"Exactly one concurrent claim must succeed; got {len(successes)} successes: {successes}"
    )

    # Verify the item appears exactly once in CLAIMED section.
    content = (tmp_path / "docs" / "reference" / "WORK_STREAM.md").read_text(encoding="utf-8")
    in_claimed = False
    claim_count = 0
    for line in content.splitlines():
        if "## CLAIMED" in line:
            in_claimed = True
        elif line.startswith("##"):
            in_claimed = False
        elif in_claimed and "| wp-1 |" in line:
            claim_count += 1
    assert claim_count == 1, f"Expected exactly 1 CLAIMED entry for wp-1, got {claim_count}"


def test_claim_success_uses_all_not_any(tmp_path: Path, monkeypatch) -> None:
    """Claim must report success=False if ANY file write fails (all() semantics).

    Regression test: previously any() was used so a claim that succeeded on
    WBS_AGENT_PROGRESS.md but failed on WORK_STREAM.md would still report
    success=True.

    # @trace TGNT-OCC-3
    """
    _write_coordination_files(tmp_path)
    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)

    from thegent.utils import helpers

    # Allow WBS_AGENT_PROGRESS.md write but reject WORK_STREAM.md write.
    def _fake_safe_write(
        path: str | Path,
        content: str,
        expected_version: str | None = None,
        encoding: str = "utf-8",
    ) -> bool:
        return Path(path).name != "WORK_STREAM.md"

    monkeypatch.setattr(helpers, "safe_write_file", _fake_safe_write)

    result = manager.claim("wp-1", "agent-x")

    # Even though WBS_AGENT_PROGRESS.md write succeeds, the overall claim
    # must fail because WORK_STREAM.md write failed.
    assert result["success"] is False, "claim() must return success=False when any file write fails (all() semantics)"


def test_occ_hash_consistency_read_text_vs_read_bytes(tmp_path: Path) -> None:
    file_path = tmp_path / "occ.txt"
    file_path.write_bytes(b"line-1\r\nline-2\r\n")

    bytes_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    text_hash = hashlib.sha256(file_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()

    assert bytes_hash != text_hash


def test_claim_blocks_when_dependencies_unmet(tmp_path: Path) -> None:
    _write_coordination_files(tmp_path)
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title | Depends |",
                "|----|-------|---------|",
                "| wp-1 | Prereq | - |",
                "| wp-2 | Blocked item | wp-1 |",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| *(none)*",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
                "| *(none)*",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)
    result = manager.claim("wp-2", "agent-1")

    assert result["success"] is False
    assert result["dependency_blocked"] is True
    assert result["blocked_by"] == ["wp-1"]
    assert result["actions"] == []


def test_claim_allows_when_dependency_is_completed(tmp_path: Path) -> None:
    _write_coordination_files(tmp_path)
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title | Depends |",
                "|----|-------|---------|",
                "| wp-1 | Prereq | - |",
                "| wp-2 | Ready item | wp-1 |",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| *(none)*",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
                "| wp-1 | agent-0 | 2026-01-02T00:00:00Z |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)
    result = manager.claim("wp-2", "agent-1")

    assert result["success"] is True
    assert "dependency_blocked" not in result


def test_verify_work_stream_invariants_detects_claimed_completed_overlap(tmp_path: Path) -> None:
    _write_coordination_files(tmp_path)
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title |",
                "|----|-------|",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| wp-1 | agent-1 | 2026-01-01T00:00:00Z |",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
                "| wp-1 | agent-1 | 2026-01-02T00:00:00Z |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)
    result = manager.verify_work_stream_invariants()

    assert result["ok"] is False
    assert result["counts"]["claimed"] == 1
    assert result["counts"]["completed"] == 1
    assert result["counts"]["overlap"] == 1
    assert any("wp-1" in error for error in result["errors"])


def test_verify_work_stream_invariants_uses_exact_id_cell_match(tmp_path: Path) -> None:
    _write_coordination_files(tmp_path)
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## BACKLOG",
                "| ID | Title |",
                "|----|-------|",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| wp-10 | agent-1 | 2026-01-01T00:00:00Z |",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
                "| wp-1 | agent-1 | 2026-01-02T00:00:00Z |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager = WorkStreamManager(ThegentSettings(), base_dir=tmp_path)
    result = manager.verify_work_stream_invariants()

    assert result["ok"] is True
    assert result["counts"]["claimed"] == 1
    assert result["counts"]["completed"] == 1
    assert result["counts"]["overlap"] == 0
    assert result["errors"] == []
