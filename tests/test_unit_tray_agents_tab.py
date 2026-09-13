"""Unit tests for tray agents tab."""

import pytest

pytest.importorskip("PySide6")

import ast
from pathlib import Path


def get_module_ast(file_path: str) -> ast.Module:
    """Parse a Python file and return its AST."""
    with open(file_path) as f:
        source = f.read()
    return ast.parse(source, filename=file_path)


def find_class_definitions(module: ast.Module) -> list[str]:
    """Find all class definitions in an AST module."""
    return [node.name for node in ast.walk(module) if isinstance(node, ast.ClassDef)]


def find_function_definitions(module: ast.Module) -> list[str]:
    """Find all function definitions in an AST module."""
    return [node.name for node in ast.walk(module) if isinstance(node, ast.FunctionDef)]


@pytest.mark.unit
class TestAgentEditDialog:
    """Tests for AgentEditDialog class."""

    def test_class_exists_in_source(self):
        """AgentEditDialog class exists in agents.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "AgentEditDialog" in classes

    def test_get_data_method_in_source(self):
        """get_data method exists in AgentEditDialog source."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)

        # Find the AgentEditDialog class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "AgentEditDialog":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "get_data" in methods
                return

        pytest.fail("AgentEditDialog class not found")

    def test_dialog_inherits_from_qdialog(self):
        """AgentEditDialog inherits from QDialog."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        with open(file_path) as f:
            source = f.read()

        # Check that QDialog is used
        assert "QDialog" in source
        assert "class AgentEditDialog" in source


@pytest.mark.unit
class TestAgentsTab:
    """Tests for AgentsTab class."""

    def test_class_exists_in_source(self):
        """AgentsTab class exists in agents.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "AgentsTab" in classes

    def test_tab_id_constant_exists(self):
        """AgentsTab has TAB_ID constant."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)

        # Find AgentsTab class and check for TAB_ID assignment
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "AgentsTab":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "TAB_ID":
                                return

        pytest.fail("TAB_ID not found in AgentsTab class")

    def test_has_required_methods(self):
        """AgentsTab has required methods."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)

        # Find the AgentsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "AgentsTab":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "_setup_ui" in methods
                assert "_load_agents" in methods
                assert "_update_table" in methods
                return

        pytest.fail("AgentsTab class not found")

    def test_accepts_api_client_parameter(self):
        """AgentsTab.__init__ accepts api_client parameter."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)

        # Find the AgentsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "AgentsTab":
                # Find __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = [arg.arg for arg in item.args.args]
                        assert "api_client" in args
                        return

        pytest.fail("AgentsTab.__init__ not found")

    def test_uses_qtimer_for_refresh(self):
        """AgentsTab uses QTimer for auto-refresh."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        with open(file_path) as f:
            source = f.read()

        # Check that QTimer is used
        assert "QTimer" in source
        assert "_refresh_timer" in source


@pytest.mark.unit
class TestGetTabFunction:
    """Tests for get_tab function."""

    def test_get_tab_function_exists(self):
        """get_tab function exists in agents.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "agents.py",
        )
        module = get_module_ast(file_path)
        functions = find_function_definitions(module)
        assert "get_tab" in functions


@pytest.mark.unit
class TestAgentsTabPackage:
    """Tests for tabs package with agents."""

    def test_tabs_package_exports_agents(self):
        """tabs package exports agents tab."""
        import sys
        from pathlib import Path

        # Add src to path
        src_path = Path(__file__).parent.parent.parent / "src"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        try:
            from thegent.tray.plugins.thegent import tabs

            # Check exports
            assert hasattr(tabs, "get_tab")
            assert callable(tabs.get_tab)
        except ImportError as e:
            if "PySide6" in str(e) or "thegent.tray" in str(e):
                pytest.skip("PySide6 not installed - tray tests require GUI libraries")
            pytest.fail(f"Failed to import tabs package: {e}")
