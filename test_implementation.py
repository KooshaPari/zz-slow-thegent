import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("src").resolve()))

from thegent.routing.tool_router import ToolRouter

from thegent.infra.sandbox import WasmSandbox


def test_tool_router():
    router = ToolRouter(registry_path=Path("test_tools_registry.json"))

    # Test routing
    prompt = "I need to research some new Zsh plugins and lint my code."
    relevant = router.route(prompt)
    for _tool in relevant:
        pass

    # Test injection
    router.get_tool_prompt_injection(prompt)

    # Clean up
    registry_path = Path("test_tools_registry.json")
    if registry_path.exists():
        registry_path.unlink()


def test_wasm_sandbox():
    WasmSandbox(sandbox_id="test-sandbox")

    # Note: Real Wasm execution requires a .wasm file and extism installed.
    # This just tests the class instantiation and interface.


if __name__ == "__main__":
    test_tool_router()
    test_wasm_sandbox()
