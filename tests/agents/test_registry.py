"""Tests for agents/registry.py - Agent registration and learning registry.

Covers:
- AGENT_NAMES constant
- get_runner function
- get_fallback_agents function
- resolve_agent function
- list_agent_names function
- list_droid_names function
- LearningCandidate class
- LearningRegistry class

Traces to: WL-034, WP-14001
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import directly from registry module to avoid litellm import issue through __init__.py
from thegent.agents.registry import (
    _AGENT_ALIASES,
    AGENT_LABELS,
    AGENT_NAMES,
    LearningCandidate,
    LearningRegistry,
    get_fallback_agents,
    get_runner,
    list_agent_names,
    list_droid_names,
    resolve_agent,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestAgentNames:
    """Tests for AGENT_NAMES constant."""

    def test_agent_names_is_list(self) -> None:
        """AGENT_NAMES is a list."""
        assert isinstance(AGENT_NAMES, list)

    def test_agent_names_contains_common_agents(self) -> None:
        """AGENT_NAMES contains expected agent names."""
        assert "gemini" in AGENT_NAMES
        assert "codex" in AGENT_NAMES
        assert "claude" in AGENT_NAMES
        assert "cursor-agent" in AGENT_NAMES

    def test_agent_names_all_strings(self) -> None:
        """All entries in AGENT_NAMES are strings."""
        for name in AGENT_NAMES:
            assert isinstance(name, str)

    def test_agent_names_no_duplicates(self) -> None:
        """AGENT_NAMES has no duplicate entries."""
        assert len(AGENT_NAMES) == len(set(AGENT_NAMES))


class TestAgentLabels:
    """Tests for AGENT_LABELS constant."""

    def test_agent_labels_is_dict(self) -> None:
        """AGENT_LABELS is a dict."""
        assert isinstance(AGENT_LABELS, dict)

    def test_agent_labels_cursor_agent(self) -> None:
        """cursor-agent maps to cursor label."""
        assert AGENT_LABELS.get("cursor-agent") == "cursor"

    def test_agent_labels_cursor_api(self) -> None:
        """cursor-api maps to cursor-api label."""
        assert AGENT_LABELS.get("cursor-api") == "cursor-api"


class TestAgentAliases:
    """Tests for _AGENT_ALIASES constant."""

    def test_aliases_is_dict(self) -> None:
        """_AGENT_ALIASES is a dict."""
        assert isinstance(_AGENT_ALIASES, dict)

    def test_alias_cursor_to_cursor_agent(self) -> None:
        """cursor alias maps to cursor-agent."""
        assert _AGENT_ALIASES.get("cursor") == "cursor-agent"

    def test_alias_oc_to_opencode(self) -> None:
        """oc alias maps to opencode."""
        assert _AGENT_ALIASES.get("oc") == "opencode"

    def test_alias_free_to_copilot(self) -> None:
        """free alias maps to copilot."""
        assert _AGENT_ALIASES.get("free") == "copilot"

    def test_aliases_all_string_values(self) -> None:
        """All alias values are strings."""
        for alias, canonical in _AGENT_ALIASES.items():
            assert isinstance(alias, str)
            assert isinstance(canonical, str)


# ---------------------------------------------------------------------------
# resolve_agent tests
# ---------------------------------------------------------------------------


class TestResolveAgent:
    """Tests for resolve_agent function."""

    def test_resolve_agent_returns_none_for_none_input(self) -> None:
        """resolve_agent returns None for None input."""
        assert resolve_agent(None) is None

    def test_resolve_agent_returns_canonical_name(self) -> None:
        """resolve_agent returns canonical name for aliases."""
        assert resolve_agent("cursor") == "cursor-agent"
        assert resolve_agent("oc") == "opencode"
        assert resolve_agent("free") == "copilot"

    def test_resolve_agent_returns_same_if_no_alias(self) -> None:
        """resolve_agent returns input if no alias exists."""
        assert resolve_agent("gemini") == "gemini"
        assert resolve_agent("claude") == "claude"

    def test_resolve_agent_handles_unknown_names(self) -> None:
        """resolve_agent returns input for unknown names."""
        assert resolve_agent("unknown-agent") == "unknown-agent"


# ---------------------------------------------------------------------------
# list_agent_names tests
# ---------------------------------------------------------------------------


class TestListAgentNames:
    """Tests for list_agent_names function."""

    def test_list_agent_names_returns_list(self) -> None:
        """list_agent_names returns a list."""
        result = list_agent_names()
        assert isinstance(result, list)

    def test_list_agent_names_matches_agent_names(self) -> None:
        """list_agent_names returns a copy of AGENT_NAMES."""
        result = list_agent_names()
        assert result == AGENT_NAMES

    def test_list_agent_names_modification_does_not_affect_original(self) -> None:
        """Modifying list_agent_names result doesn't affect AGENT_NAMES."""
        result = list_agent_names()
        original_len = len(AGENT_NAMES)
        result.append("new-agent")
        assert len(AGENT_NAMES) == original_len


# ---------------------------------------------------------------------------
# list_droid_names tests
# ---------------------------------------------------------------------------


class TestListDroidNames:
    """Tests for list_droid_names function."""

    def test_list_droid_names_returns_list(self, tmp_path: Path) -> None:
        """list_droid_names returns a list."""
        result = list_droid_names(tmp_path)
        assert isinstance(result, list)

    def test_list_droid_names_empty_for_nonexistent_dir(self, tmp_path: Path) -> None:
        """list_droid_names returns empty list for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        result = list_droid_names(nonexistent)
        assert result == []

    def test_list_droid_names_finds_md_files(self, tmp_path: Path) -> None:
        """list_droid_names finds .md files in directory."""
        (tmp_path / "droid1.md").write_text("content")
        (tmp_path / "droid2.md").write_text("content")
        result = list_droid_names(tmp_path)
        assert "droid1" in result
        assert "droid2" in result

    def test_list_droid_names_excludes_non_md_files(self, tmp_path: Path) -> None:
        """list_droid_names excludes non-.md files."""
        (tmp_path / "droid1.md").write_text("content")
        (tmp_path / "droid2.txt").write_text("content")
        result = list_droid_names(tmp_path)
        assert "droid1" in result
        assert "droid2" not in result

    def test_list_droid_names_expands_tilde(self) -> None:
        """list_droid_names expands ~ in path."""
        result = list_droid_names(Path("~/nonexistent_droid_dir"))
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# get_runner tests
# ---------------------------------------------------------------------------


class TestGetRunner:
    """Tests for get_runner function."""

    def test_get_runner_returns_none_for_unknown_agent(self) -> None:
        """get_runner returns None for completely unknown agents."""
        with patch("thegent.agents.teammate_runner.TeammateRunner") as mock_teammate:
            mock_teammate.side_effect = ValueError("no teammate")
            result = get_runner("completely-unknown-agent-xyz")
            assert result is None

    def test_get_runner_resolves_alias(self) -> None:
        """get_runner resolves aliases before creating runner."""
        with patch("thegent.agents.registry.DirectAgentRunner") as mock_direct:
            mock_direct.return_value = MagicMock()
            get_runner("cursor")  # alias for cursor-agent
            # Check that DirectAgentRunner was called with cursor-agent
            mock_direct.assert_called_once()

    def test_get_runner_for_direct_agent(self) -> None:
        """get_runner creates DirectAgentRunner for direct agents."""
        with patch("thegent.agents.registry.DirectAgentRunner") as mock_direct:
            mock_runner = MagicMock()
            mock_direct.return_value = mock_runner
            result = get_runner("cursor-agent")
            assert result is mock_runner

    def test_get_runner_for_opencode(self) -> None:
        """get_runner creates DirectAgentRunner for opencode."""
        with patch("thegent.agents.registry.DirectAgentRunner") as mock_direct:
            mock_runner = MagicMock()
            mock_direct.return_value = mock_runner
            result = get_runner("opencode")
            assert result is mock_runner

    def test_get_runner_for_proxy_agent(self) -> None:
        """get_runner creates CodexProxyRunner for proxy agents."""
        with patch("thegent.agents.registry.CodexProxyRunner") as mock_proxy:
            mock_runner = MagicMock()
            mock_proxy.return_value = mock_runner
            result = get_runner("gemini")
            assert result is mock_runner

    def test_get_runner_for_codex(self) -> None:
        """get_runner creates CodexProxyRunner for codex."""
        with patch("thegent.agents.registry.CodexProxyRunner") as mock_proxy:
            mock_runner = MagicMock()
            mock_proxy.return_value = mock_runner
            result = get_runner("codex")
            assert result is mock_runner

    def test_get_runner_for_cursor_api(self) -> None:
        """get_runner creates CursorApiRunner for cursor-api."""
        with patch("thegent.agents.registry.CursorApiRunner") as mock_cursor:
            mock_runner = MagicMock()
            mock_cursor.return_value = mock_runner
            result = get_runner("cursor-api")
            assert result is mock_runner

    def test_get_runner_for_summarizer(self) -> None:
        """get_runner creates CodexProxyRunner for summarizer."""
        with patch("thegent.agents.registry.CodexProxyRunner") as mock_proxy:
            mock_runner = MagicMock()
            mock_proxy.return_value = mock_runner
            result = get_runner("summarizer")
            assert result is mock_runner


# ---------------------------------------------------------------------------
# get_fallback_agents tests
# ---------------------------------------------------------------------------


class TestGetFallbackAgents:
    """Tests for get_fallback_agents function."""

    def test_get_fallback_agents_returns_list(self) -> None:
        """get_fallback_agents returns a list."""
        result = get_fallback_agents("gemini")
        assert isinstance(result, list)

    def test_get_fallback_agents_excludes_current_agent(self) -> None:
        """get_fallback_agents excludes the current agent from results."""
        result = get_fallback_agents("gemini")
        assert "gemini" not in result

    def test_get_fallback_agents_returns_fallback_chain(self) -> None:
        """get_fallback_agents returns agents from fallback chain."""
        result = get_fallback_agents("glm")
        # Should have fallbacks from the chain
        assert len(result) > 0

    def test_get_fallback_agents_empty_for_unknown(self) -> None:
        """get_fallback_agents returns empty list for unknown agents."""
        result = get_fallback_agents("completely-unknown-agent-xyz")
        assert result == []

    def test_get_fallback_agents_resolves_alias(self) -> None:
        """get_fallback_agents resolves aliases."""
        # cursor is alias for cursor-agent
        result = get_fallback_agents("cursor")
        # Should not include cursor-agent (resolved name)
        assert "cursor-agent" not in result


# ---------------------------------------------------------------------------
# LearningCandidate tests
# ---------------------------------------------------------------------------


class TestLearningCandidate:
    """Tests for LearningCandidate class."""

    def test_learning_candidate_init(self) -> None:
        """LearningCandidate initializes with model_id and baseline_id."""
        candidate = LearningCandidate(model_id="canary-v1", baseline_id="baseline-v1")
        assert candidate.model_id == "canary-v1"
        assert candidate.baseline_id == "baseline-v1"

    def test_learning_candidate_default_trust_score(self) -> None:
        """LearningCandidate has default trust_score of 0.0."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        assert candidate.trust_score == 0.0

    def test_learning_candidate_default_calibration(self) -> None:
        """LearningCandidate has default calibration of 0.0."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        assert candidate.calibration == 0.0

    def test_learning_candidate_default_metrics_empty(self) -> None:
        """LearningCandidate has empty metrics dict."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        assert candidate.metrics == {}

    def test_add_metric_creates_new_list(self) -> None:
        """add_metric creates a new list for new metric name."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        candidate.add_metric("latency", 1.5)
        assert "latency" in candidate.metrics
        assert candidate.metrics["latency"] == [1.5]

    def test_add_metric_appends_to_existing_list(self) -> None:
        """add_metric appends to existing metric list."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        candidate.add_metric("latency", 1.0)
        candidate.add_metric("latency", 2.0)
        assert candidate.metrics["latency"] == [1.0, 2.0]

    def test_add_metric_multiple_metrics(self) -> None:
        """add_metric handles multiple different metrics."""
        candidate = LearningCandidate(model_id="test", baseline_id="base")
        candidate.add_metric("latency", 1.0)
        candidate.add_metric("accuracy", 0.95)
        assert candidate.metrics["latency"] == [1.0]
        assert candidate.metrics["accuracy"] == [0.95]


# ---------------------------------------------------------------------------
# LearningRegistry tests
# ---------------------------------------------------------------------------


class TestLearningRegistry:
    """Tests for LearningRegistry class."""

    def test_learning_registry_init(self) -> None:
        """LearningRegistry initializes with empty canaries."""
        registry = LearningRegistry()
        assert registry.canaries == {}

    def test_learning_registry_default_active_model(self) -> None:
        """LearningRegistry has default active_model of baseline-v1."""
        registry = LearningRegistry()
        assert registry.active_model == "baseline-v1"

    def test_register_canary(self) -> None:
        """register_canary adds a new candidate to canaries."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        assert "canary-v1" in registry.canaries
        assert isinstance(registry.canaries["canary-v1"], LearningCandidate)
        assert registry.canaries["canary-v1"].baseline_id == "baseline-v1"

    def test_record_metric(self) -> None:
        """record_metric records metric for a model."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        registry.record_metric("canary-v1", "latency", 1.5)
        assert registry.canaries["canary-v1"].metrics["latency"] == [1.5]

    def test_record_metric_unknown_model_does_nothing(self) -> None:
        """record_metric for unknown model does nothing."""
        registry = LearningRegistry()
        registry.record_metric("unknown", "latency", 1.5)
        assert "unknown" not in registry.canaries

    def test_should_rollback_returns_false_for_unknown(self) -> None:
        """should_rollback returns False for unknown canary."""
        registry = LearningRegistry()
        assert registry.should_rollback("unknown") is False

    def test_should_rollback_returns_false_for_normal_latency(self) -> None:
        """should_rollback returns False when latency is acceptable."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        registry.record_metric("canary-v1", "latency", 1.0)
        assert registry.should_rollback("canary-v1") is False

    def test_should_rollback_returns_true_for_high_latency(self) -> None:
        """should_rollback returns True when any latency > 2s."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        registry.record_metric("canary-v1", "latency", 2.5)
        assert registry.should_rollback("canary-v1") is True

    def test_should_rollback_updates_active_model(self) -> None:
        """should_rollback updates active_model to baseline on rollback."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        registry.active_model = "canary-v1"
        registry.record_metric("canary-v1", "latency", 2.5)
        registry.should_rollback("canary-v1")
        assert registry.active_model == "baseline-v1"

    def test_get_active_model(self) -> None:
        """get_active_model returns the current active model."""
        registry = LearningRegistry()
        assert registry.get_active_model() == "baseline-v1"
        registry.active_model = "new-model"
        assert registry.get_active_model() == "new-model"

    def test_promote_returns_false_with_approval_required(self) -> None:
        """promote returns False when approval is required."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        result = registry.promote("canary-v1", require_approval=True)
        assert result is False

    def test_promote_returns_false_for_unknown_canary(self) -> None:
        """promote returns False for unknown canary."""
        registry = LearningRegistry()
        result = registry.promote("unknown", require_approval=False)
        assert result is False

    def test_promote_updates_active_model(self) -> None:
        """promote updates active_model when successful."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        result = registry.promote("canary-v1", require_approval=False)
        assert result is True
        assert registry.active_model == "canary-v1"

    def test_record_feedback_success(self) -> None:
        """record_feedback increases trust score on success."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        initial_trust = registry.canaries["canary-v1"].trust_score
        registry.record_feedback("canary-v1", success=True, quality_score=0.9)
        assert registry.canaries["canary-v1"].trust_score == initial_trust + 0.1

    def test_record_feedback_failure(self) -> None:
        """record_feedback decreases trust score on failure."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        initial_trust = registry.canaries["canary-v1"].trust_score
        registry.record_feedback("canary-v1", success=False, quality_score=0.5)
        assert registry.canaries["canary-v1"].trust_score == initial_trust - 0.2

    def test_record_feedback_updates_calibration(self) -> None:
        """record_feedback updates calibration score."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        registry.record_feedback("canary-v1", success=True, quality_score=0.8)
        # Calibration: (0 + 0.8) / 2 = 0.4
        assert registry.canaries["canary-v1"].calibration == 0.4
        registry.record_feedback("canary-v1", success=True, quality_score=0.9)
        # Calibration: (0.4 + 0.9) / 2 = 0.65
        assert registry.canaries["canary-v1"].calibration == 0.65

    def test_record_feedback_unknown_model_does_nothing(self) -> None:
        """record_feedback for unknown model does nothing."""
        registry = LearningRegistry()
        registry.record_feedback("unknown", success=True, quality_score=0.9)
        assert "unknown" not in registry.canaries

    def test_get_candidate(self) -> None:
        """get_candidate returns the candidate for a model."""
        registry = LearningRegistry()
        registry.register_canary("canary-v1", "baseline-v1")
        candidate = registry.get_candidate("canary-v1")
        assert candidate is not None
        assert candidate.model_id == "canary-v1"

    def test_get_candidate_returns_none_for_unknown(self) -> None:
        """get_candidate returns None for unknown model."""
        registry = LearningRegistry()
        assert registry.get_candidate("unknown") is None


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    """Integration tests for registry functions."""

    def test_full_learning_cycle(self) -> None:
        """Test full canary deployment and promotion cycle."""
        registry = LearningRegistry()

        # Register canary
        registry.register_canary("canary-v1", "baseline-v1")

        # Record some metrics
        registry.record_metric("canary-v1", "latency", 0.5)
        registry.record_metric("canary-v1", "latency", 0.6)
        registry.record_feedback("canary-v1", success=True, quality_score=0.9)

        # Check no rollback needed
        assert registry.should_rollback("canary-v1") is False

        # Promote (without approval requirement for test)
        result = registry.promote("canary-v1", require_approval=False)
        assert result is True
        assert registry.get_active_model() == "canary-v1"

    def test_rollback_cycle(self) -> None:
        """Test rollback when latency exceeds threshold."""
        registry = LearningRegistry()

        # Register canary and set as active
        registry.register_canary("canary-v1", "baseline-v1")
        registry.active_model = "canary-v1"

        # Record high latency
        registry.record_metric("canary-v1", "latency", 3.0)

        # Should trigger rollback
        assert registry.should_rollback("canary-v1") is True
        assert registry.get_active_model() == "baseline-v1"
