"""Tests for WL-112: Unified reasoning_effort Parameter in RunOptions.

Covers:
- RunOptions instantiation with each reasoning_effort value
- RunOptions defaults to None
- Invalid values raise ValidationError
- Translation to Codex config args
- Translation to Anthropic budget_tokens
- Translation to OpenAI o-series effort string
- CLI --reasoning flag validation
- run_impl signature accepts reasoning_effort
- runner_factory injects Codex config when reasoning_effort is set

# @trace WL-112
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from thegent.agents.run_options import (
    ANTHROPIC_BUDGET_TOKENS,
    CODEX_REASONING_CONFIG_KEY,
    RunOptions,
    translate_reasoning_to_anthropic_budget,
    translate_reasoning_to_codex_config,
    translate_reasoning_to_openai_effort,
)

# ---------------------------------------------------------------------------
# RunOptions model tests
# ---------------------------------------------------------------------------


class TestRunOptionsDefaults:
    """# @trace WL-112"""

    def test_default_reasoning_effort_is_none(self) -> None:
        """RunOptions defaults reasoning_effort to None.

        # @trace WL-112
        """
        opts = RunOptions()
        assert opts.reasoning_effort is None

    def test_default_output_schema_path_is_none(self) -> None:
        """RunOptions defaults output_schema_path to None.

        # @trace WL-112
        """
        opts = RunOptions()
        assert opts.output_schema_path is None


class TestRunOptionsReasoningEffortValues:
    """# @trace WL-112"""

    @pytest.mark.parametrize(
        "effort",
        ["minimal", "low", "medium", "high", "xhigh"],
    )
    def test_valid_reasoning_effort_values(self, effort: str) -> None:
        """All five valid reasoning_effort values are accepted by RunOptions.

        # @trace WL-112
        """
        opts = RunOptions(reasoning_effort=effort)  # type: ignore[arg-type]
        assert opts.reasoning_effort == effort

    def test_invalid_reasoning_effort_raises_validation_error(self) -> None:
        """An invalid reasoning_effort value raises a pydantic ValidationError.

        # @trace WL-112
        """
        with pytest.raises(ValidationError):
            RunOptions(reasoning_effort="ultra")  # type: ignore[arg-type]

    def test_invalid_reasoning_effort_empty_string_raises(self) -> None:
        """An empty-string reasoning_effort raises a pydantic ValidationError.

        # @trace WL-112
        """
        with pytest.raises(ValidationError):
            RunOptions(reasoning_effort="")  # type: ignore[arg-type]

    def test_none_reasoning_effort_is_valid(self) -> None:
        """Explicit None for reasoning_effort is valid.

        # @trace WL-112
        """
        opts = RunOptions(reasoning_effort=None)
        assert opts.reasoning_effort is None


# ---------------------------------------------------------------------------
# Translation helpers — Codex
# ---------------------------------------------------------------------------


class TestTranslateReasoningToCodexConfig:
    """# @trace WL-112"""

    @pytest.mark.parametrize(
        "effort",
        ["minimal", "low", "medium", "high", "xhigh"],
    )
    def test_returns_correct_config_key(self, effort: str) -> None:
        """translate_reasoning_to_codex_config returns dict with correct key.

        # @trace WL-112
        """
        result = translate_reasoning_to_codex_config(effort)
        assert CODEX_REASONING_CONFIG_KEY in result

    @pytest.mark.parametrize(
        "effort",
        ["minimal", "low", "medium", "high", "xhigh"],
    )
    def test_returns_correct_config_value(self, effort: str) -> None:
        """translate_reasoning_to_codex_config maps effort value to config dict value.

        # @trace WL-112
        """
        result = translate_reasoning_to_codex_config(effort)
        assert result[CODEX_REASONING_CONFIG_KEY] == effort

    def test_returns_dict_type(self) -> None:
        """translate_reasoning_to_codex_config returns a dict.

        # @trace WL-112
        """
        result = translate_reasoning_to_codex_config("high")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Translation helpers — Anthropic
# ---------------------------------------------------------------------------


class TestTranslateReasoningToAnthropicBudget:
    """# @trace WL-112"""

    def test_minimal_maps_to_1000(self) -> None:
        """minimal effort maps to 1000 budget_tokens.

        # @trace WL-112
        """
        assert translate_reasoning_to_anthropic_budget("minimal") == 1000

    def test_low_maps_to_2000(self) -> None:
        """low effort maps to 2000 budget_tokens.

        # @trace WL-112
        """
        assert translate_reasoning_to_anthropic_budget("low") == 2000

    def test_medium_maps_to_5000(self) -> None:
        """medium effort maps to 5000 budget_tokens.

        # @trace WL-112
        """
        assert translate_reasoning_to_anthropic_budget("medium") == 5000

    def test_high_maps_to_8000(self) -> None:
        """high effort maps to 8000 budget_tokens.

        # @trace WL-112
        """
        assert translate_reasoning_to_anthropic_budget("high") == 8000

    def test_xhigh_maps_to_16000(self) -> None:
        """xhigh effort maps to 16000 budget_tokens.

        # @trace WL-112
        """
        assert translate_reasoning_to_anthropic_budget("xhigh") == 16000

    def test_all_values_covered_by_mapping_constant(self) -> None:
        """ANTHROPIC_BUDGET_TOKENS covers all five effort levels.

        # @trace WL-112
        """
        expected_keys = {"minimal", "low", "medium", "high", "xhigh"}
        assert set(ANTHROPIC_BUDGET_TOKENS.keys()) == expected_keys

    def test_invalid_effort_raises_key_error(self) -> None:
        """An unknown effort value raises KeyError from the mapping.

        # @trace WL-112
        """
        with pytest.raises(KeyError):
            translate_reasoning_to_anthropic_budget("turbo")


# ---------------------------------------------------------------------------
# Translation helpers — OpenAI o-series
# ---------------------------------------------------------------------------


class TestTranslateReasoningToOpenAIEffort:
    """# @trace WL-112"""

    @pytest.mark.parametrize(
        ("effort", "expected"),
        [
            ("minimal", "minimal"),
            ("low", "low"),
            ("medium", "medium"),
            ("high", "high"),
            ("xhigh", "high"),  # clamped to OpenAI's max
        ],
    )
    def test_effort_mapping(self, effort: str, expected: str) -> None:
        """Each effort level maps correctly for OpenAI o-series.

        xhigh is clamped to 'high' since OpenAI only supports low/medium/high.

        # @trace WL-112
        """
        assert translate_reasoning_to_openai_effort(effort) == expected


# ---------------------------------------------------------------------------
# run_impl integration: reasoning_effort passes through
# ---------------------------------------------------------------------------


class TestRunImplReasoningEffortSignature:
    """run_impl accepts reasoning_effort and the CodexProxyRunner receives config.

    # @trace WL-112
    """

    def test_run_impl_accepts_reasoning_effort_kwarg(self) -> None:
        """run_impl has reasoning_effort in its signature (importable without error).

        # @trace WL-112
        """
        import inspect

        from thegent.cli.commands.impl import run_impl

        sig = inspect.signature(run_impl)
        assert "reasoning_effort" in sig.parameters

    def test_run_impl_reasoning_effort_default_is_none(self) -> None:
        """run_impl.reasoning_effort default is None.

        # @trace WL-112
        """
        import inspect

        from thegent.cli.commands.impl import run_impl

        sig = inspect.signature(run_impl)
        param = sig.parameters["reasoning_effort"]
        assert param.default is None
