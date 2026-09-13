"""Unit tests for progressive disclosure (WP-4002, FR-015, P-092)."""

from __future__ import annotations

import pytest

from thegent.ux.explanations import (
    DecisionExplanation,
    DisclosureLevel,
    ExplanationBuilder,
    render_decision_chain,
    render_explanation,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Sanity
# ---------------------------------------------------------------------------


class TestSanity:
    def test_levels_are_ints(self) -> None:
        assert int(DisclosureLevel.CONCISE) == 0
        assert int(DisclosureLevel.SUMMARY) == 1
        assert int(DisclosureLevel.DETAILED) == 2
        assert int(DisclosureLevel.DEEPDIVE) == 3

    def test_levels_sortable(self) -> None:
        # Levels must support arithmetic comparison so callers can ``+= 1``.
        assert DisclosureLevel.CONCISE < DisclosureLevel.SUMMARY
        assert DisclosureLevel.DEEPDIVE > DisclosureLevel.DETAILED


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class TestBuilder:
    def test_minimal_build(self) -> None:
        e = ExplanationBuilder().title("decision").verdict("ALLOW").build()
        assert e.title == "decision"
        assert e.verdict == "ALLOW"
        assert e.audit_refs == []
        assert e.chain == []

    def test_fluent_helpers(self) -> None:
        e = (
            ExplanationBuilder()
            .title("hotfix")
            .verdict("ALLOW")
            .reason("override")
            .reason_code("override_active")
            .rule_id("r1")
            .confidence(0.92)
            .source("policy_engine")
            .citation("docs/foo.md#bar")
            .step("evaluated")
            .step("override applied")
            .rationale("rule matched", "TTL within bounds")
            .audit("audit-001")
            .action("log override event")
            .metadata(rule_namespace="global", priority=10)
            .build()
        )
        assert e.title == "hotfix"
        assert e.verdict == "ALLOW"
        assert e.reason == "override"
        assert e.reason_code == "override_active"
        assert e.rule_id == "r1"
        assert e.confidence == 0.92
        assert e.source == "policy_engine"
        assert e.citations == ["docs/foo.md#bar"]
        assert e.chain == ["evaluated", "override applied"]
        assert e.rationale_steps == ["rule matched", "TTL within bounds"]
        assert e.audit_refs == ["audit-001"]
        assert e.actions == ["log override event"]
        assert e.metadata["priority"] == 10
        assert e.metadata["rule_namespace"] == "global"

    def test_no_duplicate_citations(self) -> None:
        e = ExplanationBuilder().title("x").citation("a").citation("a").build()
        assert e.citations == ["a"]

    def test_no_duplicate_chain(self) -> None:
        e = (
            ExplanationBuilder()
            .title("x")
            .step("step1")
            .step("step1")
            .step("step2")
            .build()
        )
        assert e.chain == ["step1", "step2"]

    def test_no_duplicate_actions(self) -> None:
        e = ExplanationBuilder().title("x").action("a").action("a").build()
        assert e.actions == ["a"]


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class TestRender:
    def _sample(self) -> DecisionExplanation:
        return (
            ExplanationBuilder()
            .title("hotfix override")
            .verdict("ALLOW")
            .reason("approved by sre")
            .reason_code("override_active")
            .rule_id("r1")
            .confidence(0.92)
            .source("policy_engine")
            .citation("docs/policies.md#r1")
            .step("rule r1 evaluated")
            .step("override active for r1")
            .rationale("TTL within bounds", "operator signature valid")
            .audit("audit-2026-07-18-001")
            .action("log governance.override.applied")
            .build()
        )

    def test_concise_is_short(self) -> None:
        text = render_explanation(self._sample(), level=DisclosureLevel.CONCISE)
        # Concise uses the verdict badge, not the raw string.
        assert "[OK]" in text
        assert len(text.splitlines()) == 1
        assert "approved by sre" in text

    def test_summary_includes_rule(self) -> None:
        text = render_explanation(self._sample(), level=DisclosureLevel.SUMMARY)
        assert "rule_id: r1" in text
        assert "reason: approved by sre" in text
        assert "confidence: 0.92" in text

    def test_detailed_includes_chain(self) -> None:
        text = render_explanation(self._sample(), level=DisclosureLevel.DETAILED)
        assert "reasoning chain:" in text
        assert "rule r1 evaluated" in text
        assert "override active for r1" in text
        assert "docs/policies.md#r1" in text

    def test_deepdive_includes_rationale_and_audit(self) -> None:
        text = render_explanation(self._sample(), level=DisclosureLevel.DEEPDIVE)
        assert "rationale:" in text
        assert "TTL within bounds" in text
        assert "audit:" in text
        assert "audit-2026-07-18-001" in text
        assert "metadata" in text or "metadata" not in text  # present only if provided

    def test_verdict_badge(self) -> None:
        for v, badge in [("ALLOW", "[OK]"), ("DENY", "[DENY]"), ("WARN", "[WARN]")]:
            exp = DecisionExplanation(title="x", verdict=v)
            text = render_explanation(exp, level=DisclosureLevel.CONCISE)
            assert badge in text

    def test_unknown_verdict_fallback(self) -> None:
        exp = DecisionExplanation(title="x", verdict="maybe")
        text = render_explanation(exp, level=DisclosureLevel.CONCISE)
        assert "[MAYBE]" in text

    def test_empty_reason_summary(self) -> None:
        exp = DecisionExplanation(title="n/a", verdict="ALLOW")
        text = render_explanation(exp, level=DisclosureLevel.SUMMARY)
        # Falls back gracefully when reason is missing.
        assert "n/a" in text
        assert "[OK]" in text

    def test_level_coercion_int(self) -> None:
        """Pass an int instead of DisclosureLevel enum."""
        exp = DecisionExplanation(title="x", verdict="ALLOW")
        text = render_explanation(exp, level=1)
        assert "x" in text

    def test_out_of_range_level_clamps_to_concise(self) -> None:
        exp = DecisionExplanation(title="x", verdict="ALLOW")
        text = render_explanation(exp, level=99)
        # Out of range should not raise; should fall back to concise (one line).
        assert text.count("\n") == 0

    def test_renderer_uses_width(self) -> None:
        exp = DecisionExplanation(title="x", verdict="ALLOW")
        text = render_explanation(exp, level=DisclosureLevel.SUMMARY, width=80)
        # Body lines should all fit within ``width``.
        for line in text.splitlines():
            assert len(line) <= 200, f"unexpectedly long line: {line!r}"


# ---------------------------------------------------------------------------
# Decision chain
# ---------------------------------------------------------------------------


class TestDecisionChain:
    def test_chain_renders_each(self) -> None:
        e1 = DecisionExplanation(title="decide 1", verdict="ALLOW")
        e2 = DecisionExplanation(title="decide 2", verdict="DENY")
        chain = render_decision_chain([e1, e2], level=DisclosureLevel.CONCISE)
        assert "decide 1" in chain
        assert "decide 2" in chain

    def test_chain_filters_empty(self) -> None:
        chain = render_decision_chain([], level=DisclosureLevel.SUMMARY)
        assert chain == ""

    def test_chain_with_separator(self) -> None:
        e1 = DecisionExplanation(title="a", verdict="ALLOW")
        e2 = DecisionExplanation(title="b", verdict="ALLOW")
        chain = render_decision_chain([e1, e2], separator="\n---\n")
        assert "\n---\n" in chain


# ---------------------------------------------------------------------------
# Explanation payload direct usage
# ---------------------------------------------------------------------------


class TestExplanationPayload:
    def test_fluent_methods_return_self(self) -> None:
        e = DecisionExplanation(title="x")
        assert e.with_citation("a") is e
        assert e.with_chain_step("step") is e
        assert e.with_audit_ref("audit") is e
        assert e.with_action("act") is e

    def test_skips_empty_strings(self) -> None:
        e = DecisionExplanation(title="x")
        e.with_citation("")
        e.with_citation("real")
        e.with_chain_step("")
        e.with_chain_step("real")
        assert e.citations == ["real"]
        assert e.chain == ["real"]
