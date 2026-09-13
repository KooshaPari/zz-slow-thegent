"""WP-23001: Hierarchical Memory System (MemoryMesh v2).
Implements a triple-tier memory architecture:
1. Working Memory (Transient, turn-based)
2. Episodic Memory (Persistent log of task outcomes)
3. Semantic Memory (Persistent Knowledge Graph / Mem0 pattern)
"""

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson as json
from pydantic import BaseModel, Field

_log = logging.getLogger(__name__)


class MemoryNode(BaseModel):
    """A node in the Semantic Memory knowledge graph."""

    id: str
    type: str  # e.g., 'concept', 'codebase_component', 'design_decision'
    content: str
    metadata: dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class MemoryEdge(BaseModel):
    """A relationship between memory nodes."""

    source_id: str
    target_id: str
    relation: str  # e.g., 'depends_on', 'implements', 'references'
    weight: float = 1.0


class MemoryMeshV2:
    """Manages hierarchical memory for thegent agents."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path.home() / ".thegent" / "memory_v2.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.working_memory: dict[str, Any] = {}

    def _init_db(self) -> None:
        """Initialize the SQLite database for Episodic and Semantic tiers."""
        with sqlite3.connect(self.db_path) as conn:
            # Episodic Memory: Log of events and outcomes
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodic_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    outcome TEXT,
                    metadata TEXT
                )
                """
            )
            # Semantic Memory: Knowledge Graph (Nodes)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )
            # Semantic Memory: Knowledge Graph (Edges)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    PRIMARY KEY (source_id, target_id, relation),
                    FOREIGN KEY (source_id) REFERENCES semantic_nodes(id),
                    FOREIGN KEY (target_id) REFERENCES semantic_nodes(id)
                )
                """
            )

    # --- Tier 1: Working Memory (Transient) ---

    def set_working(self, key: str, value: Any) -> None:
        self.working_memory[key] = value

    def get_working(self, key: str) -> Any:
        return self.working_memory.get(key)

    def clear_working(self) -> None:
        self.working_memory.clear()

    # --- Tier 2: Episodic Memory (Persistent Log) ---

    def record_episode(
        self,
        task_id: str,
        event_type: str,
        content: str,
        outcome: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Record a task episode or attempt."""
        ts = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO episodic_log (task_id, timestamp, event_type, content, outcome, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, ts, event_type, content, outcome, json.dumps(metadata or {}).decode()),
            )
            return cursor.lastrowid or 0

    def get_episodes(self, task_id: str) -> list[dict[str, Any]]:
        """Retrieve historical episodes for a task to prevent reasoning loops."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM episodic_log WHERE task_id = ? ORDER BY timestamp ASC", (task_id,))
            return [dict(row) for row in cursor]

    # --- Hot-path archival (WL-136 / L19 memory hygiene) ---

    def archive_hot_paths(
        self,
        task_id: str,
        *,
        access_counts: dict[str, int] | None = None,
        threshold: int = 5,
    ) -> list[str]:
        """Archive hot working-memory keys into the episodic log.

        A key is "hot" when its access count meets or exceeds
        ``threshold``. Hot keys represent data that the agent is
        consulting repeatedly; their full content should be persisted
        to episodic memory so a session restart doesn't lose context,
        while the working-memory slot is freed for new state.

        Args:
            task_id: Identifier used to group archived episodes in the
                episodic log (lets ``get_episodes`` reconstruct the
                session timeline).
            access_counts: Optional override mapping ``key -> access
                count``. When ``None`` (the common case) every key in
                ``working_memory`` is treated as hot and archived.
                Callers that maintain their own access counter (e.g.
                via a ``Counter`` over a public read API) can pass it
                here to honour their own definition of "hot".
            threshold: Minimum access count required to qualify a key
                as hot. Ignored when ``access_counts`` is ``None`` (in
                which case everything qualifies, matching the legacy
                ``clear_working`` behaviour but preserving content).

        Returns:
            Sorted list of archived keys (deterministic for snapshot
            tests).

        Notes:
            Best-effort: ``record_episode`` failures are logged and
            skipped so a transient DB error doesn't break the calling
            code path. The corresponding working-memory key is only
            cleared after the archive succeeds.
        """
        if access_counts is None:
            # No counter supplied — treat every working-memory key as
            # hot. This preserves the WL-136 contract: the function is
            # safe to call unconditionally as part of session teardown.
            hot = sorted(self.working_memory.keys())
        else:
            # Only count keys that are actually in working memory;
            # access_counts entries for absent keys are advisory and
            # do not represent archivable state.
            hot = sorted(
                key for key, count in access_counts.items() if count >= threshold and key in self.working_memory
            )
        for key in hot:
            value = self.working_memory.get(key)
            if value is None:
                continue
            try:
                self.record_episode(
                    task_id=task_id,
                    event_type="hot_path_archive",
                    content=f"{key}={value!r}",
                    outcome="archived",
                    metadata={"key": key, "access_count": (access_counts or {}).get(key)},
                )
            except Exception as exc:  # noqa: BLE001 — best-effort, see docstring
                _log.warning("hot_path_archive skipped for key %r: %s", key, exc)
                continue
            self.working_memory.pop(key, None)
        return hot

    # --- Tier 3: Semantic Memory (Knowledge Graph) ---

    def add_knowledge(self, node: MemoryNode, relations: list[MemoryEdge] | None = None) -> None:
        """Add a node and its relations to the knowledge graph."""
        if relations is None:
            relations = []
        with sqlite3.connect(self.db_path) as conn:
            # UPSERT node
            conn.execute(
                """
                INSERT INTO semantic_nodes (id, type, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content=excluded.content,
                    metadata=excluded.metadata,
                    timestamp=excluded.timestamp
                """,
                (node.id, node.type, node.content, json.dumps(node.metadata).decode(), node.timestamp),
            )
            # Add edges
            for edge in relations:
                conn.execute(
                    """
                    INSERT INTO semantic_edges (source_id, target_id, relation, weight)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_id, target_id, relation) DO UPDATE SET
                        weight=excluded.weight
                    """,
                    (edge.source_id, edge.target_id, edge.relation, edge.weight),
                )

    def query_knowledge(self, query: str, limit: int = 10) -> list[MemoryNode]:
        """Simple keyword-based semantic search. (Future: Vector search)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM semantic_nodes WHERE content LIKE ? OR id LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            )
            return [
                MemoryNode(
                    id=row["id"],
                    type=row["type"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"] or "{}"),
                    timestamp=row["timestamp"],
                )
                for row in cursor
            ]

    def get_related_nodes(self, node_id: str) -> list[MemoryNode]:
        """Find all nodes directly related to the given node."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT n.* FROM semantic_nodes n
                JOIN semantic_edges e ON (n.id = e.target_id AND e.source_id = ?)
                OR (n.id = e.source_id AND e.target_id = ?)
                """,
                (node_id, node_id),
            )
            return [
                MemoryNode(
                    id=row["id"],
                    type=row["type"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"] or "{}"),
                    timestamp=row["timestamp"],
                )
                for row in cursor
            ]
