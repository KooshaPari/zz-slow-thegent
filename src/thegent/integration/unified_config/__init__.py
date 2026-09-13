"""Unified config integration module."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class UnifiedConfigManager:
    """Manages unified configuration across thegent."""

    def __init__(self, config_dir: Path | str | None = None) -> None:
        self._config: dict[str, Any] = {}
        self._config_dir = Path(config_dir) if config_dir else Path("/tmp")
        self._data: dict[str, Any] = {}
        self.config_sources: list[tuple[str, Path]] = []
        self.unified_config: dict[str, Any] = {}
        self.last_sync_conflicts: dict = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def sync_configs(self) -> None:
        """Sync configurations across all sources.

        1. Detect conflicts between sources
        2. Resolve conflicts (prefer first source in config_sources)
        3. Write merged values back to files
        """
        import yaml

        # Detect conflicts between sources - only for leaf values
        conflicts = {}
        key_sources: dict[str, dict[str, Any]] = {}

        def flatten_config(config: dict, prefix: str = "") -> dict:
            """Flatten nested config to dot-notation keys."""
            result = {}
            for k, v in config.items():
                new_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict) and v:
                    result.update(flatten_config(v, new_key))
                else:
                    result[new_key] = v
            return result

        def unflatten_config(flat: dict) -> dict:
            """Unflatten dot-notation keys back to nested dict."""
            result = {}
            for key, value in flat.items():
                parts = key.split(".")
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            return result

        for source, config in self.unified_config.items():
            flat = flatten_config(config)
            for key, value in flat.items():
                if key not in key_sources:
                    key_sources[key] = {}
                key_sources[key][source] = value

        # Find conflicts (same key, different values)
        for key, sources in key_sources.items():
            if len(sources) > 1:
                unique_values = set()
                for v in sources.values():
                    if isinstance(v, (dict, list)):
                        continue  # Skip complex types
                    unique_values.add(v)
                if len(unique_values) > 1:
                    # Conflict exists
                    conflicts[key] = sources

        # Resolve conflicts - prefer first source in config_sources, else first in unified_config
        resolved = {}

        # Apply sources in order of priority - first source wins
        sources_order = [s for s, _ in self.config_sources] if self.config_sources else []

        # If config_sources is empty, use unified_config keys as order
        if not sources_order:
            sources_order = list(self.unified_config.keys())

        for source in sources_order:
            if source in self.unified_config:
                flat = flatten_config(self.unified_config[source])
                # Only add keys that haven't been resolved yet
                for key, value in flat.items():
                    if key not in resolved:
                        resolved[key] = value

        # Non-conflicting values are already picked by first source
        # Only add values from sources not yet processed
        for key, sources in key_sources.items():
            if key not in resolved:
                # Pick the first available value
                for value in sources.values():
                    resolved[key] = value
                    break

        # Build last_sync_conflicts with full conflict details
        # Structure: {key: {source: value, ...}, ...}
        self.last_sync_conflicts = conflicts.copy()

        # Write resolved config back to files
        for source, path in self.config_sources:
            if source in self.unified_config:
                # Get this source's values, using resolved values for conflicts
                source_flat = {}
                for key, sources in key_sources.items():
                    if key in conflicts:
                        # Use resolved value for conflicting keys
                        source_flat[key] = resolved.get(key)
                    elif source in sources:
                        source_flat[key] = sources[source]

                # Write back
                if path.suffix in (".yaml", ".yml"):
                    content = yaml.dump(unflatten_config(source_flat))
                    path.write_text(content, encoding="utf-8")
                elif path.name in ("WORK_STREAM.md", "PLAN.md"):
                    # Write YAML frontmatter
                    content = f"---\n{yaml.dump(unflatten_config(source_flat))}---\n"
                    existing = path.read_text(encoding="utf-8")
                    # Preserve body after ---
                    if "---" in existing:
                        parts = existing.split("---", 2)
                        content = f"---\n{yaml.dump(unflatten_config(source_flat))}---{parts[2] if len(parts) > 2 else ''}"
                    path.write_text(content, encoding="utf-8")

        self._data["conflicts"] = conflicts

    def merge(self, other: dict[str, Any], strategy: str = "prefer_existing") -> dict[str, Any]:
        """Merge configurations with conflict resolution."""
        result = self._config.copy()
        for key, value in other.items():
            if key not in result or strategy == "prefer_new":
                result[key] = value
        return result

    def load(self) -> dict:
        """Load the unified configuration."""
        return self._data

    @property
    def last_sync_config(self) -> dict | None:
        """Get the last sync configuration."""
        return self._data.get("last_sync")

    @property
    def last_sync_conflicts(self) -> dict | None:
        """Get the last sync conflicts."""
        return getattr(self, "_last_sync_conflicts", self._data.get("conflicts"))

    @last_sync_conflicts.setter
    def last_sync_conflicts(self, value: dict) -> None:
        """Set the last sync conflicts."""
        self._last_sync_conflicts = value


__all__ = ["UnifiedConfigManager"]
