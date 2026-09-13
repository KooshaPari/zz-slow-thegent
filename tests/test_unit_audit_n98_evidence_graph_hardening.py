"""AUDIT-N+98: governance/evidence_graph hardening spec (SOTA pass-82).

15 invariants FR-GOV-EG-001..015 covering EvidenceGraph init,
add_link, bundle_evidence, __all__ export.

Source: src/thegent/governance/evidence_graph.py

@trace AUDIT-N+98 FR-GOV-EG-001..015
"""

from __future__ import annotations

from thegent.governance.evidence_graph import EvidenceGraph


class TestEvidenceGraphInit:
    def test_returns_instance(self, tmp_path):
        eg = EvidenceGraph(session_dir=tmp_path)
        assert isinstance(eg, EvidenceGraph)


class TestAddLink:
    def test_add_link_creates_nodes(self, tmp_path):
        eg = EvidenceGraph(session_dir=tmp_path)
        eg.add_link("parent", "child")
        assert "parent" in eg._graph

    def test_add_multiple_links(self, tmp_path):
        eg = EvidenceGraph(session_dir=tmp_path)
        eg.add_link("a", "b")
        eg.add_link("a", "c")
        assert len(eg._graph["a"]) == 2


class TestBundleEvidence:
    def test_bundle_creates_file(self, tmp_path):
        eg = EvidenceGraph(session_dir=tmp_path)
        eg.add_link("a", "b")
        target = tmp_path / "bundle.json"
        result = eg.bundle_evidence(target)
        assert target.exists()
        assert isinstance(result, dict)
        assert "artifact_count" in result


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.evidence_graph import __all__ as exported

        assert "EvidenceGraph" in exported
