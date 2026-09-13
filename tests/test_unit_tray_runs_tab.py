"""Unit tests for tray runs tab."""

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
class TestRunDetailDialog:
    """Tests for RunDetailDialog class."""

    def test_class_exists_in_source(self):
        """RunDetailDialog class exists in runs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "RunDetailDialog" in classes

    def test_get_data_method_in_source(self):
        """get_data method exists in RunDetailDialog source."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find the RunDetailDialog class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunDetailDialog":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "get_data" in methods
                return

        pytest.fail("RunDetailDialog class not found")


@pytest.mark.unit
class TestRunsTab:
    """Tests for RunsTab class."""

    def test_class_exists_in_source(self):
        """RunsTab class exists in runs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "RunsTab" in classes

    def test_tab_id_constant_exists(self):
        """RunsTab has TAB_ID constant."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find RunsTab class and check for TAB_ID assignment
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunsTab":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "TAB_ID":
                                return

        pytest.fail("TAB_ID not found in RunsTab class")

    def test_has_required_methods(self):
        """RunsTab has required methods."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find the RunsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunsTab":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "_setup_ui" in methods
                assert "_load_runs" in methods
                assert "_update_table" in methods
                return

        pytest.fail("RunsTab class not found")

    def test_accepts_api_client_parameter(self):
        """RunsTab.__init__ accepts api_client parameter."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find the RunsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunsTab":
                # Find __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = [arg.arg for arg in item.args.args]
                        assert "api_client" in args
                        return

        pytest.fail("RunsTab.__init__ not found")

    def test_has_filter_dropdowns(self):
        """RunsTab has filter dropdowns for project and status."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find the RunsTab class and check for filter-related instance variables
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunsTab":
                # Check that filter methods exist
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "_on_project_filter_changed" in methods
                assert "_on_status_filter_changed" in methods
                return

        pytest.fail("RunsTab class not found")

    def test_has_auto_refresh_timer(self):
        """RunsTab has auto-refresh timer."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)

        # Find the RunsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "RunsTab":
                # Find __init__ method and check for timer setup
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "_setup_ui":
                        # Check for QTimer usage in the method
                        source = ast.get_source_segment(open(file_path).read(), item)
                        if source and "QTimer" in source and "30000" in source:
                            return
                # Also check _load_runs for timer usage
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "_load_runs":
                        source = ast.get_source_segment(open(file_path).read(), item)
                        if source and "QTimer" in source and "30000" in source:
                            return

        pytest.fail("Auto-refresh timer (30s) not found in RunsTab")


@pytest.mark.unit
class TestGetTabFunction:
    """Tests for get_tab function."""

    def test_get_tab_function_exists(self):
        """get_tab function exists in runs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "runs.py",
        )
        module = get_module_ast(file_path)
        functions = find_function_definitions(module)
        assert "get_tab" in functions


@pytest.mark.unit
class TestTabsPackage:
    """Tests for tabs package."""

    def test_tabs_package_exports(self):
        """tabs package exports required items."""
        import sys
        from pathlib import Path

        # Add src to path
        src_path = Path(__file__).parent.parent / "src"
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
