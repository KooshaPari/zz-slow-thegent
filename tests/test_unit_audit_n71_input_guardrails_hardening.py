"""Hardening invariants for ``governance.input_guardrails`` — AUDIT-N+71.

15 invariants FR-GOV-IG-001 .. FR-GOV-IG-015 covering
GuardrailResult, InputGuardrails (init, check, _check_pattern),
guardrails_from_settings, guardrails_from_env.

Source: src/thegent/governance/input_guardrails.py

@trace AUDIT-N+71  FR-GOV-IG-001..015
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.governance.input_guardrails import (
    GuardrailResult,
    InputGuardrails,
    guardrails_from_env,
    guardrails_from_settings,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-IG-001: GuardrailResult fields and defaults
# ---------------------------------------------------------------------------


class TestFRGOVIG001GuardrailResultFieldsDefaults:
    def test_passed_required(self) -> None:
        r = GuardrailResult(passed=True)
        assert r.passed is True
        assert r.rail_id == ""
        assert r.reason == ""
        assert r.remediation == ""

    def test_failed_with_details(self) -> None:
        r = GuardrailResult(
            passed=False,
            rail_id="prompt_length",
            reason="too long",
            remediation="shorten",
        )
        assert r.passed is False
        assert r.rail_id == "prompt_length"
        assert r.reason == "too long"
        assert r.remediation == "shorten"


# ---------------------------------------------------------------------------
# FR-GOV-IG-002: InputGuardrails init defaults
# ---------------------------------------------------------------------------


class TestFRGOVIG002InputGuardrailsInitDefaults:
    def test_defaults(self) -> None:
        ig = InputGuardrails()
        assert ig.prompt_max_chars == 65536
        assert ig.prompt_blocklist_patterns == []
        assert ig.agent_allowlist == []
        assert ig.cwd_allowed_prefixes == []
        assert ig.model_allowlist == []


# ---------------------------------------------------------------------------
# FR-GOV-IG-003: check() prompt_length rejection
# ---------------------------------------------------------------------------


class TestFRGOVIG003CheckPromptLengthRejection:
    def test_rejects_oversized_prompt(self) -> None:
        ig = InputGuardrails(prompt_max_chars=100)
        result = ig.check(prompt="x" * 101)
        assert result.passed is False
        assert result.rail_id == "prompt_length"

    def test_accepts_exact_max_chars(self) -> None:
        ig = InputGuardrails(prompt_max_chars=100)
        result = ig.check(prompt="x" * 100)
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-004: prompt_blocklist pattern match
# ---------------------------------------------------------------------------


class TestFRGOVIG004PromptBlocklistPatternMatch:
    def test_matches_blocklist_pattern(self) -> None:
        ig = InputGuardrails(prompt_blocklist_patterns=[r"forbidden"])
        result = ig.check(prompt="this contains forbidden content")
        assert result.passed is False
        assert result.rail_id == "prompt_blocklist"

    def test_no_match_when_clean(self) -> None:
        ig = InputGuardrails(prompt_blocklist_patterns=[r"forbidden"])
        result = ig.check(prompt="this is clean")
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-005: agent_allowlist enforcement
# ---------------------------------------------------------------------------


class TestFRGOVIG005AgentAllowlistEnforcement:
    def test_rejects_unlisted_agent(self) -> None:
        ig = InputGuardrails(agent_allowlist=["agent-a", "agent-b"])
        result = ig.check(agent="agent-c")
        assert result.passed is False
        assert result.rail_id == "agent_allowlist"

    def test_accepts_listed_agent(self) -> None:
        ig = InputGuardrails(agent_allowlist=["agent-a", "agent-b"])
        result = ig.check(agent="agent-a")
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-006: cwd_restriction prefix check
# ---------------------------------------------------------------------------


class TestFRGOVIG006CwdRestrictionPrefixCheck:
    def test_rejects_cwd_outside_prefix(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        ig = InputGuardrails(cwd_allowed_prefixes=[str(allowed)])
        result = ig.check(cwd=str(outside))
        assert result.passed is False
        assert result.rail_id == "cwd_restriction"

    def test_accepts_cwd_under_prefix(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        ig = InputGuardrails(cwd_allowed_prefixes=[str(allowed)])
        result = ig.check(cwd=str(allowed))
        assert result.passed is True

    def test_rejects_non_string_cwd(self) -> None:
        ig = InputGuardrails(cwd_allowed_prefixes=["/safe"])
        result = ig.check(cwd=123)  # type: ignore[arg-type]
        assert result.passed is False
        assert result.rail_id == "cwd_restriction"
        assert "not str or Path" in result.reason


# ---------------------------------------------------------------------------
# FR-GOV-IG-007: model_allowlist enforcement
# ---------------------------------------------------------------------------


class TestFRGOVIG007ModelAllowlistEnforcement:
    def test_rejects_unlisted_model(self) -> None:
        ig = InputGuardrails(model_allowlist=["gpt-4", "gpt-3.5"])
        result = ig.check(model="claude-2")
        assert result.passed is False
        assert result.rail_id == "model_allowlist"

    def test_accepts_listed_model(self) -> None:
        ig = InputGuardrails(model_allowlist=["gpt-4", "gpt-3.5"])
        result = ig.check(model="gpt-4")
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-008: check() passes all rails
# ---------------------------------------------------------------------------


class TestFRGOVIG008CheckPassesAllRails:
    def test_passes_with_all_constraints(self, tmp_path: Path) -> None:
        allowed = tmp_path / "workspace"
        allowed.mkdir()
        ig = InputGuardrails(
            prompt_max_chars=1000,
            prompt_blocklist_patterns=[r"evil"],
            agent_allowlist=["agent-a"],
            cwd_allowed_prefixes=[str(allowed)],
            model_allowlist=["gpt-4"],
        )
        result = ig.check(
            prompt="hello world",
            agent="agent-a",
            model="gpt-4",
            cwd=str(allowed),
        )
        assert result.passed is True
        assert result.rail_id == ""


# ---------------------------------------------------------------------------
# FR-GOV-IG-009: _check_pattern valid regex
# ---------------------------------------------------------------------------


class TestFRGOVIG009CheckPatternValidRegex:
    def test_returns_result_on_match(self) -> None:
        ig = InputGuardrails()
        r = ig._check_pattern(r"bad", "this is bad stuff")
        assert r is not None
        assert r.passed is False
        assert r.rail_id == "prompt_blocklist"

    def test_returns_none_on_no_match(self) -> None:
        ig = InputGuardrails()
        r = ig._check_pattern(r"bad", "this is clean")
        assert r is None


# ---------------------------------------------------------------------------
# FR-GOV-IG-010: _check_pattern invalid regex (re.error)
# ---------------------------------------------------------------------------


class TestFRGOVIG010CheckPatternInvalidRegex:
    def test_invalid_regex_returns_none(self) -> None:
        ig = InputGuardrails()
        # Unclosed bracket is an invalid regex
        r = ig._check_pattern("[invalid", "prompt text")
        assert r is None

    def test_invalid_regex_does_not_raise(self) -> None:
        ig = InputGuardrails()
        # Should not raise re.error
        ig._check_pattern("(unclosed", "prompt text")


# ---------------------------------------------------------------------------
# FR-GOV-IG-011: guardrails_from_settings construction
# ---------------------------------------------------------------------------


class TestFRGOVIG011GuardrailsFromSettingsConstruction:
    def test_builds_from_settings(self) -> None:
        fake = _FakeSettings(
            prompt_max_chars=9999,
            prompt_blocklist_patterns="pat1, pat2",
            agent_allowlist="a1, a2",
            cwd_allowed_prefixes="/tmp",
        )
        ig = guardrails_from_settings(fake)
        assert ig.prompt_max_chars == 9999
        assert ig.prompt_blocklist_patterns == ["pat1", "pat2"]
        assert ig.agent_allowlist == ["a1", "a2"]
        assert ig.cwd_allowed_prefixes == ["/tmp"]

    def test_empty_strings_produce_empty_lists(self) -> None:
        fake = _FakeSettings(
            prompt_max_chars=100,
            prompt_blocklist_patterns="",
            agent_allowlist="",
            cwd_allowed_prefixes="",
        )
        ig = guardrails_from_settings(fake)
        assert ig.prompt_blocklist_patterns == []
        assert ig.agent_allowlist == []
        assert ig.cwd_allowed_prefixes == []


# ---------------------------------------------------------------------------
# FR-GOV-IG-012: guardrails_from_env deprecated alias
# ---------------------------------------------------------------------------


class TestFRGOVIG012GuardrailsFromEnvDeprecatedAlias:
    def test_returns_input_guardrails_instance(self) -> None:
        with patch(
            "thegent.governance.input_guardrails.guardrails_from_settings"
        ) as mock_gs:
            mock_gs.return_value = InputGuardrails()
            result = guardrails_from_env()
            mock_gs.assert_called_once()
            assert isinstance(result, InputGuardrails)


# ---------------------------------------------------------------------------
# FR-GOV-IG-013: empty allowlists = allow all
# ---------------------------------------------------------------------------


class TestFRGOVIG013EmptyAllowlistsAllowAll:
    def test_empty_agent_allowlist_allows_any(self) -> None:
        ig = InputGuardrails(agent_allowlist=[])
        result = ig.check(agent="any-agent")
        assert result.passed is True

    def test_empty_model_allowlist_allows_any(self) -> None:
        ig = InputGuardrails(model_allowlist=[])
        result = ig.check(model="any-model")
        assert result.passed is True

    def test_empty_cwd_prefixes_allows_any(self) -> None:
        ig = InputGuardrails(cwd_allowed_prefixes=[])
        result = ig.check(cwd="/any/path")
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-014: empty prompt = passes
# ---------------------------------------------------------------------------


class TestFRGOVIG014EmptyPromptPasses:
    def test_empty_string_passes(self) -> None:
        ig = InputGuardrails(prompt_max_chars=10)
        result = ig.check(prompt="")
        assert result.passed is True

    def test_none_prompt_passes(self) -> None:
        ig = InputGuardrails(prompt_max_chars=10)
        result = ig.check(prompt=None)  # type: ignore[arg-type]
        assert result.passed is True


# ---------------------------------------------------------------------------
# FR-GOV-IG-015: boundary — prompt exactly at max_chars
# ---------------------------------------------------------------------------


class TestFRGOVIG015BoundaryPromptExactlyAtMaxChars:
    def test_exactly_at_max_passes(self) -> None:
        ig = InputGuardrails(prompt_max_chars=50)
        result = ig.check(prompt="a" * 50)
        assert result.passed is True

    def test_one_over_fails(self) -> None:
        ig = InputGuardrails(prompt_max_chars=50)
        result = ig.check(prompt="a" * 51)
        assert result.passed is False
        assert result.rail_id == "prompt_length"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


class _FakeSettings:
    """Minimal stand-in for ThegentSettings."""

    def __init__(
        self,
        prompt_max_chars: int = 65536,
        prompt_blocklist_patterns: str = "",
        agent_allowlist: str = "",
        cwd_allowed_prefixes: str = "",
    ) -> None:
        self.prompt_max_chars = prompt_max_chars
        self.prompt_blocklist_patterns = prompt_blocklist_patterns
        self.agent_allowlist = agent_allowlist
        self.cwd_allowed_prefixes = cwd_allowed_prefixes
