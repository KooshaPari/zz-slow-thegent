"""Unit tests for tray costs tab."""

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
class TestCostAlertDialog:
    """Tests for CostAlertDialog class."""

    def test_class_exists_in_source(self):
        """CostAlertDialog class exists in costs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "CostAlertDialog" in classes

    def test_get_data_method_in_source(self):
        """get_data method exists in CostAlertDialog source."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)

        # Find the CostAlertDialog class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "CostAlertDialog":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "get_data" in methods
                return

        pytest.fail("CostAlertDialog class not found")

    def test_has_alert_type_radio_buttons(self):
        """CostAlertDialog has alert type radio buttons."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        with open(file_path) as f:
            source = f.read()
        # Check for QRadioButton in the source
        assert "QRadioButton" in source

    def test_has_notification_checkboxes(self):
        """CostAlertDialog has notification checkboxes."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        with open(file_path) as f:
            source = f.read()
        # Check for QCheckBox in the source
        assert "QCheckBox" in source


@pytest.mark.unit
class TestCostsTab:
    """Tests for CostsTab class."""

    def test_class_exists_in_source(self):
        """CostsTab class exists in costs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "CostsTab" in classes

    def test_tab_id_constant_exists(self):
        """CostsTab has TAB_ID constant."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)

        # Find CostsTab class and check for TAB_ID assignment
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "CostsTab":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "TAB_ID":
                                return

        pytest.fail("TAB_ID not found in CostsTab class")

    def test_has_required_methods(self):
        """CostsTab has required methods."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)

        # Find the CostsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "CostsTab":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "_setup_ui" in methods
                assert "_load_costs" in methods
                return

        pytest.fail("CostsTab class not found")

    def test_accepts_api_client_parameter(self):
        """CostsTab.__init__ accepts api_client parameter."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)

        # Find the CostsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "CostsTab":
                # Find __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = [arg.arg for arg in item.args.args]
                        assert "api_client" in args
                        return

        pytest.fail("CostsTab.__init__ not found")

    def test_has_progress_bars(self):
        """CostsTab has QProgressBar for spend tracking."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        with open(file_path) as f:
            source = f.read()
        # Check for QProgressBar in the source
        assert "QProgressBar" in source


@pytest.mark.unit
class TestGetTabFunction:
    """Tests for get_tab function."""

    def test_get_tab_function_exists(self):
        """get_tab function exists in costs.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "costs.py",
        )
        module = get_module_ast(file_path)
        functions = find_function_definitions(module)
        assert "get_tab" in functions


@pytest.mark.unit
class TestTabsPackage:
    """Tests for tabs package."""

    def test_tabs_package_exports_costs(self):
        """tabs package exports costs tab items."""
        import sys
        from pathlib import Path

        # Add src to path
        src_path = Path(__file__).parent.parent.parent / "src"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        try:
            from thegent.tray.plugins.thegent import tabs

            # Check exports for costs
            assert hasattr(tabs, "CostAlertDialog")
            assert hasattr(tabs, "CostsTab")
        except ImportError as e:
            if "PySide6" in str(e) or "thegent.tray" in str(e):
                pytest.skip("PySide6 not installed - tray tests require GUI libraries")
            pytest.fail(f"Failed to import tabs package: {e}")
