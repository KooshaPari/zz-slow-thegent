from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def test_bridge_python_stub_loads() -> None:
    stub_path = Path(__file__).resolve().parents[1] / "types" / "bridge.py"
    spec = importlib.util.spec_from_file_location("bridge_stub", stub_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Python 3.14 dataclasses may inspect sys.modules during class evaluation.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert hasattr(module, "ExecutionRequest")
    assert hasattr(module, "ExecutionResponse")
    assert hasattr(module, "ProviderAdapter")
    assert hasattr(module, "MetaproviderAdapter")
