from compiler import SOPCompiler


def test_compile_simple_graph():
    sop = {
        "nodes": [
            {"id": "n1", "type": "Predict", "config": {"command": "predict(x)"}},
            {"id": "n2", "type": "Generate", "config": {"command": "generate(y)"}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "Sequential"},
        ],
    }
    compiler = SOPCompiler()
    graph = compiler.compile(sop)
    assert len(graph.tasks) == 2
    n2 = graph.get_task("n2")
    assert n2 is not None
    assert n2.dependencies == ["n1"]
    assert n2.agent_role == "generator"


def test_topological_order():
    sop = {
        "nodes": [
            {"id": "a", "type": "Retrieve", "config": {}},
            {"id": "b", "type": "Predict", "config": {}},
            {"id": "c", "type": "Aggregate", "config": {}},
        ],
        "edges": [
            {"source": "a", "target": "b", "type": "Sequential"},
            {"source": "b", "target": "c", "type": "Sequential"},
        ],
    }
    graph = SOPCompiler().compile(sop)
    order = graph.topological_order()
    ids = [t.id for t in order]
    assert ids == ["a", "b", "c"]
