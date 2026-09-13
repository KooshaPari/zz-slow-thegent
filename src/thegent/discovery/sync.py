"""Stub module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class SyncDiscovery:
    """Discovery for sync services."""

    def __init__(self) -> None:
        self._services: dict = {}

    def discover(self, name: str) -> dict | None:
        return self._services.get(name)


class SyncLoop:
    """Sync loop for service discovery."""

    def __init__(self, registry: Any = None, sync_dir: str | Path | None = None, **kwargs) -> None:
        self._running = False
        self.registry = registry
        self.sync_dir = Path(sync_dir) if sync_dir else None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def start(self) -> None:
        """Start the sync loop."""
        self._running = True

    def stop(self) -> None:
        """Stop the sync loop."""
        self._running = False

    def _collect_local_state(self, sync_dir: str | Path | None = None) -> dict:
        """Collect local service state from filesystem.

        Args:
            sync_dir: Directory to scan for state files.

        Returns:
            Dict with active_teams and other state.

        Raises:
            ValueError: If team_registry.json is malformed.
        """
        base_dir = Path(sync_dir) if sync_dir else Path()

        # Read team_registry.json
        team_file = base_dir / ".thegent" / "team_registry.json"
        active_teams = []
        if team_file.exists():
            content = team_file.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed team_registry.json: {e}") from e
            active_teams = [t for t in data.get("teams", []) if t.get("active", False)]

        return {"active_teams": active_teams}

    def _push_state_to_peer(self, peer_dir: Path, source_id: str, state: dict) -> None:
        """Push state to a peer directory.

        Args:
            peer_dir: Peer directory to push to.
            source_id: Source identifier.
            state: State to push.
        """
        inbox_dir = peer_dir / ".thegent" / "sync_inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        out_file = inbox_dir / "local_state.json"
        out_file.write_text(json.dumps(state), encoding="utf-8")

    def is_running(self) -> bool:
        """Check if loop is running."""
        return self._running


__all__ = ["SyncDiscovery", "SyncLoop"]
