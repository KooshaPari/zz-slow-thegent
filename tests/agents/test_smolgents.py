"""Unit tests for the SmolGents base classes.

Coverage targets
----------------
* Tool dataclass — construction, __call__, repr
* SmolAgent — tool calling, delegation (parent -> child), memory recall
* AgentTree — registration, parent/child wiring, traversal, error cases

FR Traceability: FR-AGT-010 (SmolGents lightweight agent hierarchy)
"""

from __future__ import annotations

from typing import Any

import pytest

from thegent.agents.smolgents import AgentTree, SmolAgent, Tool
from thegent.agents.smolgents.base import SmolAgent as SmolAgentDirect
from thegent.agents.smolgents.tools import Tool as ToolDirect

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_echo_tool() -> Tool:
    """Tool that returns the task string unchanged."""
    return Tool(name="echo", description="Echo the input back", func=lambda task: task)


def make_upper_tool() -> Tool:
    """Tool that upper-cases the task string."""
    return Tool(name="upper", description="Upper-case the input", func=lambda task: task.upper())


def make_add_tool() -> Tool:
    """Tool that accepts (a, b) and returns a + b."""

    def add(a: int, b: int) -> int:
        return a + b

    return Tool(name="add", description="Add two integers", func=add)


def _call_counter() -> tuple[Tool, list[int]]:
    """Return a counting tool and a shared calls list."""
    calls: list[int] = [0]

    def counter(*_args: Any, **_kwargs: Any) -> int:
        calls[0] += 1
        return calls[0]

    return Tool(name="counter", description="Count calls", func=counter), calls


# ---------------------------------------------------------------------------
# Tool tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTool:
    """Tests for the Tool dataclass. @trace FR-AGT-010"""

    def test_construction(self) -> None:
        """Tool stores name, description, and func."""
        t = make_echo_tool()
        assert t.name == "echo"
        assert "Echo" in t.description
        assert callable(t.func)

    def test_call_delegates_to_func(self) -> None:
        """__call__ invokes the underlying func with passed args/kwargs."""
        t = make_add_tool()
        assert t(1, 2) == 3
        assert t(a=10, b=5) == 15

    def test_repr(self) -> None:
        """Tool repr includes name and description."""
        t = make_echo_tool()
        r = repr(t)
        assert "echo" in r
        assert "Echo" in r

    def test_metadata_default_empty(self) -> None:
        """Metadata defaults to empty dict."""
        t = make_echo_tool()
        assert t.metadata == {}

    def test_metadata_stored(self) -> None:
        """Custom metadata dict is preserved."""
        t = Tool(name="t", description="d", func=lambda: None, metadata={"version": 2})
        assert t.metadata["version"] == 2

    def test_counter_increments_on_each_call(self) -> None:
        """Calling a counter tool increments the internal call count."""
        tool, calls = _call_counter()
        tool("task")
        tool("task")
        assert calls[0] == 2

    def test_public_import_matches_direct(self) -> None:
        """Tool exported from package __init__ is the same class."""
        assert Tool is ToolDirect


# ---------------------------------------------------------------------------
# SmolAgent — tool calling
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSmolAgentToolCalling:
    """Tests for SmolAgent tool selection and execution. @trace FR-AGT-010"""

    def test_run_matches_tool_by_name(self) -> None:
        """run() selects the tool whose name appears in the task string."""
        agent = SmolAgent(name="a", tools=[make_echo_tool()])
        result = agent.run("please echo this message")
        assert result == "please echo this message"

    def test_run_no_matching_tool_returns_task(self) -> None:
        """run() returns the task string unchanged when no tool matches."""
        agent = SmolAgent(name="a", tools=[make_upper_tool()])
        result = agent.run("nothing relevant here")
        assert result == "nothing relevant here"

    def test_run_case_insensitive_matching(self) -> None:
        """Tool selection is case-insensitive."""
        agent = SmolAgent(name="a", tools=[make_echo_tool()])
        result = agent.run("ECHO this back please")
        assert result == "ECHO this back please"

    def test_run_returns_string(self) -> None:
        """run() always returns a str, even when the tool returns a non-str."""

        def numeric_func(_task: str) -> int:
            return 42

        agent = SmolAgent(name="a", tools=[Tool(name="num", description="d", func=numeric_func)])
        result = agent.run("num: return something")
        assert isinstance(result, str)
        assert result == "42"

    def test_get_tool_returns_registered_tool(self) -> None:
        """get_tool() returns the named tool or None."""
        t = make_echo_tool()
        agent = SmolAgent(name="a", tools=[t])
        assert agent.get_tool("echo") is t
        assert agent.get_tool("missing") is None

    def test_add_tool_extends_toolset(self) -> None:
        """add_tool() registers an additional tool at runtime."""
        agent = SmolAgent(name="a", tools=[])
        agent.add_tool(make_echo_tool())
        assert agent.get_tool("echo") is not None

    def test_add_tool_duplicate_raises(self) -> None:
        """add_tool() raises ValueError on duplicate name."""
        agent = SmolAgent(name="a", tools=[make_echo_tool()])
        with pytest.raises(ValueError, match="already registered"):
            agent.add_tool(make_echo_tool())

    def test_tools_property_returns_list(self) -> None:
        """tools property returns a list of Tool objects."""
        tools = [make_echo_tool(), make_upper_tool()]
        agent = SmolAgent(name="a", tools=tools)
        assert len(agent.tools) == 2

    def test_public_import_matches_direct(self) -> None:
        """SmolAgent exported from __init__ is the same class."""
        assert SmolAgent is SmolAgentDirect


# ---------------------------------------------------------------------------
# SmolAgent — delegation (parent -> child)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSmolAgentDelegation:
    """Tests for SmolAgent.delegate (parent -> child spawning). @trace FR-AGT-010"""

    def test_delegate_creates_child_with_same_tools(self) -> None:
        """delegate() spawns a child that shares the parent's tool set."""
        parent = SmolAgent(name="parent", tools=[make_echo_tool()])
        result = parent.delegate("echo subtask text")
        assert result == "echo subtask text"

    def test_delegate_appends_to_children(self) -> None:
        """After delegate(), the child appears in parent.children."""
        parent = SmolAgent(name="parent", tools=[make_echo_tool()])
        parent.delegate("echo first")
        parent.delegate("echo second")
        assert len(parent.children) == 2

    def test_delegate_child_parent_reference(self) -> None:
        """The child's parent property points back to the parent agent."""
        parent = SmolAgent(name="parent", tools=[make_echo_tool()])
        parent.delegate("echo child task")
        child = parent.children[0]
        assert child.parent is parent

    def test_delegate_child_name_includes_parent_name(self) -> None:
        """Spawned child name encodes the parent name for traceability."""
        parent = SmolAgent(name="orchestrator", tools=[make_echo_tool()])
        parent.delegate("echo something")
        child = parent.children[0]
        assert "orchestrator" in child.name

    def test_delegate_no_tool_returns_subtask(self) -> None:
        """delegate() with no matching tool returns the subtask string."""
        parent = SmolAgent(name="parent", tools=[])
        result = parent.delegate("unknown subtask")
        assert result == "unknown subtask"

    def test_delegate_result_is_string(self) -> None:
        """delegate() always returns a str."""
        parent = SmolAgent(name="parent", tools=[make_upper_tool()])
        result = parent.delegate("upper-case this")
        assert isinstance(result, str)

    def test_delegate_independent_memory(self) -> None:
        """Child agents start with empty, independent memory."""
        parent = SmolAgent(name="parent", tools=[make_echo_tool()])
        parent.remember("key", "parent-value")
        parent.delegate("echo subtask")
        child = parent.children[0]
        assert child.recall("key") is None

    def test_children_property_is_copy(self) -> None:
        """Mutating the returned children list does not alter internal state."""
        parent = SmolAgent(name="parent", tools=[make_echo_tool()])
        parent.delegate("echo one")
        external = parent.children
        external.clear()
        assert len(parent.children) == 1


# ---------------------------------------------------------------------------
# SmolAgent — memory
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSmolAgentMemory:
    """Tests for SmolAgent remember/recall. @trace FR-AGT-010"""

    def test_remember_and_recall(self) -> None:
        """Basic store/retrieve round-trip."""
        agent = SmolAgent(name="a", tools=[])
        agent.remember("lang", "python")
        assert agent.recall("lang") == "python"

    def test_recall_missing_key_returns_none(self) -> None:
        """recall() returns None for unknown keys."""
        agent = SmolAgent(name="a", tools=[])
        assert agent.recall("nonexistent") is None

    def test_remember_overwrites_existing(self) -> None:
        """Subsequent remember() calls overwrite the previous value."""
        agent = SmolAgent(name="a", tools=[])
        agent.remember("x", 1)
        agent.remember("x", 2)
        assert agent.recall("x") == 2

    def test_memory_property_returns_copy(self) -> None:
        """Mutating the returned memory dict does not affect internal state."""
        agent = SmolAgent(name="a", tools=[])
        agent.remember("k", "v")
        snap = agent.memory
        snap["k"] = "mutated"
        assert agent.recall("k") == "v"

    def test_memory_pre_populated_from_constructor(self) -> None:
        """Passing a pre-populated dict to the constructor seeds memory."""
        agent = SmolAgent(name="a", tools=[], memory={"seed": 42})
        assert agent.recall("seed") == 42

    def test_remember_various_types(self) -> None:
        """Memory can store any Python value, not just strings."""
        agent = SmolAgent(name="a", tools=[])
        agent.remember("list", [1, 2, 3])
        agent.remember("dict", {"nested": True})
        agent.remember("none", None)
        assert agent.recall("list") == [1, 2, 3]
        assert agent.recall("dict") == {"nested": True}
        assert agent.recall("none") is None


# ---------------------------------------------------------------------------
# SmolAgent — hierarchy wiring via set_parent
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSmolAgentSetParent:
    """Tests for SmolAgent.set_parent (used by AgentTree). @trace FR-AGT-010"""

    def test_set_parent_wires_parent_reference(self) -> None:
        """set_parent() updates the parent property."""
        root = SmolAgent(name="root", tools=[])
        child = SmolAgent(name="child", tools=[])
        child.set_parent(root)
        assert child.parent is root

    def test_default_parent_is_none(self) -> None:
        """Freshly constructed agent has no parent."""
        agent = SmolAgent(name="a", tools=[])
        assert agent.parent is None

    def test_parent_via_constructor(self) -> None:
        """Parent can also be supplied at construction time."""
        root = SmolAgent(name="root", tools=[])
        child = SmolAgent(name="child", tools=[], parent=root)
        assert child.parent is root


# ---------------------------------------------------------------------------
# AgentTree
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAgentTree:
    """Tests for AgentTree parent/child tracking. @trace FR-AGT-010"""

    def test_register_single_agent(self) -> None:
        """Registering one agent makes it retrievable."""
        tree = AgentTree()
        agent = SmolAgent(name="solo", tools=[])
        tree.register(agent)
        assert tree.get("solo") is agent

    def test_register_duplicate_raises(self) -> None:
        """Registering the same name twice raises ValueError."""
        tree = AgentTree()
        tree.register(SmolAgent(name="a", tools=[]))
        with pytest.raises(ValueError, match="already registered"):
            tree.register(SmolAgent(name="a", tools=[]))

    def test_register_with_unknown_parent_raises(self) -> None:
        """Registering with a non-existent parent_name raises ValueError."""
        tree = AgentTree()
        child = SmolAgent(name="child", tools=[])
        with pytest.raises(ValueError, match="Parent agent"):
            tree.register(child, parent_name="ghost")

    def test_parent_child_wiring(self) -> None:
        """After registering with a parent, get_parent/get_children work."""
        tree = AgentTree()
        parent = SmolAgent(name="parent", tools=[])
        child = SmolAgent(name="child", tools=[])
        tree.register(parent)
        tree.register(child, parent_name="parent")

        assert tree.get_parent("child") is parent
        assert child in tree.get_children("parent")

    def test_set_parent_called_on_registration(self) -> None:
        """Registering with parent_name updates the child's .parent property."""
        tree = AgentTree()
        parent = SmolAgent(name="parent", tools=[])
        child = SmolAgent(name="child", tools=[])
        tree.register(parent)
        tree.register(child, parent_name="parent")
        assert child.parent is parent

    def test_get_returns_none_for_missing(self) -> None:
        """get() returns None when name is not registered."""
        tree = AgentTree()
        assert tree.get("nobody") is None

    def test_get_parent_returns_none_for_root(self) -> None:
        """get_parent() returns None for a root (parentless) agent."""
        tree = AgentTree()
        tree.register(SmolAgent(name="root", tools=[]))
        assert tree.get_parent("root") is None

    def test_get_children_empty_for_leaf(self) -> None:
        """get_children() returns [] for an agent with no children."""
        tree = AgentTree()
        tree.register(SmolAgent(name="leaf", tools=[]))
        assert tree.get_children("leaf") == []

    def test_list_agents(self) -> None:
        """list_agents() returns all registered agents."""
        tree = AgentTree()
        a = SmolAgent(name="a", tools=[])
        b = SmolAgent(name="b", tools=[])
        tree.register(a)
        tree.register(b)
        agents = tree.list_agents()
        assert a in agents
        assert b in agents
        assert len(agents) == 2

    def test_len(self) -> None:
        """len(tree) equals the number of registered agents."""
        tree = AgentTree()
        assert len(tree) == 0
        tree.register(SmolAgent(name="x", tools=[]))
        assert len(tree) == 1

    def test_get_ancestors(self) -> None:
        """get_ancestors() walks up the chain to the root."""
        tree = AgentTree()
        root = SmolAgent(name="root", tools=[])
        mid = SmolAgent(name="mid", tools=[])
        leaf = SmolAgent(name="leaf", tools=[])
        tree.register(root)
        tree.register(mid, parent_name="root")
        tree.register(leaf, parent_name="mid")

        ancestors = tree.get_ancestors("leaf")
        assert ancestors[0] is mid
        assert ancestors[1] is root

    def test_get_ancestors_root_is_empty(self) -> None:
        """Root node has no ancestors."""
        tree = AgentTree()
        tree.register(SmolAgent(name="root", tools=[]))
        assert tree.get_ancestors("root") == []

    def test_get_descendants(self) -> None:
        """get_descendants() returns all nodes below the given agent."""
        tree = AgentTree()
        root = SmolAgent(name="root", tools=[])
        c1 = SmolAgent(name="c1", tools=[])
        c2 = SmolAgent(name="c2", tools=[])
        gc = SmolAgent(name="gc", tools=[])
        tree.register(root)
        tree.register(c1, parent_name="root")
        tree.register(c2, parent_name="root")
        tree.register(gc, parent_name="c1")

        descendants = tree.get_descendants("root")
        assert c1 in descendants
        assert c2 in descendants
        assert gc in descendants
        assert len(descendants) == 3

    def test_to_dict(self) -> None:
        """to_dict() returns agents list and edges."""
        tree = AgentTree()
        parent = SmolAgent(name="p", tools=[])
        child = SmolAgent(name="c", tools=[])
        tree.register(parent)
        tree.register(child, parent_name="p")

        d = tree.to_dict()
        assert "agents" in d
        assert "edges" in d
        assert "p" in d["agents"]
        assert "c" in d["agents"]
        assert {"child": "c", "parent": "p"} in d["edges"]

    def test_repr(self) -> None:
        """repr includes registered agent names."""
        tree = AgentTree()
        tree.register(SmolAgent(name="alpha", tools=[]))
        assert "alpha" in repr(tree)


# ---------------------------------------------------------------------------
# End-to-end: orchestrator -> specialist delegation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSmolGentsE2E:
    """End-to-end tests for the full SmolGents hierarchy. @trace FR-AGT-010"""

    def test_orchestrator_delegates_to_specialist(self) -> None:
        """Orchestrator delegates a subtask and specialist executes it."""
        specialist_tool = Tool(
            name="analyse",
            description="Analyse data",
            func=lambda task: f"analysis: {task}",
        )
        orchestrator = SmolAgent(name="orchestrator", tools=[specialist_tool])

        # The orchestrator runs the task itself (could also delegate)
        result = orchestrator.run("analyse the dataset")
        assert result.startswith("analysis:")

    def test_delegation_chain(self) -> None:
        """Two-level delegation: orchestrator -> child -> tool result."""
        tool = Tool(
            name="compute",
            description="Compute something",
            func=lambda task: "computed",
        )
        orchestrator = SmolAgent(name="orchestrator", tools=[tool])
        result = orchestrator.delegate("compute the answer")
        assert result == "computed"

    def test_memory_persists_across_runs(self) -> None:
        """Memory stored between calls to run() persists."""
        agent = SmolAgent(name="a", tools=[make_echo_tool()])
        agent.remember("session", "abc")
        agent.run("echo first")
        agent.run("echo second")
        assert agent.recall("session") == "abc"

    def test_tree_integration_with_delegation(self) -> None:
        """AgentTree tracks registered agents; delegate() creates ad-hoc children."""
        tree = AgentTree()
        tool = make_echo_tool()
        parent = SmolAgent(name="parent", tools=[tool])
        tree.register(parent)

        # Delegate creates a child but NOT via AgentTree.register —
        # the tree is for explicitly managed hierarchies; delegate() creates
        # ad-hoc children that live on parent._children.
        parent.delegate("echo task one")
        assert len(parent.children) == 1
        # The tree itself still only has the one registered agent
        assert len(tree) == 1

    def test_smolAgent_run_conforms_to_agentrunner_interface(self) -> None:
        """SmolAgent.run(task) returns str, matching AgentRunner output contract."""
        agent = SmolAgent(name="a", tools=[make_echo_tool()])
        result = agent.run("echo hello")
        assert isinstance(result, str)
