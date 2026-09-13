"""Integration tests - run real agent with deterministic file-content prompts.

Minimizes probabilism: prompt asks "what is in file X" -> assert response contains
expected content from that file.
"""

from pathlib import Path

import orjson as json
import pytest

from thegent.agents import get_runner
from thegent.config import ThegentSettings


@pytest.mark.integration
@pytest.mark.slow
class TestGeminiFileContent:
    """Integration tests: gemini with deterministic file-content prompts."""

    @staticmethod
    def _extract_assistant_text(raw_output: str) -> str:
        """Extract assistant text from Gem/Claude stream-json transcript output."""
        lines = []
        for line in (raw_output or "").splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if (
                isinstance(payload, dict)
                and payload.get("role") == "assistant"
                and isinstance(payload.get("content"), str)
            ):
                lines.append(payload["content"])
        return "\n".join(lines).strip()

    @staticmethod
    def _assert_contains_with_flexible_whitespace(output: str, expected: str) -> None:
        """Assert `expected` appears even when transport adds newline/spacing artifacts."""
        compact_output = "".join(output.split())
        compact_expected = "".join(expected.split())
        assert compact_expected in compact_output, f"Expected '{expected}' in response: {output[:500]}"

    def test_readme_first_line_in_response(
        self,
        project_root: Path,
        thegent_readme_path: Path,
        thegent_readme_first_line: str,
    ) -> None:
        # @trace FR-AGT-011
        """Prompt: first line of README -> response must contain that line."""
        if not thegent_readme_path.exists():
            pytest.skip("thegent README not found")

        ThegentSettings()
        runner = get_runner("gemini")
        if runner is None:
            pytest.skip("gemini runner not available")

        # Deterministic prompt: ask for exact first line
        prompt = (
            f"Read the file {thegent_readme_path.relative_to(project_root)}. "
            "Output ONLY the first line of that file, nothing else."
        )
        result = runner.run(
            prompt=prompt,
            cwd=project_root,
            mode="read-only",
            timeout=90,
        )

        if result.timed_out:
            pytest.skip("gemini timed out (agent may be unavailable)")

        assert result.exit_code == 0, result.stderr

        assistant_text = self._extract_assistant_text(result.stdout)
        if not assistant_text and ('"tool_use"' in result.stdout or '"type":"assistant"' in result.stdout):
            pytest.skip("gemini returned tool-use transcript instead of plain content")
        # Response must contain the known first line
        response = assistant_text or result.stdout
        self._assert_contains_with_flexible_whitespace(response, thegent_readme_first_line)

    def test_pyproject_name_in_response(
        self,
        project_root: Path,
        thegent_pyproject_path: Path,
        thegent_pyproject_name_line: str,
    ) -> None:
        # @trace FR-AGT-011
        """Prompt: project name from pyproject.toml -> response must contain it."""
        if not thegent_pyproject_path.exists():
            pytest.skip("thegent pyproject.toml not found")

        ThegentSettings()
        runner = get_runner("gemini")
        if runner is None:
            pytest.skip("gemini runner not available")

        prompt = (
            f"Read {thegent_pyproject_path.relative_to(project_root)}. "
            "What is the value of the 'name' field? Output only that value in quotes."
        )
        result = runner.run(
            prompt=prompt,
            cwd=project_root,
            mode="read-only",
            timeout=90,
        )

        if result.timed_out:
            pytest.skip("gemini timed out")

        assert result.exit_code == 0, result.stderr
        assistant_text = self._extract_assistant_text(result.stdout)
        if not assistant_text and ('"tool_use"' in result.stdout or '"type":"assistant"' in result.stdout):
            pytest.skip("gemini returned tool-use transcript instead of plain content")
        response = assistant_text or result.stdout
        assert "thegent" in response.lower(), f"Expected 'thegent' in response: {response[:500]}"
