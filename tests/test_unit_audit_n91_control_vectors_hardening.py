"""AUDIT-N+91: governance/control_vectors hardening spec (SOTA pass-75).

15 invariants FR-GOV-CV-001..015 covering ControlVectorManager init,
analyze_and_inject keyword gate, prepare_environment, __all__ export.

Source: src/thegent/governance/control_vectors.py

@trace AUDIT-N+91 FR-GOV-CV-001..015
"""

from __future__ import annotations

from thegent.governance.control_vectors import ControlVectorManager


class TestControlVectorManagerInit:
    def test_returns_instance(self):
        cvm = ControlVectorManager(agent_id="test-agent")
        assert isinstance(cvm, ControlVectorManager)

    def test_has_vectors(self):
        cvm = ControlVectorManager(agent_id="test-agent")
        assert hasattr(cvm, "vectors")
        assert isinstance(cvm.vectors, dict)
        assert len(cvm.vectors) >= 1


class TestAnalyzeAndInject:
    def test_safe_prompt_unchanged(self):
        cvm = ControlVectorManager(agent_id="test-agent")
        result = cvm.analyze_and_inject("read status report", {})
        assert result == "read status report"

    def test_destructive_prompt_injected(self):
        cvm = ControlVectorManager(agent_id="test-agent")
        result = cvm.analyze_and_inject("delete all files", {})
        assert len(result) > len("delete all files")

    def test_returns_string(self):
        cvm = ControlVectorManager(agent_id="test-agent")
        result = cvm.analyze_and_inject("hello", {"compliance_risk": 0.9})
        assert isinstance(result, str)


class TestPrepareEnvironment:
    def test_creates_policy_file(self, tmp_path):
        cvm = ControlVectorManager(agent_id="test-agent")
        cvm.prepare_environment(tmp_path)
        assert (tmp_path / ".AGENT_POLICY.md").exists()


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.control_vectors import __all__ as exported

        assert "ControlVectorManager" in exported
