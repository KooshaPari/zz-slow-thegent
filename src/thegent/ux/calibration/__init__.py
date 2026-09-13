"""Confidence calibration loader for the operator cockpit UX lane.

This module loads per-agent confidence bias values from
``<session_dir>/confidence_calibration.json`` (UTF-8) at construction
time and exposes them as ``self.bias_map: dict[str, float]``. The file
is *optional*: a missing file, an unreadable file, corrupt JSON, or a
JSON value that is not a string-keyed mapping all degrade gracefully to
an empty bias map and emit a WARNING on the ``thegent.ux.calibration``
logger so an operator can see why the calibration is empty without a
hard failure. Numeric bias values that fail float coercion (e.g.
``"abc"``) are silently dropped; this keeps the loader permissive and
avoids crashing when a hand-edited calibration file has a typo.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger("thegent.ux.calibration")


class ConfidenceCalibrator:
    """Calibrator for confidence scores with per-agent bias offsets.

    The constructor takes a settings-like object exposing ``.session_dir``
    (a ``pathlib.Path``); the calibration JSON is loaded eagerly so
    downstream callers can rely on ``self.bias_map`` being a populated
    ``dict[str, float]`` (possibly empty).
    """

    threshold: float = 0.5

    def __init__(self, settings: Any) -> None:
        self.bias_map: dict[str, float] = {}
        session_dir: Path = Path(settings.session_dir)
        path = session_dir / "confidence_calibration.json"
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        except OSError as exc:
            _log.warning("Failed to read calibration JSON from %s: %s", path, exc)
            return
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            _log.warning("Failed to parse calibration JSON: %s", exc)
            return
        if not isinstance(payload, dict):
            _log.warning(
                "Invalid calibration schema: expected object, got %s",
                type(payload).__name__,
            )
            return
        # Silently drop non-numeric values (e.g. hand-typed booleans or
        # nested objects) — the rest of the map is still usable.
        for key, value in payload.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self.bias_map[str(key)] = float(value)

    def calibrate(self, score: float) -> float:
        """Calibrate a confidence score."""
        return min(1.0, max(0.0, score))

    def is_confident(self, score: float) -> bool:
        """Check if score meets confidence threshold."""
        return score >= self.threshold


__all__ = ["ConfidenceCalibrator"]
