"""Tool borrowing: export thegent MCP tools for use in other projects.

Enables other projects to "borrow" thegent MCP tools without copying code.
Generates MCP server config and CLAUDE.md snippets pointing at a running
thegent MCP server instance.

# @trace FR-TOOLS-BORROW-001
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from thegent.integrations.base import SerializableMixin

_log = logging.getLogger(__name__)

# Default MCP server connection details (mirrors ThegentSettings defaults)
_DEFAULT_MCP_HOST = "127.0.0.1"
_DEFAULT_MCP_PORT = 3847

# Canonical tool categories derived from TOOL_ICONS and mcp_server.py tool registrations
_TOOL_CATALOG: list[dict[str, Any]] = [
    # Session management
    {
        "name": "thegent_run",
        "description": "Run an agent task in the background or foreground",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_run",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_bg",
        "description": "Start a background agent session",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_bg",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_ps",
        "description": "List all background sessions and their statuses",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_ps",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_status",
        "description": "Get the status of a specific session",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_status",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_logs",
        "description": "Get logs from a background session",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_logs",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_stop",
        "description": "Stop a running session",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_stop",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_wait",
        "description": "Wait for a session to complete",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_wait",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_inspect",
        "description": "Inspect session details including metadata and contract",
        "category": "session",
        "module": "thegent.mcp.server",
        "function": "thegent_inspect",
        "requires": ["thegent"],
        "read_only": True,
    },
    # Planning and work stream
    {
        "name": "thegent_do_next",
        "description": "Get the next ready work item from the plan",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_do_next",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_plan_get_next",
        "description": "Get the next task from the plan without claiming it",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_plan_get_next",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_plan_progress",
        "description": "Show recent plan progress and completion statistics",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_plan_progress",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_plan_analyze",
        "description": "Analyze the plan for bottlenecks and critical paths",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_plan_analyze",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_plan_incorporate",
        "description": "Incorporate pending plan fragments into the main plan",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_plan_incorporate",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_plan_wait_next",
        "description": "Block until the next plan item is ready",
        "category": "planning",
        "module": "thegent.mcp.server",
        "function": "thegent_plan_wait_next",
        "requires": ["thegent"],
        "read_only": True,
    },
    # DAG management
    {
        "name": "thegent_dag_list",
        "description": "List all DAG tasks and their dependencies",
        "category": "dag",
        "module": "thegent.mcp.server",
        "function": "thegent_dag_list",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_dag_status",
        "description": "Get the current DAG execution status",
        "category": "dag",
        "module": "thegent.mcp.server",
        "function": "thegent_dag_status",
        "requires": ["thegent"],
        "read_only": True,
    },
    # Research tools
    {
        "name": "thegent_ddg_search",
        "description": "Search the web using DuckDuckGo",
        "category": "research",
        "module": "thegent.mcp.server",
        "function": "thegent_ddg_search",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_reddit_search",
        "description": "Search Reddit for discussions and community knowledge",
        "category": "research",
        "module": "thegent.mcp.server",
        "function": "thegent_reddit_search",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_scrape_url",
        "description": "Scrape content from a URL using Playwright",
        "category": "research",
        "module": "thegent.mcp.server",
        "function": "thegent_scrape_url",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_deep_research",
        "description": "Perform deep multi-source research on a topic",
        "category": "research",
        "module": "thegent.mcp.server",
        "function": "thegent_deep_research",
        "requires": ["thegent"],
        "read_only": True,
    },
    # Agent and model discovery
    {
        "name": "thegent_list_agents",
        "description": "List all available agent personas",
        "category": "discovery",
        "module": "thegent.mcp.server",
        "function": "thegent_list_agents",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_list_models",
        "description": "List all available models across providers",
        "category": "discovery",
        "module": "thegent.mcp.server",
        "function": "thegent_list_models",
        "requires": ["thegent"],
        "read_only": True,
    },
    # Inbox and queue
    {
        "name": "thegent_inbox_list",
        "description": "List pending inbox items for the current owner",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_inbox_list",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_inbox_wait",
        "description": "Wait for inbox items to arrive",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_inbox_wait",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_queue_list",
        "description": "List the task queue",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_queue_list",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_queue_add",
        "description": "Add a task to the queue",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_queue_add",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_queue_claim",
        "description": "Claim a task from the queue for processing",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_queue_claim",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_queue_done",
        "description": "Mark a claimed queue task as done",
        "category": "queue",
        "module": "thegent.mcp.server",
        "function": "thegent_queue_done",
        "requires": ["thegent"],
        "read_only": False,
    },
    # Escalation
    {
        "name": "thegent_escalate_list",
        "description": "List pending escalations",
        "category": "escalation",
        "module": "thegent.mcp.server",
        "function": "thegent_escalate_list",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_escalate_add",
        "description": "Add an escalation for human review",
        "category": "escalation",
        "module": "thegent.mcp.server",
        "function": "thegent_escalate_add",
        "requires": ["thegent"],
        "read_only": False,
    },
    # History and continuity
    {
        "name": "thegent_history",
        "description": "Show recent session execution history",
        "category": "history",
        "module": "thegent.mcp.server",
        "function": "thegent_history",
        "requires": ["thegent"],
        "read_only": True,
    },
    {
        "name": "thegent_continuity_snapshot",
        "description": "Take a continuity snapshot for session hand-off",
        "category": "history",
        "module": "thegent.mcp.server",
        "function": "thegent_continuity_snapshot",
        "requires": ["thegent"],
        "read_only": False,
    },
    # Free agent runner
    {
        "name": "thegent_free",
        "description": "Run a free-tier agent task (default agent provider)",
        "category": "execution",
        "module": "thegent.mcp.server",
        "function": "thegent_free",
        "requires": ["thegent"],
        "read_only": False,
    },
    {
        "name": "thegent_retry",
        "description": "Retry a failed session",
        "category": "execution",
        "module": "thegent.mcp.server",
        "function": "thegent_retry",
        "requires": ["thegent"],
        "read_only": False,
    },
]

# Map from category name to human-readable label for CLAUDE.md generation
_CATEGORY_LABELS: dict[str, str] = {
    "session": "Session Management",
    "planning": "Planning and Work Streams",
    "dag": "DAG Task Management",
    "research": "Web Research",
    "discovery": "Agent and Model Discovery",
    "queue": "Task Queue",
    "escalation": "Escalations",
    "history": "History and Continuity",
    "execution": "Agent Execution",
}


@dataclass
class ToolManifest(SerializableMixin):
    """Manifest entry for a single borrowable thegent MCP tool."""

    name: str
    description: str
    module: str
    function: str
    requires: list[str]
    category: str = "general"
    read_only: bool = True


@dataclass
class BorrowConfig:
    """Connection configuration for a running thegent MCP server."""

    host: str = _DEFAULT_MCP_HOST
    port: int = _DEFAULT_MCP_PORT

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"


class ToolBorrower:
    """Discovers and exports thegent MCP tools for cross-project use.

    Other projects call this class to:
    1. Enumerate available tools (``list_available_tools``).
    2. Build an MCP server config fragment (``export_tool_config``).
    3. Write an ``mcp.json`` file suitable for Claude Code (``generate_mcp_json``).
    4. Generate a CLAUDE.md snippet instructing Claude to use the tools
       (``generate_claude_md_snippet``).

    Example::

        borrower = ToolBorrower()
        borrower.generate_mcp_json(
            ["thegent_run", "thegent_ps", "thegent_ddg_search"],
            output_path=Path("my-other-project"),
        )
    """

    def __init__(self, config: BorrowConfig | None = None) -> None:
        self._config = config or BorrowConfig()
        self._catalog: list[ToolManifest] = [ToolManifest(**dict(entry.items())) for entry in _TOOL_CATALOG]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_available_tools(self) -> list[ToolManifest]:
        """Return all borrowable tool manifests, sorted by category then name."""
        return sorted(self._catalog, key=lambda t: (t.category, t.name))

    def list_available_tools_by_category(self) -> dict[str, list[ToolManifest]]:
        """Return tools grouped by category."""
        result: dict[str, list[ToolManifest]] = {}
        for manifest in self.list_available_tools():
            result.setdefault(manifest.category, []).append(manifest)
        return result

    def get_tool(self, name: str) -> ToolManifest | None:
        """Return the manifest for a tool by name, or None if not found."""
        for manifest in self._catalog:
            if manifest.name == name:
                return manifest
        return None

    def export_tool_config(self, tool_names: list[str]) -> dict[str, Any]:
        """Build an MCP server config dict for the requested tools.

        The returned dict is the ``mcpServers`` entry for a Claude Code
        ``mcp.json`` / ``.claude.json`` config.  It points at the running
        thegent HTTP+SSE MCP server; no tool filtering is applied at the
        config level because the server exposes all tools and MCP clients
        select the ones they need.

        Args:
            tool_names: List of tool names to document in the config metadata.
                Pass an empty list to include all tools.

        Returns:
            Dict with shape ``{"thegent": {"type": "http", "url": ..., ...}}``.

        Raises:
            ValueError: If any requested tool name is not found in the catalog.
        """
        unknown = [n for n in tool_names if self.get_tool(n) is None]
        if unknown:
            raise ValueError(f"Unknown tool(s): {', '.join(unknown)}")

        selected = tool_names or [m.name for m in self._catalog]
        manifests = [self.get_tool(n) for n in selected if self.get_tool(n) is not None]

        return {
            "thegent": {
                "type": "http",
                "url": self._config.url,
                "metadata": {
                    "description": "thegent MCP server — agent orchestration and governance platform",
                    "borrowed_tools": selected,
                    "tool_count": len(manifests),
                    "categories": sorted({m.category for m in manifests if m is not None}),
                },
            }
        }

    def generate_mcp_json(
        self,
        tool_names: list[str],
        output_path: Path,
        *,
        merge: bool = True,
    ) -> Path:
        """Write (or update) an ``mcp.json`` file in ``output_path``.

        The file uses Claude Code's ``mcpServers`` format.  When ``merge=True``
        and the file already exists, the ``thegent`` server entry is upserted
        without touching existing entries.

        Args:
            tool_names: Tools to document. Empty list borrows all tools.
            output_path: Directory where ``mcp.json`` will be written.
            merge: If True, merge with existing ``mcp.json``; otherwise overwrite.

        Returns:
            Absolute path to the written file.
        """
        output_dir = Path(output_path).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / "mcp.json"

        server_config = self.export_tool_config(tool_names)

        if merge and target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                _log.warning("Could not parse existing %s (%s); overwriting", target, exc)
                existing = {}
        else:
            existing = {}

        existing.setdefault("mcpServers", {})
        existing["mcpServers"].update(server_config)

        target.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")
        _log.info("Wrote mcp.json to %s", target)
        return target

    def generate_claude_md_snippet(self, tool_names: list[str]) -> str:
        """Generate a CLAUDE.md section instructing Claude to use thegent tools.

        Args:
            tool_names: Tools to document. Empty list includes all tools.

        Returns:
            Markdown string ready to paste into a project's CLAUDE.md.

        Raises:
            ValueError: If any requested tool name is not found in the catalog.
        """
        unknown = [n for n in tool_names if self.get_tool(n) is None]
        if unknown:
            raise ValueError(f"Unknown tool(s): {', '.join(unknown)}")

        selected_names = tool_names or [m.name for m in self._catalog]
        by_category: dict[str, list[ToolManifest]] = {}
        for name in selected_names:
            manifest = self.get_tool(name)
            if manifest is not None:
                by_category.setdefault(manifest.category, []).append(manifest)

        lines: list[str] = [
            "# thegent MCP Tools",
            "",
            f"This project borrows tools from the thegent MCP server running at `{self._config.url}`.",
            "These tools are available via the `thegent` MCP server configured in `mcp.json`.",
            "",
            "## Available Tools",
            "",
        ]

        for category, manifests in sorted(by_category.items()):
            label = _CATEGORY_LABELS.get(category, category.replace("_", " ").title())
            lines.append(f"### {label}")
            lines.append("")
            for m in sorted(manifests, key=lambda x: x.name):
                ro_tag = " _(read-only)_" if m.read_only else ""
                lines.append(f"- **`{m.name}`**{ro_tag}: {m.description}")
            lines.append("")

        lines += [
            "## Usage",
            "",
            "Ensure the thegent MCP server is running:",
            "",
            "```bash",
            "thegent serve  # or: uvicorn thegent.mcp.server:mcp --port 3847",
            "```",
            "",
            "Then use the tools directly in prompts or agent code.",
            "",
        ]

        return "\n".join(lines)

    def validate_server_reachable(self) -> bool:
        """Check whether the configured thegent MCP server is reachable.

        Performs a simple HTTP GET to the ``/health`` endpoint.

        Returns:
            True if the server responds with status 200, False otherwise.
        """
        import httpx

        try:
            resp = httpx.get(
                f"http://{self._config.host}:{self._config.port}/health",
                timeout=3.0,
            )
            return resp.status_code == 200
        except Exception as exc:
            _log.debug("thegent MCP server not reachable at %s: %s", self._config.url, exc)
            return False
