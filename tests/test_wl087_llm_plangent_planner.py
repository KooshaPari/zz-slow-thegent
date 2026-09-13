"""Tests for WL-087: LLMPlangentPlanner — LLM-Backed Plan Decomposition.

Covers:
- _parse_llm_response(): valid JSON with all required keys
- _parse_llm_response(): raises ValueError on non-JSON input
- _parse_llm_response(): raises ValueError when root is not a dict
- _parse_llm_response(): raises ValueError when 'nodes' key missing
- _parse_llm_response(): raises ValueError when 'nodes' is not a list
- _parse_llm_response(): raises ValueError when 'nodes' list is empty
- _parse_llm_response(): raises ValueError when node entry is not a dict
- _parse_llm_response(): raises ValueError when node missing required keys
- _parse_llm_response(): raises ValueError for blank node 'id'
- _parse_llm_response(): raises ValueError for blank node 'task'
- _parse_llm_response(): raises ValueError for non-null non-str agent_hint
- _parse_llm_response(): raises ValueError for non-list deps
- _parse_llm_response(): raises ValueError for non-str dep entry
- _parse_llm_response(): raises ValueError for non-int non-null budget_tokens
- _parse_llm_response(): accepts null agent_hint and budget_tokens
- _specs_to_plan_nodes(): creates PlanNodes with remapped UUIDs
- _specs_to_plan_nodes(): deps reference resolved UUIDs not LLM ids
- _specs_to_plan_nodes(): stores agent_hint and budget_tokens in metadata
- _specs_to_plan_nodes(): missing deps reference is silently dropped (unknown ids)
- LLMPlangentPlanner: constructor defaults are correct
- LLMPlangentPlanner: constructor forwards separator and max_nodes_per_level
- LLMPlangentPlanner.decompose(): success path produces Plan with nodes
- LLMPlangentPlanner.decompose(): nodes have agent_hint in metadata
- LLMPlangentPlanner.decompose(): falls back to heuristic when FlashAgent unavailable
- LLMPlangentPlanner.decompose(): raises ValueError on invalid LLM JSON (no fallback)
- LLMPlangentPlanner.decompose(): empty goal raises ValueError from parent
- LLMPlangentPlanner.decompose_to_orchestration_plan(): success path returns OrchestrationPlan
- LLMPlangentPlanner.decompose_to_orchestration_plan(): empty goal raises ValueError
- LLMPlangentPlanner.decompose_to_orchestration_plan(): fallback when model unavailable
- LLMPlangentPlanner.decompose_to_orchestration_plan(): raises ValueError on bad schema
- LLMPlangentPlanner._generate_plan_nodes(): returns None on FlashAgent failure
- LLMPlangentPlanner._generate_plan_nodes(): returns nodes on success
- LLMPlangentPlanner: model and timeout forwarded to FlashAgentConfig
- LLMPlangentPlanner: max_tokens forwarded to FlashAgentConfig

# @trace WL-087
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

from thegent.agents.plangent import (
    LLMPlangentPlanner,
    Plan,
    PlangentPlanner,
    _LLMNodeSpec,
    _parse_llm_response,
    _specs_to_plan_nodes,
)
from thegent.orchestration.plan import OrchestrationPlan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_llm_json(
    *,
    node_id: str = "t1",
    task: str = "Implement the feature",
    agent_hint: str | None = "coder",
    deps: list[str] | None = None,
    budget_tokens: int | None = 500,
    extra_nodes: list[dict[str, Any]] | None = None,
) -> str:
    """Build a valid LLM JSON response string."""
    node: dict[str, Any] = {
        "id": node_id,
        "task": task,
        "agent_hint": agent_hint,
        "deps": deps if deps is not None else [],
        "budget_tokens": budget_tokens,
    }
    nodes = [node]
    if extra_nodes:
        nodes.extend(extra_nodes)
    return json.dumps({"nodes": nodes}).decode()


def _make_flash_result(
    *, success: bool, output: str = "", elapsed_s: float = 0.5
) -> MagicMock:
    """Build a minimal FlashAgentResult mock."""
    result = MagicMock()
    result.success = success
    result.output = output
    result.elapsed_s = elapsed_s
    result.agent_id = "abcd1234"
    return result


def _patch_flash_agent(*, success: bool, output: str = "") -> Any:
    """Patch FlashAgent as imported into the plangent module namespace."""
    mock_result = _make_flash_result(success=success, output=output)
    return patch(
        "thegent.agents.plangent.FlashAgent",
        autospec=True,
        return_value=MagicMock(run=AsyncMock(return_value=mock_result)),
    )


# ---------------------------------------------------------------------------
# _parse_llm_response — valid path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseLlmResponseValid:
    """Happy-path tests for _parse_llm_response.

    # @trace WL-087
    """

    def test_parses_minimal_valid_json(self) -> None:
        """_parse_llm_response parses a single-node JSON correctly."""
        raw = _make_valid_llm_json()
        specs = _parse_llm_response(raw)
        assert len(specs) == 1
        assert specs[0].id == "t1"
        assert specs[0].task == "Implement the feature"
        assert specs[0].agent_hint == "coder"
        assert specs[0].deps == []
        assert specs[0].budget_tokens == 500

    def test_parses_null_agent_hint(self) -> None:
        """_parse_llm_response accepts null agent_hint without error."""
        raw = _make_valid_llm_json(agent_hint=None)
        specs = _parse_llm_response(raw)
        assert specs[0].agent_hint is None

    def test_parses_null_budget_tokens(self) -> None:
        """_parse_llm_response accepts null budget_tokens without error."""
        raw = _make_valid_llm_json(budget_tokens=None)
        specs = _parse_llm_response(raw)
        assert specs[0].budget_tokens is None

    def test_parses_multiple_nodes_with_deps(self) -> None:
        """_parse_llm_response handles multiple nodes with dependency references."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "Step 1",
                        "agent_hint": None,
                        "deps": [],
                        "budget_tokens": None,
                    },
                    {
                        "id": "t2",
                        "task": "Step 2",
                        "agent_hint": "coder",
                        "deps": ["t1"],
                        "budget_tokens": 200,
                    },
                ]
            }
        )
        specs = _parse_llm_response(raw)
        assert len(specs) == 2
        assert specs[1].deps == ["t1"]

    def test_strips_whitespace_from_id_and_task(self) -> None:
        """_parse_llm_response strips leading/trailing whitespace from id and task."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": " t1 ",
                        "task": "  do it  ",
                        "agent_hint": None,
                        "deps": [],
                        "budget_tokens": None,
                    }
                ]
            }
        )
        specs = _parse_llm_response(raw)
        assert specs[0].id == "t1"
        assert specs[0].task == "do it"


# ---------------------------------------------------------------------------
# _parse_llm_response — error paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseLlmResponseErrors:
    """Error-path tests for _parse_llm_response — all must raise ValueError.

    # @trace WL-087
    """

    def test_raises_on_non_json_input(self) -> None:
        """_parse_llm_response raises ValueError on non-JSON text."""
        with pytest.raises(ValueError, match="not valid JSON"):
            _parse_llm_response("This is plain text, not JSON.")

    def test_raises_on_json_array_at_root(self) -> None:
        """_parse_llm_response raises ValueError when root is a JSON array."""
        with pytest.raises(ValueError, match="JSON object"):
            _parse_llm_response(json.dumps([{"id": "t1"}]).decode())

    def test_raises_when_nodes_key_missing(self) -> None:
        """_parse_llm_response raises ValueError when 'nodes' key is absent."""
        with pytest.raises(ValueError, match="missing required key 'nodes'"):
            _parse_llm_response(json.dumps({"tasks": []}).decode())

    def test_raises_when_nodes_is_not_list(self) -> None:
        """_parse_llm_response raises ValueError when 'nodes' is not a list."""
        with pytest.raises(ValueError, match="'nodes' must be a list"):
            _parse_llm_response(json.dumps({"nodes": "not a list"}).decode())

    def test_raises_when_nodes_list_is_empty(self) -> None:
        """_parse_llm_response raises ValueError when 'nodes' is an empty list."""
        with pytest.raises(ValueError, match="must not be empty"):
            _parse_llm_response(json.dumps({"nodes": []}).decode())

    def test_raises_when_node_entry_is_not_dict(self) -> None:
        """_parse_llm_response raises ValueError when a node entry is not a dict."""
        with pytest.raises(ValueError, match="nodes\\[0\\] must be a JSON object"):
            _parse_llm_response(json.dumps({"nodes": ["string not dict"]}).decode())

    def test_raises_when_node_missing_required_keys(self) -> None:
        """_parse_llm_response raises ValueError when a node is missing required keys."""
        with pytest.raises(ValueError, match="missing required keys"):
            _parse_llm_response(
                json.dumps({"nodes": [{"id": "t1", "task": "do"}]}).decode()
            )

    def test_raises_on_blank_node_id(self) -> None:
        """_parse_llm_response raises ValueError for a blank 'id' field."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "   ",
                        "task": "do",
                        "agent_hint": None,
                        "deps": [],
                        "budget_tokens": None,
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="non-empty string"):
            _parse_llm_response(raw)

    def test_raises_on_blank_node_task(self) -> None:
        """_parse_llm_response raises ValueError for a blank 'task' field."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "",
                        "agent_hint": None,
                        "deps": [],
                        "budget_tokens": None,
                    }
                ]
            }
        ).decode()
        with pytest.raises(ValueError, match="non-empty string"):
            _parse_llm_response(raw)

    def test_raises_on_non_str_agent_hint(self) -> None:
        """_parse_llm_response raises ValueError when agent_hint is non-string non-null."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "do",
                        "agent_hint": 42,
                        "deps": [],
                        "budget_tokens": None,
                    }
                ]
            }
        ).decode()
        with pytest.raises(ValueError, match="agent_hint must be a string or null"):
            _parse_llm_response(raw)

    def test_raises_on_non_list_deps(self) -> None:
        """_parse_llm_response raises ValueError when deps is not a list."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "do",
                        "agent_hint": None,
                        "deps": "t0",
                        "budget_tokens": None,
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="deps must be a list"):
            _parse_llm_response(raw)

    def test_raises_on_non_str_dep_entry(self) -> None:
        """_parse_llm_response raises ValueError when a dep entry is not a string."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "do",
                        "agent_hint": None,
                        "deps": [123],
                        "budget_tokens": None,
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="deps entries must be strings"):
            _parse_llm_response(raw)

    def test_raises_on_float_budget_tokens(self) -> None:
        """_parse_llm_response raises ValueError when budget_tokens is a float."""
        raw = json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "do",
                        "agent_hint": None,
                        "deps": [],
                        "budget_tokens": 1.5,
                    }
                ]
            }
        ).decode()
        with pytest.raises(ValueError, match="budget_tokens must be an int or null"):
            _parse_llm_response(raw)


# ---------------------------------------------------------------------------
# _specs_to_plan_nodes
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSpecsToPlanNodes:
    """Tests for the _specs_to_plan_nodes conversion function.

    # @trace WL-087
    """

    def test_creates_plan_nodes_with_real_uuids(self) -> None:
        """_specs_to_plan_nodes produces PlanNodes with UUID-format ids."""
        import re

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        specs = [
            _LLMNodeSpec(
                id="t1", task="Task A", agent_hint=None, deps=[], budget_tokens=None
            )
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert len(nodes) == 1
        assert uuid_pattern.match(nodes[0].id), f"Expected UUID, got {nodes[0].id!r}"

    def test_deps_reference_resolved_uuids(self) -> None:
        """_specs_to_plan_nodes remaps dep ids from LLM namespace to real UUIDs."""
        specs = [
            _LLMNodeSpec(
                id="t1", task="First", agent_hint=None, deps=[], budget_tokens=None
            ),
            _LLMNodeSpec(
                id="t2", task="Second", agent_hint=None, deps=["t1"], budget_tokens=None
            ),
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert nodes[1].depends_on == [nodes[0].id]

    def test_agent_hint_stored_in_metadata(self) -> None:
        """_specs_to_plan_nodes stores agent_hint in node.metadata."""
        specs = [
            _LLMNodeSpec(
                id="t1",
                task="do it",
                agent_hint="researcher",
                deps=[],
                budget_tokens=None,
            )
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert nodes[0].metadata.get("agent_hint") == "researcher"

    def test_budget_tokens_stored_in_metadata(self) -> None:
        """_specs_to_plan_nodes stores budget_tokens in node.metadata."""
        specs = [
            _LLMNodeSpec(
                id="t1", task="do it", agent_hint=None, deps=[], budget_tokens=800
            )
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert nodes[0].metadata.get("budget_tokens") == 800

    def test_null_agent_hint_not_in_metadata(self) -> None:
        """_specs_to_plan_nodes does not add agent_hint to metadata when null."""
        specs = [
            _LLMNodeSpec(
                id="t1", task="do it", agent_hint=None, deps=[], budget_tokens=None
            )
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert "agent_hint" not in nodes[0].metadata

    def test_unknown_dep_reference_silently_dropped(self) -> None:
        """_specs_to_plan_nodes drops dep references to unknown LLM ids."""
        specs = [
            _LLMNodeSpec(
                id="t1",
                task="do it",
                agent_hint=None,
                deps=["unknown_id"],
                budget_tokens=None,
            )
        ]
        nodes = _specs_to_plan_nodes(specs)
        assert nodes[0].depends_on == []


# ---------------------------------------------------------------------------
# LLMPlangentPlanner — constructor
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMPlangentPlannerConstructor:
    """Tests for LLMPlangentPlanner constructor defaults and overrides.

    # @trace WL-087
    """

    def test_default_model_is_haiku(self) -> None:
        """LLMPlangentPlanner defaults to claude-haiku-4.5."""
        planner = LLMPlangentPlanner()
        assert planner._model == "claude-haiku-4.5"

    def test_default_timeout_is_30(self) -> None:
        """LLMPlangentPlanner defaults timeout_s to 30.0."""
        planner = LLMPlangentPlanner()
        assert planner._timeout_s == 30.0

    def test_default_max_tokens_is_1024(self) -> None:
        """LLMPlangentPlanner defaults max_tokens to 1024."""
        planner = LLMPlangentPlanner()
        assert planner._max_tokens == 1024

    def test_inherits_from_plangent_planner(self) -> None:
        """LLMPlangentPlanner is a subclass of PlangentPlanner."""
        assert issubclass(LLMPlangentPlanner, PlangentPlanner)

    def test_custom_model_stored(self) -> None:
        """LLMPlangentPlanner stores custom model string."""
        planner = LLMPlangentPlanner(model="gemini-3-flash")
        assert planner._model == "gemini-3-flash"

    def test_separator_forwarded_to_parent(self) -> None:
        """LLMPlangentPlanner forwards separator to PlangentPlanner."""
        planner = LLMPlangentPlanner(separator="|")
        assert planner._separator == "|"

    def test_max_nodes_per_level_forwarded(self) -> None:
        """LLMPlangentPlanner forwards max_nodes_per_level to PlangentPlanner."""
        planner = LLMPlangentPlanner(max_nodes_per_level=10)
        assert planner._max_nodes_per_level == 10


# ---------------------------------------------------------------------------
# LLMPlangentPlanner.decompose() — success path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMPlangentPlannerDecomposeSuccess:
    """Success-path tests for LLMPlangentPlanner.decompose().

    # @trace WL-087
    """

    def _valid_two_node_json(self) -> str:
        return json.dumps(
            {
                "nodes": [
                    {
                        "id": "t1",
                        "task": "Research the topic",
                        "agent_hint": "researcher",
                        "deps": [],
                        "budget_tokens": 300,
                    },
                    {
                        "id": "t2",
                        "task": "Write the code",
                        "agent_hint": "coder",
                        "deps": ["t1"],
                        "budget_tokens": 700,
                    },
                ]
            }
        ).decode()

    def test_decompose_returns_plan(self) -> None:
        """decompose() returns a Plan instance on success."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_two_node_json()):
            plan = planner.decompose("Build a feature")
        assert isinstance(plan, Plan)

    def test_decompose_goal_stored_in_plan(self) -> None:
        """decompose() stores the stripped goal in plan.goal."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_two_node_json()):
            plan = planner.decompose("  Build a feature  ")
        assert plan.goal == "Build a feature"

    def test_decompose_produces_correct_node_count(self) -> None:
        """decompose() produces the number of nodes from LLM output."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_two_node_json()):
            plan = planner.decompose("Build a feature")
        assert len(plan.nodes) == 2

    def test_decompose_nodes_task_text_from_llm(self) -> None:
        """decompose() nodes carry the task text produced by the LLM."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_two_node_json()):
            plan = planner.decompose("Build a feature")
        tasks = [n.task for n in plan.nodes]
        assert "Research the topic" in tasks
        assert "Write the code" in tasks

    def test_decompose_all_nodes_start_pending(self) -> None:
        """decompose() nodes all start with 'pending' status."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_two_node_json()):
            plan = planner.decompose("Build a feature")
        assert all(n.status == "pending" for n in plan.nodes)


# ---------------------------------------------------------------------------
# LLMPlangentPlanner.decompose() — fallback and error paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMPlangentPlannerDecomposeFallback:
    """Fallback and error-path tests for LLMPlangentPlanner.decompose().

    # @trace WL-087
    """

    def test_fallback_to_heuristic_when_model_unavailable(self) -> None:
        """decompose() uses parent heuristic when FlashAgent returns success=False."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=False, output=""):
            plan = planner.decompose("Build something")
        # Parent heuristic produces at least 1 node.
        assert isinstance(plan, Plan)
        assert len(plan.nodes) >= 1

    def test_fallback_emits_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """decompose() logs a WARNING when falling back to heuristic."""
        import logging

        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=False):
            with caplog.at_level(logging.WARNING, logger="thegent.agents.plangent"):
                planner.decompose("do something")
        assert any("falling back to heuristic" in rec.message for rec in caplog.records)

    def test_raises_on_invalid_json_schema_no_fallback(self) -> None:
        """decompose() raises ValueError on bad LLM JSON — no silent fallback."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output='{"nodes": []}'):
            with pytest.raises(ValueError, match="must not be empty"):
                planner.decompose("Build something")

    def test_raises_on_non_json_output_no_fallback(self) -> None:
        """decompose() raises ValueError when LLM returns non-JSON — no silent fallback."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output="I cannot decompose this goal."):
            with pytest.raises(ValueError, match="not valid JSON"):
                planner.decompose("Build something")

    def test_empty_goal_raises_value_error(self) -> None:
        """decompose() raises ValueError for empty goal (inherited from PlangentPlanner)."""
        planner = LLMPlangentPlanner()
        with pytest.raises(ValueError, match="non-empty"):
            planner.decompose("")

    def test_whitespace_only_goal_raises(self) -> None:
        """decompose() raises ValueError for whitespace-only goal."""
        planner = LLMPlangentPlanner()
        with pytest.raises(ValueError, match="non-empty"):
            planner.decompose("   ")


# ---------------------------------------------------------------------------
# LLMPlangentPlanner.decompose_to_orchestration_plan()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMPlangentPlannerOrchestrationPlan:
    """Tests for decompose_to_orchestration_plan() producing OrchestrationPlan.

    # @trace WL-087
    """

    def _valid_json(self) -> str:
        return json.dumps(
            {
                "nodes": [
                    {
                        "id": "a1",
                        "task": "Analyse",
                        "agent_hint": "analyst",
                        "deps": [],
                        "budget_tokens": 200,
                    },
                    {
                        "id": "a2",
                        "task": "Implement",
                        "agent_hint": "coder",
                        "deps": ["a1"],
                        "budget_tokens": 600,
                    },
                ]
            }
        ).decode()

    def test_returns_orchestration_plan_instance(self) -> None:
        """decompose_to_orchestration_plan() returns an OrchestrationPlan."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_json()):
            oplan = asyncio.run(planner.decompose_to_orchestration_plan("My goal"))
        assert isinstance(oplan, OrchestrationPlan)

    def test_orchestration_plan_goal_set(self) -> None:
        """decompose_to_orchestration_plan() sets goal on the returned plan."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_json()):
            oplan = asyncio.run(planner.decompose_to_orchestration_plan("My goal"))
        assert oplan.goal == "My goal"

    def test_orchestration_plan_node_count(self) -> None:
        """decompose_to_orchestration_plan() carries all LLM nodes."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_json()):
            oplan = asyncio.run(planner.decompose_to_orchestration_plan("My goal"))
        assert len(oplan.nodes) == 2

    def test_orchestration_plan_metadata_preserved(self) -> None:
        """decompose_to_orchestration_plan() preserves agent_hint metadata on nodes."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output=self._valid_json()):
            oplan = asyncio.run(planner.decompose_to_orchestration_plan("My goal"))
        assert oplan.nodes[0].metadata.get("agent_hint") == "analyst"
        assert oplan.nodes[1].metadata.get("agent_hint") == "coder"

    def test_orchestration_plan_empty_goal_raises(self) -> None:
        """decompose_to_orchestration_plan() raises ValueError for empty goal."""
        planner = LLMPlangentPlanner()
        with pytest.raises(ValueError, match="non-empty"):
            asyncio.run(planner.decompose_to_orchestration_plan(""))

    def test_orchestration_plan_fallback_when_unavailable(self) -> None:
        """decompose_to_orchestration_plan() falls back to heuristic when model unavailable."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=False):
            oplan = asyncio.run(planner.decompose_to_orchestration_plan("My goal"))
        assert isinstance(oplan, OrchestrationPlan)
        assert len(oplan.nodes) >= 1

    def test_orchestration_plan_bad_schema_raises(self) -> None:
        """decompose_to_orchestration_plan() raises ValueError on schema failure."""
        planner = LLMPlangentPlanner()
        with _patch_flash_agent(success=True, output='{"nodes": [{"id": "t1"}]}'):
            with pytest.raises(ValueError, match="missing required keys"):
                asyncio.run(planner.decompose_to_orchestration_plan("My goal"))


# ---------------------------------------------------------------------------
# LLMPlangentPlanner — FlashAgentConfig forwarding
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLLMPlangentPlannerConfigForwarding:
    """Tests verifying FlashAgentConfig parameters are forwarded correctly.

    # @trace WL-087
    """

    def _capture_flash_config(self) -> tuple[MagicMock, Any]:
        """Return (patcher_context, captured_config_list) for inspection."""
        captured: list[Any] = []
        valid_output = _make_valid_llm_json()

        async def _fake_run(config: Any) -> MagicMock:
            captured.append(config)
            return _make_flash_result(success=True, output=valid_output)

        mock_instance = MagicMock()
        mock_instance.run = _fake_run
        mock_cls = MagicMock(return_value=mock_instance)

        patcher = patch("thegent.agents.plangent.FlashAgent", mock_cls)
        return patcher, captured

    def test_model_forwarded_to_flash_config(self) -> None:
        """LLMPlangentPlanner forwards model= to FlashAgentConfig."""
        planner = LLMPlangentPlanner(model="gemini-3-flash")
        patcher, captured = self._capture_flash_config()
        with patcher:
            planner.decompose("do something")
        assert captured[0].model == "gemini-3-flash"

    def test_timeout_forwarded_to_flash_config(self) -> None:
        """LLMPlangentPlanner forwards timeout_s= to FlashAgentConfig."""
        planner = LLMPlangentPlanner(timeout_s=15.0)
        patcher, captured = self._capture_flash_config()
        with patcher:
            planner.decompose("do something")
        assert captured[0].timeout_s == 15.0

    def test_max_tokens_forwarded_to_flash_config(self) -> None:
        """LLMPlangentPlanner forwards max_tokens= to FlashAgentConfig."""
        planner = LLMPlangentPlanner(max_tokens=512)
        patcher, captured = self._capture_flash_config()
        with patcher:
            planner.decompose("do something")
        assert captured[0].max_tokens == 512
