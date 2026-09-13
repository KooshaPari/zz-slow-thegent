from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    id: str
    command: str
    dependencies: list[str] = field(default_factory=list)
    agent_role: str = "default"


@dataclass
class TaskGraph:
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Task | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def topological_order(self) -> list[Task]:
        visited = set()
        order = []

        def visit(tid: str) -> None:
            if tid in visited:
                return
            visited.add(tid)
            task = self.get_task(tid)
            if task:
                for dep in task.dependencies:
                    visit(dep)
                order.append(task)

        for t in self.tasks:
            visit(t.id)
        return order


class SOPCompiler:
    """Compile a Standard Operating Procedure (SOP) graph into a thegent task graph."""

    NODE_ROLE_MAP = {
        "Predict": "predictor",
        "Retrieve": "retriever",
        "Generate": "generator",
        "Evaluate": "evaluator",
        "Aggregate": "aggregator",
    }

    def compile(self, sop_graph: dict[str, Any]) -> TaskGraph:
        """Compile an SOP graph into a TaskGraph.

        Args:
            sop_graph: A dict representation with keys:
                - nodes: List of dicts with keys id, type, config
                - edges: List of dicts with keys source, target, type
        Returns:
            A TaskGraph containing compiled Task objects.
        """
        task_graph = TaskGraph()
        nodes = sop_graph.get("nodes", [])
        edges = sop_graph.get("edges", [])

        node_map: dict[str, dict[str, Any]] = {}
        for node in nodes:
            nid = node.get("id", f"node_{len(node_map)}")
            node_map[nid] = node

        deps: dict[str, list[str]] = {n["id"]: [] for n in nodes}
        for edge in edges:
            etype = edge.get("type", "Sequential")
            source = edge.get("source")
            target = edge.get("target")
            if etype in ("Sequential", "Conditional"):
                if target and source:
                    deps[target].append(source)
            elif etype == "Parallel":
                pass

        for node in nodes:
            nid = node.get("id")
            ntype = node.get("type", "Predict")
            config = node.get("config", {})
            command = config.get("command", f"{ntype.lower()}({nid})")
            role = self.NODE_ROLE_MAP.get(ntype, "default")
            task = Task(
                id=nid,
                command=command,
                dependencies=deps.get(nid, []),
                agent_role=role,
            )
            task_graph.add_task(task)

        return task_graph
