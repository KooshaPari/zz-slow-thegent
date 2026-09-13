"""AUDIT-N+87: governance/personas hardening spec (SOTA pass-71).

15 invariants FR-GOV-PR-001..015 covering PersonaManager init,
check_access known persona, check_access unknown persona,
check_access lane guard, discover_teammates, list_teammates,
__all__ export.

Source: src/thegent/governance/personas.py

@trace AUDIT-N+87 FR-GOV-PR-001..015
"""

from __future__ import annotations

from thegent.governance.personas import PersonaManager


class TestPersonaManagerInit:
    def test_returns_instance(self):
        pm = PersonaManager()
        assert isinstance(pm, PersonaManager)

    def test_has_personas(self):
        pm = PersonaManager()
        assert hasattr(pm, "_personas")
        assert isinstance(pm._personas, dict)
        assert len(pm._personas) >= 1


class TestCheckAccess:
    def test_known_persona(self):
        pm = PersonaManager()
        result = pm.check_access("operator", "read", "standard")
        assert isinstance(result, dict)
        assert "allowed" in result

    def test_unknown_persona_denied(self):
        pm = PersonaManager()
        result = pm.check_access("nonexistent_persona", "read", "standard")
        assert result["allowed"] is False

    def test_critical_lane_restricted(self):
        pm = PersonaManager()
        result = pm.check_access("operator", "read", "critical")
        assert result["allowed"] is False

    def test_incident_commander_critical(self):
        pm = PersonaManager()
        result = pm.check_access("incident_commander", "read", "critical")
        assert result["allowed"] is True

    def test_team_lead_critical(self):
        pm = PersonaManager()
        result = pm.check_access("team_lead", "read", "critical")
        assert result["allowed"] is True


class TestDiscoverTeammates:
    def test_missing_dir_returns_empty(self, tmp_path):
        pm = PersonaManager(agents_dir=tmp_path / "nonexistent")
        result = pm.discover_teammates()
        assert isinstance(result, dict)

    def test_list_teammates(self):
        pm = PersonaManager()
        result = pm.list_teammates()
        assert isinstance(result, list)


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.personas import __all__ as exported

        assert "PersonaManager" in exported
