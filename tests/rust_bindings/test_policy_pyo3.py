"""Test PyO3 binding for thegent-policy Rust crate.

# @trace FR-GOV-001
"""

import pytest


def test_policy_engine_import():
    """Policy engine Rust module must be importable.

    Verify the PyO3-bound thegent_policy module can be imported.
    This test will skip if the module is not built.
    """
    try:
        import thegent_policy  # noqa: F401

        assert True
    except ImportError as e:
        pytest.skip(f"thegent_policy not built: {e}")


def test_policy_engine_instantiation():
    """Policy engine must instantiate from a config file path.

    Creates an instance and verifies basic initialization.
    """
    try:
        import tempfile
        from pathlib import Path

        from thegent_policy import PolicyEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "policy.toml"
            config_path.write_text("""
version = "1.0"

[[policies]]
id = "cost-governance"
category = "cost"
rules = ["cost-1"]
enabled = true
""")
            engine = PolicyEngine(str(config_path))
            assert engine is not None
    except ImportError as e:
        pytest.skip(f"thegent_policy not built: {e}")


def test_cost_enforcer_instantiation():
    """Cost enforcer must instantiate with a daily limit.

    Creates an enforcer instance and verifies methods are callable.
    """
    try:
        from thegent_policy import CostEnforcer

        enforcer = CostEnforcer(10.0)
        assert enforcer is not None
        remaining = enforcer.remaining()
        assert remaining == 10.0
    except ImportError as e:
        pytest.skip(f"thegent_policy not built: {e}")


def test_cost_enforcer_spending():
    """Cost enforcer must track spending correctly.

    Verifies can_spend() and remaining() methods.
    """
    try:
        from thegent_policy import CostEnforcer

        enforcer = CostEnforcer(10.0)
        assert enforcer.can_spend(5.0)
        assert enforcer.remaining() == 10.0
    except ImportError as e:
        pytest.skip(f"thegent_policy not built: {e}")
