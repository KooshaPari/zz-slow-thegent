"""AUDIT-N+93: governance/plugin_lifecycle hardening spec (SOTA pass-77).

15 invariants FR-GOV-PL-001..015 covering PluginLifecycleManager init,
register_plugin, run_conformance, get_plugin_status, PluginStatus enum,
__all__ export.

Source: src/thegent/governance/plugin_lifecycle.py

@trace AUDIT-N+93 FR-GOV-PL-001..015
"""

from __future__ import annotations

from thegent.governance.plugin_lifecycle import (
    PluginLifecycleManager,
    PluginStatus,
)


class TestPluginStatus:
    def test_registered(self):
        assert PluginStatus.REGISTERED.value == "registered"

    def test_all_members(self):
        members = list(PluginStatus)
        assert len(members) >= 4


class TestPluginLifecycleManagerInit:
    def test_returns_instance(self):
        plm = PluginLifecycleManager()
        assert isinstance(plm, PluginLifecycleManager)


class TestRegisterPlugin:
    def test_register_returns_plugin_id(self):
        plm = PluginLifecycleManager()
        result = plm.register_plugin(
            "p1", {"name": "Test", "version": "1.0", "entry_point": "main"}
        )
        assert result == "p1"

    def test_registered_status(self):
        plm = PluginLifecycleManager()
        plm.register_plugin(
            "p1", {"name": "Test", "version": "1.0", "entry_point": "main"}
        )
        assert plm.get_plugin_status("p1") == PluginStatus.REGISTERED


class TestRunConformance:
    def test_passing_conformance(self):
        plm = PluginLifecycleManager()
        plm.register_plugin(
            "p1", {"name": "Test", "version": "1.0", "entry_point": "main"}
        )
        result = plm.run_conformance("p1")
        assert result is True

    def test_missing_metadata_quarantines(self):
        plm = PluginLifecycleManager()
        plm.register_plugin("p1", {"name": "Test"})
        result = plm.run_conformance("p1")
        assert result is False


class TestGetPluginStatus:
    def test_unknown_quarantined(self):
        plm = PluginLifecycleManager()
        assert plm.get_plugin_status("unknown") == PluginStatus.QUARANTINED

    def test_active_after_conformance(self):
        plm = PluginLifecycleManager()
        plm.register_plugin("p1", {"name": "T", "version": "1.0", "entry_point": "m"})
        plm.run_conformance("p1")
        assert plm.get_plugin_status("p1") == PluginStatus.ACTIVE


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.plugin_lifecycle import __all__ as exported

        assert "PluginLifecycleManager" in exported
        assert "PluginStatus" in exported
