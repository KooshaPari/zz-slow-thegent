import pytest

from thegent.docgen.api_typescript import TypeScriptAPIGenerator


@pytest.fixture
def generator():
    return TypeScriptAPIGenerator()


def test_parse_typescript_file(generator, tmp_path):
    ts_content = """
/**
 * A user object.
 */
export interface User {
  id: string;
  name: string;
}

/**
 * App configuration.
 */
type Config = {
  apiUrl: string;
};

/**
 * Main application class.
 */
class App<T> extends BaseApp {
  start() {}
}

/**
 * Possible status values.
 */
enum Status {
  Active,
  Inactive
}

/**
 * Calculate the sum of two numbers.
 * @param a First number
 * @param b Second number
 */
export async function add(a: number, b: number): Promise<number> {
  return a + b;
}

/**
 * Multiply two numbers.
 */
const multiply = (a: number, b: number): number => a * b;
"""
    file_path = tmp_path / "test.ts"
    file_path.write_text(ts_content)

    info = generator.parse_file(file_path)

    assert info["interfaces"][0]["name"] == "User"
    assert "A user object" in info["interfaces"][0]["docstring"]

    assert info["types"][0]["name"] == "Config"
    assert "App configuration" in info["types"][0]["docstring"]

    assert info["classes"][0]["name"] == "App"
    assert "Main application class" in info["classes"][0]["docstring"]

    assert info["enums"][0]["name"] == "Status"
    assert "Possible status values" in info["enums"][0]["docstring"]

    assert info["functions"][0]["name"] == "add"
    assert info["functions"][0]["args"] == ["a", "b"]
    assert "Calculate the sum" in info["functions"][0]["docstring"]

    assert info["functions"][1]["name"] == "multiply"
    assert info["functions"][1]["args"] == ["a", "b"]
    assert "Multiply two numbers" in info["functions"][1]["docstring"]


def test_generate_docs(generator, tmp_path):
    ts_content = """
/**
 * Test interface
 */
interface TestInterface {}

/**
 * Test function
 */
function testFunc(a, b) {}
"""
    file_path = tmp_path / "test.ts"
    file_path.write_text(ts_content)
    info = generator.parse_file(file_path)

    docs = generator.generate_docs(info)

    assert "# test" in docs
    assert "## Interfaces" in docs
    assert "### TestInterface" in docs
    assert "Test interface" in docs
    assert "## Functions" in docs
    assert "### testFunc(a, b)" in docs
    assert "Test function" in docs
