"""Tests for agents/base.py - AgentRunner, RunResult.

Covers:
- RunResult dataclass fields and defaults
- AgentRunner initialization and abstract methods
- activate_skill and get_skill_prompt_suffix
- _ensure_activated_skills
- _process_output_deferrals

Traces to: WL-038, WL-080, WL-101
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import directly from base module to avoid litellm import issue through __init__.py
from thegent.agents.base import AgentRunner, RunResult

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# RunResult dataclass tests
# ---------------------------------------------------------------------------


class TestRunResult:
    """Tests for RunResult dataclass."""

    def test_run_result_required_fields(self) -> None:
        """RunResult requires exit_code, stdout, stderr."""
        result = RunResult(exit_code=0, stdout="output", stderr="errors")
        assert result.exit_code == 0
        assert result.stdout == "output"
        assert result.stderr == "errors"

    def test_run_result_default_timed_out_false(self) -> None:
        """timed_out defaults to False."""
        result = RunResult(exit_code=0, stdout="", stderr="")
        assert result.timed_out is False

    def test_run_result_default_optional_fields_none(self) -> None:
        """Optional context fields default to None."""
        result = RunResult(exit_code=0, stdout="", stderr="")
        assert result.context_tokens_used is None
        assert result.context_window_max is None
        assert result.context_usage_ratio is None
        assert result.audio_transcript is None
        assert result.grounding_sources is None

    def test_run_result_all_fields_populated(self) -> None:
        """All fields can be populated."""
        result = RunResult(
            exit_code=1,
            stdout="out",
            stderr="err",
            timed_out=True,
            context_tokens_used=5000,
            context_window_max=128000,
            context_usage_ratio=0.039,
            audio_transcript="hello world",
            grounding_sources=["source1", "source2"],
        )
        assert result.exit_code == 1
        assert result.timed_out is True
        assert result.context_tokens_used == 5000
        assert result.context_window_max == 128000
        assert result.context_usage_ratio == 0.039
        assert result.audio_transcript == "hello world"
        assert result.grounding_sources == ["source1", "source2"]

    def test_run_result_is_mutable(self) -> None:
        """RunResult instances are mutable (not a frozen dataclass)."""
        result = RunResult(exit_code=0, stdout="", stderr="")
        result.exit_code = 1
        assert result.exit_code == 1

    def test_run_result_empty_strings(self) -> None:
        """RunResult accepts empty strings for stdout/stderr."""
        result = RunResult(exit_code=0, stdout="", stderr="")
        assert result.stdout == ""
        assert result.stderr == ""


# ---------------------------------------------------------------------------
# AgentRunner base class tests
# ---------------------------------------------------------------------------


class TestAgentRunner:
    """Tests for AgentRunner base class."""

    def test_agent_runner_init_creates_activated_skills_dict(self) -> None:
        """AgentRunner.__init__ creates an empty activated_skills dict."""
        runner = AgentRunner()
        assert runner.activated_skills == {}

    def test_agent_runner_sub_dispatcher_default_none(self) -> None:
        """sub_dispatcher class attribute defaults to None."""
        runner = AgentRunner()
        assert runner.sub_dispatcher is None

    def test_ensure_activated_skills_returns_dict(self) -> None:
        """_ensure_activated_skills returns the activated_skills dict."""
        runner = AgentRunner()
        skills = runner._ensure_activated_skills()
        assert isinstance(skills, dict)
        assert skills is runner.activated_skills

    def test_ensure_activated_skills_initializes_if_missing(self) -> None:
        """_ensure_activated_skills initializes dict if attribute is missing."""
        runner = AgentRunner()
        delattr(runner, "activated_skills")
        skills = runner._ensure_activated_skills()
        assert skills == {}
        assert runner.activated_skills == {}

    def test_ensure_activated_skills_handles_non_dict(self) -> None:
        """_ensure_activated_skills replaces non-dict with empty dict."""
        runner = AgentRunner()
        runner.activated_skills = "not a dict"  # type: ignore[assignment]
        skills = runner._ensure_activated_skills()
        assert skills == {}
        assert runner.activated_skills == {}

    def test_run_is_abstract(self) -> None:
        """AgentRunner.run() raises TypeError for base class."""
        runner = AgentRunner()
        with pytest.raises(TypeError, match="abstract"):
            runner.run("prompt", None, "mode", 60)

    def test_run_abstract_message_includes_class_name(self) -> None:
        """Abstract run error message includes the class name."""
        runner = AgentRunner()
        with pytest.raises(TypeError, match="AgentRunner"):
            runner.run("prompt", None, "mode", 60)

    def test_get_skill_prompt_suffix_empty_when_no_skills(self) -> None:
        """get_skill_prompt_suffix returns empty string when no skills activated."""
        runner = AgentRunner()
        assert runner.get_skill_prompt_suffix() == ""

    def test_get_skill_prompt_suffix_returns_formatted_string(self) -> None:
        """get_skill_prompt_suffix returns formatted skill instructions."""
        runner = AgentRunner()
        runner.activated_skills = {"test-skill": "Do something useful."}
        suffix = runner.get_skill_prompt_suffix()
        assert "# Activated Skills" in suffix
        assert "## test-skill" in suffix
        assert "Do something useful." in suffix

    def test_get_skill_prompt_suffix_multiple_skills(self) -> None:
        """get_skill_prompt_suffix includes all activated skills."""
        runner = AgentRunner()
        runner.activated_skills = {
            "skill-a": "Instruction A",
            "skill-b": "Instruction B",
        }
        suffix = runner.get_skill_prompt_suffix()
        assert "## skill-a" in suffix
        assert "## skill-b" in suffix
        assert "Instruction A" in suffix
        assert "Instruction B" in suffix

    def test_get_skill_prompt_suffix_starts_with_newlines(self) -> None:
        """get_skill_prompt_suffix starts with double newline for separation."""
        runner = AgentRunner()
        runner.activated_skills = {"skill": "content"}
        suffix = runner.get_skill_prompt_suffix()
        assert suffix.startswith("\n\n# Activated Skills")

    def test_activated_skills_is_mutable(self) -> None:
        """activated_skills dict can be modified."""
        runner = AgentRunner()
        runner.activated_skills["new-skill"] = "instructions"
        assert "new-skill" in runner.activated_skills
        assert runner.activated_skills["new-skill"] == "instructions"


class TestActivateSkill:
    """Tests for AgentRunner.activate_skill method."""

    def test_activate_skill_stores_content(self) -> None:
        """activate_skill stores skill content in activated_skills."""
        runner = AgentRunner()
        mock_manifest = MagicMock()
        mock_manifest.instructions = "Test skill instructions."

        with patch("thegent.skills.discovery.SkillDiscovery") as mock_discovery_cls:
            mock_discovery = MagicMock()
            mock_discovery.find.return_value = mock_manifest
            mock_discovery_cls.return_value = mock_discovery

            result = runner.activate_skill("test-skill")

        assert result == "Test skill instructions."
        assert runner.activated_skills["test-skill"] == "Test skill instructions."

    def test_activate_skill_raises_keyerror_when_not_found(self) -> None:
        """activate_skill raises KeyError when skill not found."""
        runner = AgentRunner()

        with patch("thegent.skills.discovery.SkillDiscovery") as mock_discovery_cls:
            mock_discovery = MagicMock()
            mock_discovery.find.side_effect = KeyError("skill not found")
            mock_discovery_cls.return_value = mock_discovery

            with pytest.raises(KeyError):
                runner.activate_skill("nonexistent-skill")

    def test_activate_skill_uses_skill_discovery(self) -> None:
        """activate_skill creates SkillDiscovery and calls find."""
        runner = AgentRunner()
        mock_manifest = MagicMock()
        mock_manifest.instructions = "content"

        with patch("thegent.skills.discovery.SkillDiscovery") as mock_discovery_cls:
            mock_discovery = MagicMock()
            mock_discovery.find.return_value = mock_manifest
            mock_discovery_cls.return_value = mock_discovery

            runner.activate_skill("my-skill")

            mock_discovery_cls.assert_called_once()
            mock_discovery.find.assert_called_once_with("my-skill")


class TestProcessOutputDeferrals:
    """Tests for AgentRunner._process_output_deferrals method."""

    def test_process_output_deferrals_returns_result_unchanged(self) -> None:
        """_process_output_deferrals returns the original result object."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout="output", stderr="")
        returned = runner._process_output_deferrals(result)
        assert returned is result

    def test_process_output_deferrals_empty_output(self) -> None:
        """_process_output_deferrals handles empty stdout/stderr."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout="", stderr="")
        returned = runner._process_output_deferrals(result)
        assert returned is result

    def test_process_output_deferrals_handles_none_output(self) -> None:
        """_process_output_deferrals handles None stdout/stderr."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout=None, stderr=None)  # type: ignore[arg-type]
        returned = runner._process_output_deferrals(result)
        assert returned is result

    def test_process_output_deferrals_with_cwd(self) -> None:
        """_process_output_deferrals accepts cwd parameter."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout="", stderr="")
        returned = runner._process_output_deferrals(result, cwd=Path("/tmp"))
        assert returned is result

    def test_process_output_deferrals_with_project(self) -> None:
        """_process_output_deferrals accepts project parameter."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout="", stderr="")
        returned = runner._process_output_deferrals(result, project="test-project")
        assert returned is result

    def test_process_output_deferrals_extracts_deferred_tasks(self) -> None:
        """_process_output_deferrals extracts $defer tasks from output."""
        runner = AgentRunner()
        result = RunResult(
            exit_code=0,
            stdout="Done.\n$defer follow-up task",
            stderr="",
        )

        with patch("thegent.orchestration.resilience.deferral.extract_deferred_tasks") as mock_extract:
            mock_extract.return_value = ["follow-up task"]
            with patch("thegent.orchestration.resilience.deferral.inject_deferred_tasks") as mock_inject:
                mock_inject.return_value = 1
                with patch("thegent.config.ThegentSettings"):
                    runner._process_output_deferrals(result, cwd=Path("/project"))

                mock_extract.assert_called_once()

    def test_process_output_deferrals_handles_exception_gracefully(self) -> None:
        """_process_output_deferrals returns result even when extraction fails."""
        runner = AgentRunner()
        result = RunResult(exit_code=0, stdout="output", stderr="")

        with patch(
            "thegent.orchestration.resilience.deferral.extract_deferred_tasks",
            side_effect=RuntimeError("fail"),
        ):
            returned = runner._process_output_deferrals(result)
            assert returned is result


# ---------------------------------------------------------------------------
# Concrete AgentRunner subclass for testing
# ---------------------------------------------------------------------------


class ConcreteRunner(AgentRunner):
    """Concrete implementation of AgentRunner for testing."""

    def run(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        *,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout=None,
        on_stderr=None,
        env: dict | None = None,
        image_paths: list[str] | None = None,
    ) -> RunResult:
        """Concrete run implementation."""
        return RunResult(exit_code=0, stdout=f"processed: {prompt}", stderr="")


class TestConcreteRunner:
    """Tests for concrete AgentRunner subclass."""

    def test_concrete_runner_implements_run(self) -> None:
        """Concrete subclass can implement run()."""
        runner = ConcreteRunner()
        result = runner.run("test prompt", None, "mode", 60)
        assert result.exit_code == 0
        assert "test prompt" in result.stdout

    def test_concrete_runner_inherits_activated_skills(self) -> None:
        """Concrete subclass inherits activated_skills functionality."""
        runner = ConcreteRunner()
        assert runner.activated_skills == {}
        runner.activated_skills["skill"] = "content"
        assert runner.activated_skills["skill"] == "content"

    def test_concrete_runner_get_skill_prompt_suffix(self) -> None:
        """Concrete subclass inherits get_skill_prompt_suffix."""
        runner = ConcreteRunner()
        runner.activated_skills = {"test": "instructions"}
        suffix = runner.get_skill_prompt_suffix()
        assert "## test" in suffix

    def test_concrete_runner_accepts_all_run_parameters(self) -> None:
        """Concrete run accepts all parameters from base signature."""
        runner = ConcreteRunner()
        result = runner.run(
            "prompt",
            Path("/tmp"),
            "mode",
            30,
            use_stream=False,
            live_output=True,
            on_stdout=lambda x: None,
            on_stderr=lambda x: None,
            env={"KEY": "value"},
            image_paths=["/img.png"],
        )
        assert result.exit_code == 0


class TestAgentRunnerTypeAnnotations:
    """Tests for AgentRunner type annotations and imports."""

    def test_sub_dispatcher_annotation_exists(self) -> None:
        """AgentRunner has sub_dispatcher attribute with correct annotation."""
        # This is a class attribute annotation check
        annotations = AgentRunner.__annotations__
        assert "sub_dispatcher" in annotations

    def test_runner_has_activated_skills_attribute(self) -> None:
        """AgentRunner instance has activated_skills attribute."""
        runner = AgentRunner()
        assert hasattr(runner, "activated_skills")
        assert isinstance(runner.activated_skills, dict)
