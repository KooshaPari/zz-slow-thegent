"""Session persistence for compositor layouts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from yaml import YAMLError, safe_dump, safe_load


class SessionState:
    """Persist one named compositor session as YAML."""

    def __init__(self, session_name: str = "default", session_dir: Path | None = None) -> None:
        self.session_name = self._safe_session_name(session_name)
        self.session_dir = session_dir or Path.home() / ".thegent" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / f"{self.session_name}.yaml"
        self._state: dict[str, Any] = {}

    @staticmethod
    def _safe_session_name(session_name: str) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_name).strip(".-")
        return safe_name or "default"

    def get(self, key: str) -> Any:
        """Get state value."""
        return self._state.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set state value."""
        self._state[key] = value

    def save_session(self, layout: dict[str, Any]) -> bool:
        """Save the provided layout."""
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.session_file.write_text(safe_dump(layout), encoding="utf-8")
        except OSError:
            return False
        return True

    def load_session(self) -> dict[str, Any] | None:
        """Load this session layout if it exists."""
        if not self.session_file.exists():
            return None
        try:
            data = safe_load(self.session_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, YAMLError):
            return None
        return data if isinstance(data, dict) else None

    def delete_session(self) -> bool:
        """Delete this session file."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
        except OSError:
            return False
        return True

    def list_sessions(self) -> list[str]:
        """Return known session names."""
        if not self.session_dir.exists():
            return []
        return sorted(path.stem for path in self.session_dir.glob("*.yaml"))

    def session_exists(self) -> bool:
        """Return whether this session has persisted data."""
        return self.session_file.exists()


__all__ = ["SessionState"]
