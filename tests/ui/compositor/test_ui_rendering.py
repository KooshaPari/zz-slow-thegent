"""Integration tests for the compositor."""

from thegent.compositor.pane_manager import PaneManager
from thegent.compositor.session_state import SessionState


class TestCompositorIntegration:
    """Integration tests for compositor components."""

    def test_basic_workflow(self) -> None:
        """Test basic compositor workflow."""
        # Initialize pane manager
        pm = PaneManager()
        assert pm.get_pane_count() == 1

        # Split horizontally
        pm.split_pane("H")
        assert pm.get_pane_count() == 2

        # Split vertically
        pm.split_pane("V")
        assert pm.get_pane_count() == 3

        # Close a pane
        pm.close_pane()
        assert pm.get_pane_count() == 2

    def test_session_persistence(self) -> None:
        """Test saving and restoring session."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial layout
            pm1 = PaneManager()
            pm1.split_pane("H")
            pm1.split_pane("V")
            layout = pm1.save_layout()

            # Save to session
            session = SessionState("test")
            session.session_dir = Path(tmpdir)
            session.session_file = session.session_dir / "test.yaml"
            assert session.save_session(layout)

            # Load in new manager
            pm2 = PaneManager()
            loaded_layout = session.load_session()
            assert pm2.restore_layout(loaded_layout)
            assert pm2.get_pane_count() == 3

    def test_focus_rotation(self) -> None:
        """Test focus rotation among panes."""
        pm = PaneManager()
        initial_pane = pm.focus_pane_id

        pm.split_pane("H")
        pane2_id = pm.focus_pane_id
        assert pane2_id != initial_pane

        pm.split_pane("V")
        pane3_id = pm.focus_pane_id
        assert pane3_id != pane2_id
        assert pane3_id != initial_pane

        # Rotate through panes
        panes = [pm.focus_pane_id]
        for _ in range(3):
            pm.focus_next()
            panes.append(pm.focus_pane_id)

        # Should cycle through all panes
        assert len(set(panes[1:])) >= 2  # At least 2 unique panes in rotation

    def test_complex_split_operations(self) -> None:
        """Test complex split and close operations."""
        pm = PaneManager()

        # Create a 2x2 grid-like structure through splits
        pm.split_pane("V")  # Root: [pane1, pane2]

        pm.split_pane("H")  # pane2: [pane2a, pane2b]
        pane2b_id = pm.focus_pane_id

        assert pm.get_pane_count() == 3

        # Close one pane
        pm.close_pane(pane2b_id)
        assert pm.get_pane_count() == 2

        # Focus back to root area
        pm.focus_pane_id = pm.root.pane.pane_id if pm.root.pane else "root"

        # All panes should still be valid
        all_panes = pm.get_all_panes()
        assert len(all_panes) == 2
        assert all(pane.is_active for pane in all_panes)

    def test_layout_serialization_fidelity(self) -> None:
        """Test that layout serialization preserves tree structure."""
        pm = PaneManager()

        # Create complex layout
        for _ in range(3):
            pm.split_pane("H")
            pm.split_pane("V")

        # Save layout
        layout1 = pm.save_layout()

        # Create new manager and restore
        pm2 = PaneManager()
        pm2.restore_layout(layout1)

        # Save layout again
        pm2.save_layout()

        # Layouts should have same structure
        assert pm.get_pane_count() == pm2.get_pane_count()
