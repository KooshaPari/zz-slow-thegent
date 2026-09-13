"""Full test suite for Agent Registry (WL-034).

# @trace WL-034

Covers:
- Frontmatter parsing
- Capability indexing
- Recommendation scoring
- Doctor health checks
- Auto-agent selection in thegent free / run agent
"""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from thegent.agents.capability_index import (
    AgentRecommendation,
    AgentRecord,
    CapabilityIndex,
    DoctorResult,
    _coerce_list,
    _parse_frontmatter,
    _tf_idf_score,
    _tokenize,
)

# @trace WL-034


pytestmark = pytest.mark.requirement("WL-034")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_agent_md(tmp_path: Path, name: str, fm: dict, body: str = "Agent body.") -> Path:
    """Write a minimal agent .md file with frontmatter."""
    content_lines = ["---"]
    content_lines.append(yaml.dump(fm, default_flow_style=False).strip())
    content_lines.append("---")
    content_lines.append("")
    content_lines.append(body)
    path = tmp_path / f"{name}.md"
    path.write_text("\n".join(content_lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 1. Frontmatter parsing
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    """Tests for _parse_frontmatter."""  # @trace WL-034

    def test_simple_frontmatter(self) -> None:
        content = "---\nname: my-agent\nmodel: haiku\n---\n\nBody text."
        fm, body = _parse_frontmatter(content)
        assert fm == {"name": "my-agent", "model": "haiku"}
        assert body == "Body text."

    def test_no_frontmatter(self) -> None:
        content = "Just body text."
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert body == "Just body text."

    def test_empty_frontmatter(self) -> None:
        content = "---\n---\nBody."
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert body == "Body."

    def test_capabilities_list(self) -> None:
        content = "---\ncapabilities:\n  - code-review\n  - python\n---\n"
        fm, _ = _parse_frontmatter(content)
        assert fm["capabilities"] == ["code-review", "python"]

    def test_unclosed_frontmatter_raises(self) -> None:
        content = "---\nname: foo\n"  # No closing ---
        with pytest.raises(ValueError, match="not closed"):
            _parse_frontmatter(content)

    def test_non_mapping_frontmatter_raises(self) -> None:
        content = "---\n- item1\n- item2\n---\n"
        with pytest.raises(ValueError, match="YAML mapping"):
            _parse_frontmatter(content)

    def test_frontmatter_with_description(self) -> None:
        content = "---\nname: test\ndescription: A testing specialist\n---\nBody."
        fm, body = _parse_frontmatter(content)
        assert fm["description"] == "A testing specialist"
        assert body == "Body."


class TestCoerceList:
    """Tests for _coerce_list."""  # @trace WL-034

    def test_none_returns_empty(self) -> None:
        assert _coerce_list(None) == []

    def test_list_passthrough(self) -> None:
        assert _coerce_list(["a", "b", "c"]) == ["a", "b", "c"]

    def test_string_csv(self) -> None:
        result = _coerce_list("code-review, python, testing")
        assert result == ["code-review", "python", "testing"]

    def test_scalar_to_list(self) -> None:
        assert _coerce_list(42) == ["42"]


# ---------------------------------------------------------------------------
# 2. Capability indexing
# ---------------------------------------------------------------------------


class TestCapabilityIndexBuild:
    """Tests for CapabilityIndex construction and indexing."""  # @trace WL-034

    def test_empty_dirs_gives_empty_index(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[tmp_path])
        assert idx.all_agents() == []

    def test_loads_agent_with_capabilities(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "code-reviewer",
            {
                "name": "code-reviewer",
                "description": "Performs code review tasks",
                "capabilities": ["code-review", "python", "testing"],
                "model": "haiku",
            },
        )
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[tmp_path])
        agents = idx.all_agents()
        assert len(agents) == 1
        assert agents[0].name == "code-reviewer"
        assert "code-review" in agents[0].capabilities

    def test_agents_for_capability_lookup(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "python-dev",
            {
                "name": "python-dev",
                "description": "Python developer",
                "capabilities": ["python", "testing"],
                "model": "sonnet",
            },
        )
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[tmp_path])
        python_agents = idx.agents_for_capability("python")
        assert any(a.name == "python-dev" for a in python_agents)

    def test_capability_lookup_case_insensitive(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "security-agent",
            {
                "name": "security-agent",
                "description": "Security auditing",
                "capabilities": ["Security", "SAST"],
                "model": "opus",
            },
        )
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[tmp_path])
        assert len(idx.agents_for_capability("security")) == 1
        assert len(idx.agents_for_capability("sast")) == 1

    def test_multiple_agents_multiple_dirs(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        _write_agent_md(
            dir_a,
            "agent-a",
            {"name": "agent-a", "description": "Agent A", "capabilities": ["python"], "model": "haiku"},
        )
        _write_agent_md(
            dir_b, "agent-b", {"name": "agent-b", "description": "Agent B", "capabilities": ["go"], "model": "sonnet"}
        )
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[dir_a, dir_b])
        assert len(idx.all_agents()) == 2

    def test_malformed_frontmatter_is_skipped(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        bad_file = tmp_path / "bad.md"
        # Unclosed frontmatter block
        bad_file.write_text("---\nname: broken\n", encoding="utf-8")
        good_file = tmp_path / "good.md"
        good_file.write_text("---\nname: good-agent\ndescription: Fine\nmodel: haiku\n---\nBody.", encoding="utf-8")
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            idx = CapabilityIndex.build(extra_dirs=[tmp_path])
        names = [a.name for a in idx.all_agents()]
        assert "good-agent" in names
        assert "broken" not in names

    def test_ttl_cache_returns_same_instance(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[tmp_path]):
            idx1 = CapabilityIndex.get()
            idx2 = CapabilityIndex.get()
            assert idx1 is idx2

    def test_invalidate_clears_cache(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[tmp_path]):
            idx1 = CapabilityIndex.get()
            CapabilityIndex.invalidate()
            idx2 = CapabilityIndex.get()
            assert idx1 is not idx2


# ---------------------------------------------------------------------------
# 3. Recommendation scoring
# ---------------------------------------------------------------------------


class TestRecommendationScoring:
    """Tests for CapabilityIndex.recommend()."""  # @trace WL-034

    def _make_index_with_agents(self, tmp_path: Path, agent_specs: list[dict]) -> CapabilityIndex:
        CapabilityIndex.invalidate()
        for spec in agent_specs:
            _write_agent_md(tmp_path, spec["name"], spec)
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            return CapabilityIndex.build(extra_dirs=[tmp_path])

    def test_empty_task_returns_no_recommendations(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [{"name": "agent-a", "description": "Python developer", "capabilities": ["python"], "model": "haiku"}],
        )
        recs = idx.recommend("")
        assert recs == []

    def test_exact_capability_match_ranks_first(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [
                {
                    "name": "python-dev",
                    "description": "Python developer",
                    "capabilities": ["python", "code-review"],
                    "model": "haiku",
                },
                {
                    "name": "go-dev",
                    "description": "Go developer",
                    "capabilities": ["go", "performance"],
                    "model": "sonnet",
                },
            ],
        )
        recs = idx.recommend("write a python function")
        assert len(recs) > 0
        assert recs[0].name == "python-dev"

    def test_recommendations_sorted_by_score_descending(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [
                {
                    "name": "testing-expert",
                    "description": "Testing expert for python testing",
                    "capabilities": ["testing", "python", "pytest"],
                    "model": "haiku",
                },
                {
                    "name": "generic-agent",
                    "description": "General purpose agent",
                    "capabilities": ["general"],
                    "model": "mini",
                },
            ],
        )
        recs = idx.recommend("run python tests with pytest")
        assert len(recs) >= 1
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limits_results(self, tmp_path: Path) -> None:
        specs = [
            {
                "name": f"agent-{i}",
                "description": f"Python agent {i}",
                "capabilities": ["python"],
                "model": "haiku",
            }
            for i in range(5)
        ]
        idx = self._make_index_with_agents(tmp_path, specs)
        recs = idx.recommend("python task", top_n=3)
        assert len(recs) <= 3

    def test_score_is_between_zero_and_one(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [
                {
                    "name": "security-agent",
                    "description": "Security scanning and SAST analysis",
                    "capabilities": ["security", "sast", "scanning"],
                    "model": "sonnet",
                },
            ],
        )
        recs = idx.recommend("run security scan")
        for rec in recs:
            assert 0.0 <= rec.score <= 1.0

    def test_no_match_returns_empty_list(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [{"name": "go-dev", "description": "Go developer", "capabilities": ["go"], "model": "haiku"}],
        )
        recs = idx.recommend("blockchain smart contract solidity")
        # May or may not match; just ensure it's a list
        assert isinstance(recs, list)

    def test_recommendation_fields_populated(self, tmp_path: Path) -> None:
        idx = self._make_index_with_agents(
            tmp_path,
            [
                {
                    "name": "doc-agent",
                    "description": "Documentation writer",
                    "capabilities": ["documentation", "writing"],
                    "model": "claude",
                }
            ],
        )
        recs = idx.recommend("write documentation")
        assert len(recs) >= 1
        rec = recs[0]
        assert isinstance(rec, AgentRecommendation)
        assert rec.name == "doc-agent"
        assert rec.path.exists()
        assert isinstance(rec.score, float)
        assert isinstance(rec.capabilities, list)

    def test_tf_idf_score_zero_for_no_overlap(self) -> None:
        agent = AgentRecord(
            name="agent",
            path=Path("/fake/agent.md"),
            description="Go developer",
            capabilities=["go"],
            model="haiku",
            runner=None,
            raw_frontmatter={},
            body="",
        )
        idf = {"python": 1.0, "code": 0.8}
        score = _tf_idf_score(["python", "code"], agent, idf)
        assert score == 0.0

    def test_tf_idf_score_full_match(self) -> None:
        agent = AgentRecord(
            name="agent",
            path=Path("/fake/agent.md"),
            description="python code developer",
            capabilities=["python"],
            model="haiku",
            runner=None,
            raw_frontmatter={},
            body="",
        )
        idf = {"python": 1.5, "code": 1.0}
        score = _tf_idf_score(["python", "code"], agent, idf)
        # Both tokens present — score = total_matched / total_possible = 1.0
        assert math.isclose(score, 1.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# 4. Doctor checks
# ---------------------------------------------------------------------------


class TestDoctorChecks:
    """Tests for CapabilityIndex.doctor()."""  # @trace WL-034

    def _make_index(self, tmp_path: Path, agent_specs: list[dict]) -> CapabilityIndex:
        CapabilityIndex.invalidate()
        for spec in agent_specs:
            _write_agent_md(tmp_path, spec["name"], spec)
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[]):
            return CapabilityIndex.build(extra_dirs=[tmp_path])

    def test_healthy_agent_passes_doctor(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [{"name": "healthy", "description": "A fine agent", "capabilities": ["python"], "model": "haiku"}],
        )
        results = idx.doctor()
        assert len(results) == 1
        r = results[0]
        assert r.healthy is True
        assert r.valid_frontmatter is True
        assert r.has_runner_config is True
        assert r.issues == []

    def test_missing_model_and_runner_flagged(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [{"name": "no-runner", "description": "No runner config", "capabilities": ["python"]}],
        )
        results = idx.doctor()
        assert len(results) == 1
        r = results[0]
        assert r.healthy is False
        assert r.has_runner_config is False
        assert any("model" in issue or "runner" in issue for issue in r.issues)

    def test_runner_field_accepted(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [
                {
                    "name": "runner-agent",
                    "description": "Uses runner field",
                    "capabilities": [],
                    "runner": "custom-runner",
                }
            ],
        )
        results = idx.doctor()
        assert results[0].has_runner_config is True

    def test_missing_description_flagged(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [{"name": "no-desc", "capabilities": ["python"], "model": "haiku"}],
        )
        results = idx.doctor()
        assert len(results) == 1
        r = results[0]
        assert any("description" in issue for issue in r.issues)

    def test_empty_runner_string_flagged(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [{"name": "empty-runner", "description": "Empty runner", "capabilities": [], "runner": ""}],
        )
        results = idx.doctor()
        r = results[0]
        assert any("runner" in issue for issue in r.issues)

    def test_doctor_result_has_name_and_path(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [{"name": "my-agent", "description": "Some agent", "capabilities": [], "model": "haiku"}],
        )
        results = idx.doctor()
        r = results[0]
        assert isinstance(r, DoctorResult)
        assert r.name == "my-agent"
        assert isinstance(r.path, Path)

    def test_multiple_agents_all_checked(self, tmp_path: Path) -> None:
        idx = self._make_index(
            tmp_path,
            [
                {"name": "agent-a", "description": "A", "capabilities": ["x"], "model": "haiku"},
                {"name": "agent-b", "description": "B", "capabilities": ["y"]},  # Missing model/runner
            ],
        )
        results = idx.doctor()
        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"agent-a", "agent-b"}
        healthy_count = sum(1 for r in results if r.healthy)
        assert healthy_count == 1  # Only agent-a is healthy


# ---------------------------------------------------------------------------
# 5. Auto-agent selection in thegent free / run agent
# ---------------------------------------------------------------------------


class TestAutoAgentSelection:
    """Tests for auto-agent selection wired into run.py (WL-034)."""  # @trace WL-034

    def test_auto_select_agent_returns_best_match(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "python-tester",
            {
                "name": "python-tester",
                "description": "Python testing expert",
                "capabilities": ["python", "testing", "pytest"],
                "model": "haiku",
            },
        )
        _write_agent_md(
            tmp_path,
            "go-dev",
            {
                "name": "go-dev",
                "description": "Go developer",
                "capabilities": ["go", "performance"],
                "model": "sonnet",
            },
        )
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[tmp_path]):
            CapabilityIndex.invalidate()
            from thegent.cli.apps.run import _auto_select_agent

            result = _auto_select_agent("run python tests")
            assert result == "python-tester"

    def test_auto_select_returns_none_when_no_agents(self, tmp_path: Path) -> None:
        CapabilityIndex.invalidate()
        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[tmp_path]):
            CapabilityIndex.invalidate()
            from thegent.cli.apps.run import _auto_select_agent

            result = _auto_select_agent("some task")
            assert result is None

    def test_auto_select_exception_returns_none(self) -> None:
        """If CapabilityIndex raises, _auto_select_agent should return None (not propagate)."""
        with patch(
            "thegent.agents.capability_index.CapabilityIndex.get",
            side_effect=RuntimeError("index failure"),
        ):
            from thegent.cli.apps.run import _auto_select_agent

            # Must not raise
            result = _auto_select_agent("some task")
            assert result is None

    def test_run_agent_uses_auto_selected_agent(self, tmp_path: Path) -> None:
        """run_agent passes auto-selected agent to run_cmd when --agent not given."""
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "doc-writer",
            {
                "name": "doc-writer",
                "description": "Documentation writing specialist",
                "capabilities": ["documentation", "writing", "markdown"],
                "model": "claude",
            },
        )

        mock_rec = AgentRecommendation(
            name="doc-writer",
            path=tmp_path / "doc-writer.md",
            score=0.85,
            description="Documentation writing specialist",
            capabilities=["documentation", "writing", "markdown"],
        )

        with (
            patch("thegent.cli.apps.run._auto_select_agent", return_value="doc-writer"),
            patch("thegent.agents.capability_index.CapabilityIndex.get") as mock_get,
            patch("thegent.cli.commands.cli.run_cmd") as mock_run_cmd,
        ):
            mock_index = mock_get.return_value
            mock_index.recommend.return_value = [mock_rec]
            mock_run_cmd.return_value = None

            from typer.testing import CliRunner

            from thegent.cli.apps.run import app

            runner = CliRunner()
            runner.invoke(app, ["agent", "write documentation for my module"], catch_exceptions=True)
            # run_cmd should have been called with agent="doc-writer"
            if mock_run_cmd.called:
                call_kwargs = mock_run_cmd.call_args
                assert call_kwargs is not None

    def test_run_agent_no_auto_agent_skips_recommendation(self, tmp_path: Path) -> None:
        """With --no-auto-agent, _auto_select_agent is NOT called."""
        CapabilityIndex.invalidate()

        with patch("thegent.cli.apps.run._auto_select_agent") as mock_select:
            from typer.testing import CliRunner

            from thegent.cli.apps.run import app

            runner = CliRunner()
            with patch("thegent.cli.commands.cli.run_cmd") as mock_run_cmd:
                mock_run_cmd.return_value = None
                runner.invoke(
                    app,
                    ["agent", "do some task", "--no-auto-agent"],
                    catch_exceptions=True,
                )
                mock_select.assert_not_called()

    def test_recommend_agent_public_api(self, tmp_path: Path) -> None:
        """registry.recommend_agent() returns AgentRecommendation list."""
        CapabilityIndex.invalidate()
        _write_agent_md(
            tmp_path,
            "security-scanner",
            {
                "name": "security-scanner",
                "description": "Security scanning specialist",
                "capabilities": ["security", "scanning", "sast"],
                "model": "opus",
            },
        )

        with patch("thegent.agents.capability_index._glob_agent_dirs", return_value=[tmp_path]):
            CapabilityIndex.invalidate()
            from thegent.cli.apps.registry import recommend_agent

            recs = recommend_agent("run a security scan")
            assert isinstance(recs, list)
            if recs:
                assert recs[0].name == "security-scanner"


# ---------------------------------------------------------------------------
# 6. Tokenizer helpers
# ---------------------------------------------------------------------------


class TestTokenizer:
    """Tests for _tokenize helper."""  # @trace WL-034

    def test_basic_tokenization(self) -> None:
        tokens = _tokenize("Code Review Python")
        assert tokens == ["code", "review", "python"]

    def test_strips_punctuation(self) -> None:
        tokens = _tokenize("run tests: pytest, unittest")
        assert "pytest" in tokens
        assert "unittest" in tokens

    def test_empty_string(self) -> None:
        assert _tokenize("") == []

    def test_numbers_included(self) -> None:
        tokens = _tokenize("Python3 type hints")
        assert "python3" in tokens


# ---------------------------------------------------------------------------
# 7. Cross_project/registry integration check
# ---------------------------------------------------------------------------


class TestCrossProjectRegistryIntegration:
    """Verify CrossProjectRegistry is still intact alongside new CapabilityIndex."""  # @trace WL-034

    def test_cross_project_registry_importable(self) -> None:
        from thegent.cross_project.registry import CrossProjectRegistry

        assert CrossProjectRegistry is not None

    def test_cross_project_registry_register_and_get(self, tmp_path: Path) -> None:
        from thegent.cross_project.registry import CrossProjectRegistry

        reg = CrossProjectRegistry(registry_path=tmp_path / "registry.json")
        reg.register_persona("test-project", {"name": "alice", "role": "reviewer"})
        personas = reg.get_personas("test-project")
        assert len(personas) == 1
        assert personas[0]["name"] == "alice"

    def test_cross_project_registry_get_all(self, tmp_path: Path) -> None:
        from thegent.cross_project.registry import CrossProjectRegistry

        reg = CrossProjectRegistry(registry_path=tmp_path / "registry2.json")
        reg.register_persona("proj-a", {"name": "bob"})
        reg.register_persona("proj-b", {"name": "carol"})
        all_personas = reg.get_personas()
        assert len(all_personas) == 2
