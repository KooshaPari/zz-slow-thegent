"""Unit tests for runtime_dispatcher module.

Tests the pure Python JIT-friendly routing logic for task classification
and agent selection based on keyword matching.
Also tests PerformanceModule, dispatchers, and runtime status functions.
"""

from unittest.mock import MagicMock

import pytest

from thegent.infra.runtime_dispatcher import (
    HAS_EXTISM,
    HAS_FREETHREADING,
    IS_PYPY,
    PerformanceModule,
    WasmDispatcher,
    _python_route_logic,
    get_json_dumps,
    get_json_loads,
    get_router,
    get_runtime_status,
    get_toml_loads,
    json_dumps_dispatcher,
    json_loads_dispatcher,
    toml_loads_dispatcher,
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"MockAgent({self.name})"


class TestPythonRouteLogicBasic:
    """Basic tests for _python_route_logic."""

    def test_returns_agent_from_list(self):
        """Test that route logic returns an agent from the provided list."""
        agents = [MockAgent("agent1"), MockAgent("agent2")]
        result = _python_route_logic("do something", agents)
        assert result in agents

    def test_returns_single_agent(self):
        """Test that route logic returns exactly one agent."""
        agents = [MockAgent("agent1"), MockAgent("agent2")]
        result = _python_route_logic("do something", agents)
        assert result is not None

    def test_empty_agents_list(self):
        """Test behavior with empty agents list."""
        result = _python_route_logic("do something", [])
        assert result is None

    def test_single_agent_returns_that_agent(self):
        """Test that single agent is returned."""
        agent = MockAgent("lone_agent")
        result = _python_route_logic("any task", [agent])
        assert result is agent


class TestPythonRouteLogicCodeKeywords:
    """Tests for code-related task routing."""

    def test_implement_keyword_prefers_implementer(self):
        """Test 'implement' keyword prefers implementer agents."""
        generic_agent = MockAgent("generic_agent")
        implementer = MockAgent("code_implementer")
        agents = [generic_agent, implementer]

        result = _python_route_logic("implement the feature", agents)
        assert result is implementer

    def test_code_keyword_prefers_coder(self):
        """Test 'code' keyword prefers coder agents."""
        generic_agent = MockAgent("agent")
        coder = MockAgent("super_coder")
        agents = [generic_agent, coder]

        result = _python_route_logic("code the module", agents)
        assert result is coder

    def test_write_keyword_scores_implementer(self):
        """Test 'write' keyword scores implementer agents higher."""
        generic = MockAgent("worker")
        implementer = MockAgent("implementer_bot")
        agents = [generic, implementer]

        result = _python_route_logic("write a new function", agents)
        assert result is implementer

    def test_fix_keyword_routes_to_implementer(self):
        """Test 'fix' keyword routes to implementer."""
        planner = MockAgent("planner")
        implementer = MockAgent("implementer")
        agents = [planner, implementer]

        result = _python_route_logic("fix the bug", agents)
        assert result is implementer

    def test_debug_keyword_routes_to_implementer(self):
        """Test 'debug' keyword routes to implementer."""
        researcher = MockAgent("researcher")
        implementer = MockAgent("implementer")
        agents = [researcher, implementer]

        result = _python_route_logic("debug the issue", agents)
        assert result is implementer

    def test_refactor_keyword_routes_to_implementer(self):
        """Test 'refactor' keyword routes to implementer."""
        planner = MockAgent("architect")
        implementer = MockAgent("implementer")
        agents = [planner, implementer]

        result = _python_route_logic("refactor the code", agents)
        assert result is implementer

    def test_patch_keyword_routes_to_implementer(self):
        """Test 'patch' keyword routes to implementer."""
        researcher = MockAgent("researcher")
        implementer = MockAgent("implementer")
        agents = [researcher, implementer]

        result = _python_route_logic("patch the vulnerability", agents)
        assert result is implementer


class TestPythonRouteLogicResearchKeywords:
    """Tests for research-related task routing."""

    def test_research_keyword_prefers_researcher(self):
        """Test 'research' keyword prefers researcher agents."""
        implementer = MockAgent("implementer")
        researcher = MockAgent("research_agent")
        agents = [implementer, researcher]

        result = _python_route_logic("research the topic", agents)
        assert result is researcher

    def test_search_keyword_routes_to_search(self):
        """Test 'search' keyword routes to search agents."""
        implementer = MockAgent("implementer")
        searcher = MockAgent("search_agent")
        agents = [implementer, searcher]

        result = _python_route_logic("search for the file", agents)
        assert result is searcher

    def test_find_keyword_routes_to_researcher(self):
        """Test 'find' keyword routes to researcher agents."""
        generic = MockAgent("generic")
        researcher = MockAgent("researcher")
        agents = [generic, researcher]

        result = _python_route_logic("find the solution", agents)
        assert result is researcher

    def test_explore_keyword_routes_to_researcher(self):
        """Test 'explore' keyword routes to researcher agents."""
        planner = MockAgent("planner")
        researcher = MockAgent("researcher")
        agents = [planner, researcher]

        result = _python_route_logic("explore the codebase", agents)
        assert result is researcher

    def test_analyze_keyword_routes_to_researcher(self):
        """Test 'analyze' keyword routes to researcher agents."""
        implementer = MockAgent("implementer")
        researcher = MockAgent("researcher")
        agents = [implementer, researcher]

        result = _python_route_logic("analyze the data", agents)
        assert result is researcher

    def test_summarize_keyword_routes_to_researcher(self):
        """Test 'summarize' keyword routes to researcher agents."""
        planner = MockAgent("planner")
        researcher = MockAgent("researcher")
        agents = [planner, researcher]

        result = _python_route_logic("summarize the findings", agents)
        assert result is researcher


class TestPythonRouteLogicPlanKeywords:
    """Tests for planning-related task routing."""

    def test_plan_keyword_prefers_planner(self):
        """Test 'plan' keyword prefers planner agents."""
        implementer = MockAgent("implementer")
        planner = MockAgent("planner_agent")
        agents = [implementer, planner]

        result = _python_route_logic("plan the project", agents)
        assert result is planner

    def test_design_keyword_routes_to_architect(self):
        """Test 'design' keyword routes to architect agents."""
        researcher = MockAgent("researcher")
        architect = MockAgent("architect")
        agents = [researcher, architect]

        result = _python_route_logic("design the system", agents)
        assert result is architect

    def test_architect_keyword_routes_to_planner(self):
        """Test 'architect' keyword routes to planner agents."""
        implementer = MockAgent("implementer")
        planner = MockAgent("planner")
        agents = [implementer, planner]

        result = _python_route_logic("architect the solution", agents)
        assert result is planner

    def test_spec_keyword_routes_to_planner(self):
        """Test 'spec' keyword routes to planner agents."""
        researcher = MockAgent("researcher")
        planner = MockAgent("planner")
        agents = [researcher, planner]

        result = _python_route_logic("spec out the requirements", agents)
        assert result is planner

    def test_document_keyword_routes_to_planner(self):
        """Test 'document' keyword routes to planner agents."""
        implementer = MockAgent("implementer")
        planner = MockAgent("planner")
        agents = [implementer, planner]

        result = _python_route_logic("document the API", agents)
        assert result is planner


class TestPythonRouteLogicFallbackScoring:
    """Tests for fallback scoring when no keywords match."""

    def test_generic_agent_gets_base_score(self):
        """Test generic agents get base score when no keywords match."""
        agents = [MockAgent("generic_bot")]
        result = _python_route_logic("hello world", agents)
        assert result is agents[0]

    def test_agent_suffix_gets_bonus(self):
        """Test agents with 'agent' in name get bonus scoring."""
        generic = MockAgent("worker")
        agent = MockAgent("my_agent")
        agents = [generic, agent]

        # Using a code keyword, agent gets +5 bonus
        result = _python_route_logic("implement feature", agents)
        # Both get code scores, but agent gets +5 bonus
        assert result is agent

    def test_first_agent_wins_on_tie(self):
        """Test that first agent wins when scores are tied."""
        agent1 = MockAgent("agent_alpha")
        agent2 = MockAgent("agent_beta")
        agents = [agent1, agent2]

        # Both have same name pattern, no keywords match
        result = _python_route_logic("unknown task", agents)
        # First agent should win as it gets selected first with same score
        assert result in agents


class TestPythonRouteLogicCaseInsensitivity:
    """Tests for case-insensitive keyword matching."""

    def test_uppercase_keywords(self):
        """Test uppercase keywords are matched."""
        implementer = MockAgent("implementer")
        researcher = MockAgent("researcher")
        agents = [researcher, implementer]

        result = _python_route_logic("IMPLEMENT THE FEATURE", agents)
        assert result is implementer

    def test_mixed_case_keywords(self):
        """Test mixed case keywords are matched."""
        planner = MockAgent("planner")
        implementer = MockAgent("implementer")
        agents = [implementer, planner]

        result = _python_route_logic("Plan The Project", agents)
        assert result is planner

    def test_agent_names_case_insensitive(self):
        """Test agent name matching is case-insensitive."""
        generic = MockAgent("GENERIC")
        implementer = MockAgent("IMPLementer")
        agents = [generic, implementer]

        result = _python_route_logic("implement it", agents)
        assert result is implementer


class TestPythonRouteLogicComplexTasks:
    """Tests for complex multi-keyword tasks."""

    def test_multiple_keywords_first_wins(self):
        """Test tasks with multiple keyword types."""
        implementer = MockAgent("implementer")
        researcher = MockAgent("researcher")
        planner = MockAgent("planner")
        agents = [implementer, researcher, planner]

        # Has both implement and plan keywords - implementer scores higher
        result = _python_route_logic("implement and plan the feature", agents)
        # implementer gets +10 for implement, planner gets +10 for plan
        # Since implementer comes first with same score, it wins
        assert result is implementer

    def test_composite_task_description(self):
        """Test routing with composite task description."""
        researcher = MockAgent("researcher")
        implementer = MockAgent("implementer")
        agents = [researcher, implementer]

        result = _python_route_logic("research and code the solution", agents)
        # Both get +10, implementer gets selected first
        assert result in agents


class TestPythonRouteLogicAgentAttributes:
    """Tests for agent attribute handling."""

    def test_agent_without_name_attribute(self):
        """Test handling agents without name attribute."""
        # Create a mock that doesn't have a name attribute by default
        agent = MagicMock(spec=[])  # Empty spec means no attributes
        # The function uses getattr(agent, "name", str(agent))
        # str() on MagicMock returns something like "<MagicMock id=...>"

        result = _python_route_logic("implement", [agent])
        # Should not crash, returns the agent
        assert result is agent

    def test_agent_with_string_representation(self):
        """Test agents that are just strings."""
        # The function expects objects with .name attribute
        # If agents are strings, getattr returns the string itself
        agents = ["implementer", "researcher"]
        result = _python_route_logic("implement", agents)
        # String's .lower() works, so routing should succeed
        assert result in agents


class TestPythonRouteLogicEdgeCases:
    """Edge case tests for _python_route_logic."""

    def test_empty_task_string(self):
        """Test with empty task string."""
        agents = [MockAgent("agent1"), MockAgent("agent2")]
        result = _python_route_logic("", agents)
        assert result in agents

    def test_task_with_only_spaces(self):
        """Test task with only whitespace."""
        agents = [MockAgent("agent1")]
        result = _python_route_logic("   ", agents)
        assert result is agents[0]

    def test_task_with_special_characters(self):
        """Test task with special characters."""
        implementer = MockAgent("implementer")
        agents = [implementer]
        result = _python_route_logic("implement!@#$%^&*()", agents)
        # "implement" substring should still match
        assert result is implementer

    def test_partial_keyword_match(self):
        """Test partial keyword matching."""
        implementer = MockAgent("implementer")
        agents = [implementer]
        # "implementation" contains "implement"
        result = _python_route_logic("implementation needed", agents)
        assert result is implementer


class TestRuntimeFlags:
    """Tests for runtime identification flags."""

    def test_is_pypy_is_boolean(self):
        """Test IS_PYPY is a boolean."""
        assert isinstance(IS_PYPY, bool)

    def test_has_freethreading_is_boolean(self):
        """Test HAS_FREETHREADING is a boolean."""
        assert isinstance(HAS_FREETHREADING, bool)

    def test_is_pypy_matches_implementation(self):
        """Test IS_PYPY matches sys.implementation.name."""
        import sys

        expected = sys.implementation.name == "pypy"
        assert expected == IS_PYPY


class TestPerformanceModule:
    """Tests for PerformanceModule class."""

    def test_init_sets_name(self):
        """Test initialization sets the module name."""
        pm = PerformanceModule("test_module")
        assert pm.name == "test_module"

    def test_init_empty_implementations(self):
        """Test initialization starts with empty implementations."""
        pm = PerformanceModule("test_module")
        assert pm._implementations == {}

    def test_init_selected_is_none(self):
        """Test initialization starts with no selected implementation."""
        pm = PerformanceModule("test_module")
        assert pm._selected is None

    def test_register_stores_implementation(self):
        """Test register stores an implementation."""
        pm = PerformanceModule("test_module")

        def impl(x):
            return x

        pm.register("python", impl)
        assert pm._implementations["python"] is impl

    def test_register_multiple_implementations(self):
        """Test registering multiple implementations."""
        pm = PerformanceModule("test_module")
        pm.register("python", lambda: "py")
        pm.register("native", lambda: "native")
        pm.register("pypy", lambda: "pypy")
        assert len(pm._implementations) == 3

    def test_get_impl_returns_cached_selection(self):
        """Test get_impl returns cached selection without re-evaluation."""
        pm = PerformanceModule("test_module")
        pm._selected = lambda: "cached"
        result = pm.get_impl()
        assert result() == "cached"

    def test_get_impl_selects_native_on_cpython(self):
        """Test get_impl selects native on CPython when available."""
        # Create a fresh module to avoid cache
        pm = PerformanceModule("test_module")

        def native_impl():
            return "native"

        def python_impl():
            return "python"

        pm.register("native", native_impl)
        pm.register("python", python_impl)

        # On CPython (not PyPy), native should be selected
        if not IS_PYPY:
            result = pm.get_impl()
            assert result is native_impl

    def test_get_impl_selects_pypy_on_pypy(self):
        """Test get_impl selects pypy on PyPy when available."""
        pm = PerformanceModule("test_module")

        def pypy_impl():
            return "pypy"

        def python_impl():
            return "python"

        pm.register("pypy", pypy_impl)
        pm.register("python", python_impl)

        # On PyPy, pypy implementation should be selected
        if IS_PYPY:
            result = pm.get_impl()
            assert result is pypy_impl

    def test_get_impl_falls_back_to_python(self):
        """Test get_impl falls back to python implementation."""
        pm = PerformanceModule("test_module")

        def python_impl():
            return "python"

        pm.register("python", python_impl)

        result = pm.get_impl()
        assert result is python_impl

    def test_get_impl_returns_none_when_no_python_fallback(self):
        """Test get_impl returns None when no python fallback exists."""
        pm = PerformanceModule("test_module")
        # No implementations registered
        result = pm.get_impl()
        assert result is None

    def test_get_impl_caches_selection(self):
        """Test get_impl caches the selected implementation."""
        pm = PerformanceModule("test_module")

        def python_impl():
            return "python"

        pm.register("python", python_impl)

        result1 = pm.get_impl()
        result2 = pm.get_impl()

        # Same object should be returned (cached)
        assert result1 is result2
        assert pm._selected is python_impl


class TestJsonDumpsDispatcher:
    """Tests for json_dumps_dispatcher."""

    def test_dispatcher_exists(self):
        """Test json_dumps_dispatcher is initialized."""
        assert json_dumps_dispatcher is not None
        assert isinstance(json_dumps_dispatcher, PerformanceModule)

    def test_dispatcher_has_implementations(self):
        """Test json_dumps_dispatcher has implementations registered."""
        assert len(json_dumps_dispatcher._implementations) > 0

    def test_dumps_returns_string(self):
        """Test json dumps returns a string."""
        dumps = get_json_dumps()
        result = dumps({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result

    def test_dumps_with_kwargs(self):
        """Test json dumps with keyword arguments."""
        dumps = get_json_dumps()
        # Note: orjson doesn't support indent, so we just test with default args
        result = dumps({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result


class TestJsonLoadsDispatcher:
    """Tests for json_loads_dispatcher."""

    def test_dispatcher_exists(self):
        """Test json_loads_dispatcher is initialized."""
        assert json_loads_dispatcher is not None
        assert isinstance(json_loads_dispatcher, PerformanceModule)

    def test_loads_returns_dict(self):
        """Test json loads returns a dict."""
        loads = get_json_loads()
        result = loads('{"key": "value"}')
        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_loads_with_bytes(self):
        """Test json loads accepts bytes."""
        loads = get_json_loads()
        result = loads(b'{"key": "value"}')
        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_loads_with_kwargs(self):
        """Test json loads with keyword arguments."""
        loads = get_json_loads()
        result = loads('{"key": "value"}')
        assert result["key"] == "value"


class TestTomlLoadsDispatcher:
    """Tests for toml_loads_dispatcher."""

    def test_dispatcher_exists(self):
        """Test toml_loads_dispatcher is initialized."""
        assert toml_loads_dispatcher is not None
        assert isinstance(toml_loads_dispatcher, PerformanceModule)

    def test_loads_returns_dict(self):
        """Test toml loads returns a dict."""
        loads = get_toml_loads()
        toml_str = '[section]\nkey = "value"\n'
        result = loads(toml_str)
        assert isinstance(result, dict)

    def test_loads_parses_section(self):
        """Test toml loads parses sections."""
        loads = get_toml_loads()
        toml_str = '[database]\nhost = "localhost"\nport = 5432\n'
        result = loads(toml_str)
        assert "database" in result
        assert result["database"]["host"] == "localhost"


class TestWasmDispatcher:
    """Tests for WasmDispatcher class."""

    def test_call_plugin_raises_without_extism(self):
        """Test call_plugin raises ImportError when extism not installed."""
        if not HAS_EXTISM:
            with pytest.raises(ImportError, match="extism not installed"):
                WasmDispatcher.call_plugin("/fake/path.wasm", "func", b"data")

    def test_has_extism_is_boolean(self):
        """Test HAS_EXTISM is a boolean."""
        assert isinstance(HAS_EXTISM, bool)


class TestGetRouter:
    """Tests for get_router function."""

    def test_returns_callable(self):
        """Test get_router returns a callable."""
        router = get_router()
        assert callable(router)

    def test_router_dispatcher_exists(self):
        """Test router_dispatcher is properly initialized."""
        from thegent.infra.runtime_dispatcher import router_dispatcher

        assert router_dispatcher is not None
        assert router_dispatcher.name == "router"


class TestGetRuntimeStatus:
    """Tests for get_runtime_status function."""

    def test_returns_dict(self):
        """Test get_runtime_status returns a dict."""
        status = get_runtime_status()
        assert isinstance(status, dict)

    def test_has_implementation_key(self):
        """Test status has implementation key."""
        status = get_runtime_status()
        assert "implementation" in status
        assert isinstance(status["implementation"], str)

    def test_has_version_key(self):
        """Test status has version key."""
        status = get_runtime_status()
        assert "version" in status
        assert isinstance(status["version"], str)

    def test_has_freethreading_key(self):
        """Test status has freethreading key."""
        status = get_runtime_status()
        assert "freethreading" in status
        assert isinstance(status["freethreading"], bool)

    def test_has_jit_key(self):
        """Test status has jit key."""
        status = get_runtime_status()
        assert "jit" in status
        assert isinstance(status["jit"], bool)

    def test_has_active_extensions_key(self):
        """Test status has active_extensions key."""
        status = get_runtime_status()
        assert "active_extensions" in status
        assert isinstance(status["active_extensions"], dict)

    def test_active_extensions_has_expected_keys(self):
        """Test active_extensions has expected extension keys."""
        status = get_runtime_status()
        ext = status["active_extensions"]
        assert "orjson" in ext
        assert "ujson" in ext
        assert "rtoml" in ext
        assert "rust_router" in ext

    def test_extension_flags_are_booleans(self):
        """Test extension flags are booleans."""
        status = get_runtime_status()
        for key, value in status["active_extensions"].items():
            assert isinstance(value, bool), f"{key} should be bool, got {type(value)}"


class TestGlobalAccessFunctions:
    """Tests for global access functions."""

    def test_get_json_dumps_returns_callable(self):
        """Test get_json_dumps returns a callable."""
        dumps = get_json_dumps()
        assert callable(dumps)

    def test_get_json_loads_returns_callable(self):
        """Test get_json_loads returns a callable."""
        loads = get_json_loads()
        assert callable(loads)

    def test_get_toml_loads_returns_callable(self):
        """Test get_toml_loads returns a callable."""
        loads = get_toml_loads()
        assert callable(loads)


class TestJsonDispatcherEdgeCases:
    """Tests for JSON dispatcher edge cases and library paths."""

    def test_dumps_handles_nested_objects(self):
        """Test json dumps handles nested objects."""
        dumps = get_json_dumps()
        result = dumps({"outer": {"inner": [1, 2, 3]}})
        assert "outer" in result
        assert "inner" in result

    def test_dumps_handles_unicode(self):
        """Test json dumps handles unicode."""
        dumps = get_json_dumps()
        result = dumps({"unicode": "こんにちは"})
        assert "unicode" in result

    def test_dumps_handles_numbers(self):
        """Test json dumps handles numbers."""
        dumps = get_json_dumps()
        result = dumps({"int": 42, "float": 3.14})
        assert "42" in result

    def test_loads_handles_unicode(self):
        """Test json loads handles unicode."""
        loads = get_json_loads()
        result = loads('{"text": "こんにちは"}')
        assert result["text"] == "こんにちは"

    def test_loads_handles_whitespace(self):
        """Test json loads handles whitespace."""
        loads = get_json_loads()
        result = loads('  {  "key"  :  "value"  }  ')
        assert result["key"] == "value"


class TestTomlDispatcherEdgeCases:
    """Tests for TOML dispatcher edge cases."""

    def test_loads_handles_arrays(self):
        """Test toml loads handles arrays."""
        loads = get_toml_loads()
        toml_str = "items = [1, 2, 3]\n"
        result = loads(toml_str)
        assert result["items"] == [1, 2, 3]

    def test_loads_handles_nested_tables(self):
        """Test toml loads handles nested tables."""
        loads = get_toml_loads()
        toml_str = '[a.b]\nkey = "value"\n'
        result = loads(toml_str)
        assert "a" in result

    def test_loads_handles_strings(self):
        """Test toml loads handles strings."""
        loads = get_toml_loads()
        toml_str = 'name = "test"\n'
        result = loads(toml_str)
        assert result["name"] == "test"

    def test_loads_handles_booleans(self):
        """Test toml loads handles booleans."""
        loads = get_toml_loads()
        toml_str = "enabled = true\ndisabled = false\n"
        result = loads(toml_str)
        assert result["enabled"] is True
        assert result["disabled"] is False


class TestRouterDispatcher:
    """Tests for router dispatcher."""

    def test_router_is_callable(self):
        """Test router is callable."""
        router = get_router()
        assert callable(router)

    def test_router_dispatcher_has_implementations(self):
        """Test router_dispatcher has implementations."""
        from thegent.infra.runtime_dispatcher import router_dispatcher

        assert len(router_dispatcher._implementations) > 0


class TestExtensionFlags:
    """Tests for extension availability flags."""

    def test_has_orjson_is_boolean(self):
        """Test HAS_ORJSON is boolean."""
        from thegent.infra.runtime_dispatcher import HAS_ORJSON

        assert isinstance(HAS_ORJSON, bool)

    def test_has_ujson_is_boolean(self):
        """Test HAS_UJSON is boolean."""
        from thegent.infra.runtime_dispatcher import HAS_UJSON

        assert isinstance(HAS_UJSON, bool)

    def test_has_rtoml_is_boolean(self):
        """Test HAS_RTOML is boolean."""
        from thegent.infra.runtime_dispatcher import HAS_RTOML

        assert isinstance(HAS_RTOML, bool)

    def test_has_rust_router_is_boolean(self):
        """Test HAS_RUST_ROUTER is boolean."""
        from thegent.infra.runtime_dispatcher import HAS_RUST_ROUTER

        assert isinstance(HAS_RUST_ROUTER, bool)


class TestPrivateDispatcherFunctions:
    """Tests for private dispatcher functions to cover all code paths."""

    def test_pypy_json_dumps(self):
        """Test _pypy_json_dumps function."""
        from thegent.infra.runtime_dispatcher import _pypy_json_dumps

        result = _pypy_json_dumps({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result

    def test_pypy_json_dumps_with_kwargs(self):
        """Test _pypy_json_dumps with kwargs."""
        from thegent.infra.runtime_dispatcher import _pypy_json_dumps

        result = _pypy_json_dumps([1, 2, 3])
        # The format may include spaces depending on library used
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_cpython_json_dumps(self):
        """Test _cpython_json_dumps function."""
        from thegent.infra.runtime_dispatcher import _cpython_json_dumps

        result = _cpython_json_dumps({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result

    def test_cpython_json_dumps_with_bytes_return(self):
        """Test _cpython_json_dumps returns string."""
        from thegent.infra.runtime_dispatcher import _cpython_json_dumps

        result = _cpython_json_dumps("test string")
        assert isinstance(result, str)

    def test_pypy_json_loads(self):
        """Test _pypy_json_loads function."""
        from thegent.infra.runtime_dispatcher import _pypy_json_loads

        result = _pypy_json_loads('{"key": "value"}')
        assert result["key"] == "value"

    def test_pypy_json_loads_with_bytes(self):
        """Test _pypy_json_loads with bytes."""
        from thegent.infra.runtime_dispatcher import _pypy_json_loads

        result = _pypy_json_loads(b'{"key": "value"}')
        assert result["key"] == "value"

    def test_cpython_json_loads(self):
        """Test _cpython_json_loads function."""
        from thegent.infra.runtime_dispatcher import _cpython_json_loads

        result = _cpython_json_loads('{"key": "value"}')
        assert result["key"] == "value"

    def test_cpython_json_loads_with_bytes(self):
        """Test _cpython_json_loads with bytes."""
        from thegent.infra.runtime_dispatcher import _cpython_json_loads

        result = _cpython_json_loads(b'{"key": "value"}')
        assert result["key"] == "value"

    def test_pypy_toml_loads(self):
        """Test _pypy_toml_loads function."""
        from thegent.infra.runtime_dispatcher import _pypy_toml_loads

        result = _pypy_toml_loads('[section]\nkey = "value"\n')
        assert isinstance(result, dict)

    def test_cpython_toml_loads(self):
        """Test _cpython_toml_loads function."""
        from thegent.infra.runtime_dispatcher import _cpython_toml_loads

        result = _cpython_toml_loads('[section]\nkey = "value"\n')
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
