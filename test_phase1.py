#!/usr/bin/env python3
"""Quick validation script for Phase 1 implementation."""

import sys
import tempfile
from pathlib import Path

# Test imports
try:
    from thegent.compositor import CompositApp, PaneManager, SessionState, TerminalPane

except ImportError:
    sys.exit(1)

# Test TerminalPane
try:
    pane = TerminalPane("test-pane", "/tmp")
    assert pane.pane_id == "test-pane"
    assert pane.working_dir == "/tmp"
except Exception:
    sys.exit(1)

# Test PaneManager
try:
    pm = PaneManager()
    assert pm.get_pane_count() == 1
    new_pane = pm.split_pane("H")
    assert pm.get_pane_count() == 2
    pm.close_pane(new_pane.pane.pane_id)
    assert pm.get_pane_count() == 1
except Exception:
    sys.exit(1)

# Test SessionState
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        state = SessionState("test")
        state.session_dir = Path(tmpdir)
        state.session_file = state.session_dir / "test.yaml"

        layout = {"type": "pane", "id": "root"}
        assert state.save_session(layout)
        loaded = state.load_session()
        assert loaded is not None
except Exception:
    sys.exit(1)

# Test layout serialization
try:
    pm = PaneManager()
    pm.split_pane("H")
    pm.split_pane("V")
    layout = pm.save_layout()

    pm2 = PaneManager()
    pm2.restore_layout(layout)
    assert pm2.get_pane_count() == 3
except Exception:
    sys.exit(1)

# Test focus rotation
try:
    pm = PaneManager()
    pm.split_pane("H")
    initial = pm.focus_pane_id
    pm.focus_next()
    assert pm.focus_pane_id != initial
    pm.focus_next()
    assert pm.focus_pane_id == initial
except Exception:
    sys.exit(1)
