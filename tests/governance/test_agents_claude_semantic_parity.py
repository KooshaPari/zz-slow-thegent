from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = ROOT / "AGENTS.md"
CLAUDE_PATH = ROOT / "CLAUDE.md"

SECTION_HEADERS = (
    "## ⛔ FORBIDDEN: Killing Agent or Terminal Processes",
    "## ⛔ FORBIDDEN: Fallbacks, Legacy Compatibility, and Silent Failures",
)


def _extract_section(text: str, header: str) -> str:
    marker = f"\n{header}\n"
    start = text.find(marker)
    if start == -1:
        if text.startswith(f"{header}\n"):
            start = 0
        else:
            raise AssertionError(f"Missing section header: {header}")
    else:
        start += 1

    next_h2 = text.find("\n## ", start + len(header) + 1)
    next_h1 = text.find("\n# ", start + len(header) + 1)
    candidates = [value for value in (next_h1, next_h2) if value != -1]
    if not candidates:
        return text[start:].strip()
    return text[start : min(candidates)].strip()


def _normalize_markdown(section: str) -> str:
    lines = []
    for line in section.splitlines():
        compact = re.sub(r"\s+", " ", line.strip())
        compact = compact.replace("**", "")
        compact = compact.replace("`", "")
        if compact:
            lines.append(compact)
    return "\n".join(lines)


def test_agents_and_claude_forbidden_sections_remain_semantically_aligned() -> None:
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")
    claude_text = CLAUDE_PATH.read_text(encoding="utf-8")

    for header in SECTION_HEADERS:
        agents_section = _extract_section(agents_text, header)
        claude_section = _extract_section(claude_text, header)
        assert _normalize_markdown(agents_section) == _normalize_markdown(claude_section), header
