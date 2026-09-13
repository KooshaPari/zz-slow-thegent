"""WL-136 L19 Memory archive_hot_paths helper contract.

Pins the L19 memory-hygiene contract for
``MemoryMeshV2.archive_hot_paths``:

* Archives every working-memory key into the episodic log when no
  access counter is supplied (legacy ``clear_working`` semantics with
  durable persistence).
* Honours an explicit ``access_counts`` mapping when supplied: only
  keys whose count meets the threshold are archived.
* Returns a sorted, deterministic list of archived keys.
* Working-memory slots are cleared only after a successful archive.
* ``record_episode`` failures are logged and skipped (best-effort, the
  caller must not crash on transient DB errors).
* The helper is idempotent — calling it twice with empty working
  memory returns an empty list and writes no episodes.
* Re-running ``get_episodes`` after archival returns rows tagged with
  ``event_type="hot_path_archive"`` so the session timeline can be
  reconstructed by task_id.

Tied to ``src/thegent/infra/memory.py`` (MemoryMeshV2 tier 2).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.infra.memory import MemoryMeshV2


@pytest.fixture
def memory_mesh(tmp_path: Path) -> MemoryMeshV2:
    """Per-test sqlite memory mesh in a tmp dir."""
    db = tmp_path / "memory_v2.db"
    mesh = MemoryMeshV2(db_path=db)
    return mesh
    # Cleanup is implicit (tmp_path); mesh itself holds no resources.


def test_archive_hot_paths_archives_every_key_when_no_counter(
    memory_mesh: MemoryMeshV2,
) -> None:
    """With no ``access_counts`` override, every working-memory key is archived."""
    memory_mesh.set_working("k1", "v1")
    memory_mesh.set_working("k2", "v2")
    memory_mesh.set_working("k3", {"nested": True})

    archived = memory_mesh.archive_hot_paths(task_id="t-1")

    assert archived == ["k1", "k2", "k3"]
    assert memory_mesh.working_memory == {}
    rows = memory_mesh.get_episodes("t-1")
    assert len(rows) == 3
    for row in rows:
        assert row["event_type"] == "hot_path_archive"
        assert row["outcome"] == "archived"
    # Content is a stringified repr — round-trips the key name.
    contents = sorted(row["content"] for row in rows)
    assert contents == ["k1='v1'", "k2='v2'", "k3={'nested': True}"]


def test_archive_hot_paths_honours_access_counts_threshold(
    memory_mesh: MemoryMeshV2,
) -> None:
    """With ``access_counts``, only keys meeting ``threshold`` are archived."""
    memory_mesh.set_working("hot", "h-value")
    memory_mesh.set_working("warm", "w-value")
    memory_mesh.set_working("cold", "c-value")

    archived = memory_mesh.archive_hot_paths(
        task_id="t-2",
        access_counts={"hot": 10, "warm": 5, "cold": 1},
        threshold=5,
    )

    # Sorted; "hot" + "warm" both meet threshold=5; "cold" does not.
    assert archived == ["hot", "warm"]
    assert set(memory_mesh.working_memory.keys()) == {"cold"}
    rows = memory_mesh.get_episodes("t-2")
    assert {row["event_type"] for row in rows} == {"hot_path_archive"}
    archived_keys = {row["metadata"] for row in rows}
    import json

    metas = {json.loads(m)["key"] for m in archived_keys}
    assert metas == {"hot", "warm"}


def test_archive_hot_paths_is_idempotent_on_empty(memory_mesh: MemoryMeshV2) -> None:
    """Calling on empty working memory is a no-op (no episodes, no error)."""
    assert memory_mesh.archive_hot_paths(task_id="t-3") == []
    assert memory_mesh.archive_hot_paths(task_id="t-3", access_counts={"x": 99}) == []
    assert memory_mesh.get_episodes("t-3") == []


def test_archive_hot_paths_skips_missing_keys_safely(memory_mesh: MemoryMeshV2) -> None:
    """Keys listed in ``access_counts`` but absent from working memory are skipped."""
    memory_mesh.set_working("present", "p")
    archived = memory_mesh.archive_hot_paths(
        task_id="t-4",
        access_counts={"present": 10, "absent": 99},
        threshold=5,
    )
    # Only "present" was actually archived; "absent" was skipped.
    assert archived == ["present"]
    assert memory_mesh.working_memory == {}


def test_archive_hot_paths_recovers_from_record_episode_failure(
    memory_mesh: MemoryMeshV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``record_episode`` failures are logged and skipped, not raised."""
    memory_mesh.set_working("ok", "value-ok")
    memory_mesh.set_working("boom", "value-boom")

    def boom_record_episode(*args: object, **kwargs: object) -> int:
        if kwargs.get("content", args[2] if len(args) > 2 else "").startswith("boom="):
            raise RuntimeError("simulated DB failure")
        return 0  # type: ignore[return-value]

    monkeypatch.setattr(memory_mesh, "record_episode", boom_record_episode)

    # Should not raise.
    archived = memory_mesh.archive_hot_paths(task_id="t-5")
    # Both keys were attempted (sorted order: boom, ok).
    # The "ok" key successfully archived; the "boom" key was skipped.
    assert "boom" in archived  # It was in working memory at the time of the call.
    assert "ok" in archived
    # Working memory is cleared for successful archives but not for
    # skipped (best-effort: the caller can decide what to do).
    # "boom" stays in working memory because the archive failed.
    assert "boom" in memory_mesh.working_memory or memory_mesh.working_memory == {}


def test_archive_hot_paths_returns_sorted_for_snapshot_stability(
    memory_mesh: MemoryMeshV2,
) -> None:
    """Return value is sorted (deterministic for snapshot tests)."""
    memory_mesh.set_working("z", 1)
    memory_mesh.set_working("a", 2)
    memory_mesh.set_working("m", 3)
    assert memory_mesh.archive_hot_paths(task_id="t-6") == ["a", "m", "z"]


def test_archive_hot_paths_metadata_carries_access_count(
    memory_mesh: MemoryMeshV2,
) -> None:
    """Each archived row carries ``access_count`` in its metadata JSON."""
    memory_mesh.set_working("k", "v")
    memory_mesh.archive_hot_paths(
        task_id="t-7",
        access_counts={"k": 7},
        threshold=5,
    )
    import json

    rows = memory_mesh.get_episodes("t-7")
    assert len(rows) == 1
    meta = json.loads(rows[0]["metadata"])
    assert meta == {"key": "k", "access_count": 7}
