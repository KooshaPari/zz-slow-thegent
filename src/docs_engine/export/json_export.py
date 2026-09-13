"""JSON export - STUB."""
from __future__ import annotations

import json


class JsonExporter:
    """Exporter for JSON format."""

    def __init__(self, pretty: bool = False) -> None:
        self.pretty = pretty

    def export(self, data: dict | list) -> str:
        """Export data to JSON format."""
        if self.pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)


__all__ = ["JsonExporter"]
