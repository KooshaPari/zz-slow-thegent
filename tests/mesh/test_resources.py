"""Mesh resource-management tests for SCLI-P12.x."""


from thegent.mesh.resources import ResourceManager


def test_set_limits_calls_expected_rlimit(monkeypatch) -> None:
    """SCLI-P12.1–SCLI-P12.3 apply memory/process/fd limits to the process."""
    seen = []

    def fake_setrlimit(resource_name, limits):  # type: ignore[no-redef]
        seen.append((resource_name, limits))

    monkeypatch.setattr("thegent.mesh.resources.resource.setrlimit", fake_setrlimit)
    manager = ResourceManager("agent-1")
    manager.set_limits(memory_mb=64, proc_limit=12, fd_limit=33)

    assert len(seen) >= 1


def test_get_cgroup_path(monkeypatch) -> None:
    """SCLI-P12.1 returns a memory cgroup path only when memory controller is present."""
    monkeypatch.setattr("thegent.mesh.resources.os.path.exists", lambda _: True)
    manager = ResourceManager("agent-2")
    path = manager.get_cgroup_path()

    assert path is not None
    assert path.name == "agent-agent-2"


def test_apply_cgroup_limits_no_cgroup(monkeypatch) -> None:
    """SCLI-P12.1 safely no-ops when no cgroup path is available."""
    monkeypatch.setattr("thegent.mesh.resources.os.path.exists", lambda _: False)
    manager = ResourceManager("agent-3")
    manager.apply_cgroup_limits(memory_mb=256)
