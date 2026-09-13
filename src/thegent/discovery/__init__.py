"""WP-4008: Discovery of external agents via heliosShield and process tree.

BKM-08 integration: ``scan_agent_processes`` now delegates to
``DiscoveryClient`` (crates/thegent-discovery) when the native binary is
available, falling back to the original psutil-based scan otherwise.
"""

import contextlib
import logging
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any

import orjson as json
import psutil
from pydantic import BaseModel, Field

_log = logging.getLogger(__name__)

__all__ = [
    "DiscoveredAgent",
    "_is_triggered_by_agent_process",
    "get_current_agent_id",
    "list_discovered_agents",
    "register_discovered_agent",
    "scan_agent_processes",
    "scan_harness_agents",
]

# BKM-08: lazy-loaded native discovery client (avoids import cost when unused)
_native_client: "Any | None" = None
_native_checked: bool = False


def _get_native_client() -> "Any | None":
    """Return the DiscoveryClient singleton, or None if unavailable."""
    global _native_client, _native_checked  # noqa: PLW0603
    if _native_checked:
        return _native_client
    _native_checked = True
    try:
        discovery_native = import_module("thegent.native.discovery_native")
        DiscoveryClient = discovery_native.DiscoveryClient

        _native_client = DiscoveryClient()
        if _native_client.is_native:
            _log.debug("BKM-08: thegent-discovery binary active")
        else:
            _log.debug("BKM-08: thegent-discovery binary absent; psutil fallback")
    except Exception as exc:
        _log.debug("BKM-08: could not initialise DiscoveryClient: %s", exc)
        _native_client = None
    return _native_client


class DiscoveredAgent(BaseModel):
    """Metadata for an agent discovered outside thegent's direct control."""

    pid: int
    ppid: int
    agent: str
    cwd: str
    discovered_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_seen_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    command: str | None = None
    args_preview: str | None = None
    tmux_pane: str | None = None
    session_id: str | None = None
    token_usage: dict | None = None
    mcp_errors: list[str] = Field(default_factory=list)


def get_current_agent_id() -> str:
    """Get unique ID for the current agent session."""
    import getpass
    import os

    # Check env vars first
    for var in ["THGENT_AGENT_ID", "AGENT_ID", "SESSION_ID"]:
        val = os.environ.get(var)
        if val:
            return val

    # Try to identify by parent process
    try:
        current = psutil.Process()
        parent = current.parent()
        if parent:
            parent_name = parent.name().lower()
            agent_names = {
                "thegent",
                "codex",
                "copilot",
                "claude",
                "cursor-agent",
                "opencode",
                "zen",
            }
            for agent in agent_names:
                if agent in parent_name:
                    return f"{agent}-{os.getpid()}"
    except Exception:
        pass

    # Fallback to user and PID
    try:
        user = getpass.getuser()
    except Exception:
        user = "unknown"
    return f"{user}-{os.getpid()}"


def register_discovered_agent(
    pid: int,
    ppid: int,
    agent: str,
    cwd: str,
    command: str | None = None,
    args_preview: str | None = None,
    session_dir: Path | None = None,
    session_id: str | None = None,
    token_usage: dict | None = None,
    mcp_errors: list[str] | None = None,
) -> Path:
    """Register or update a discovered agent in the session directory."""
    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    base_dir = session_dir or settings.session_dir.expanduser().resolve()
    discovery_dir = base_dir / "discovered"
    discovery_dir.mkdir(parents=True, exist_ok=True)

    # We use PPID as the primary key for the "session" of the agent
    # since most agents launch subcommands from a stable parent process.
    file_path = discovery_dir / f"ppid_{ppid}.json"

    agent_data: dict[str, Any]
    if file_path.exists():
        try:
            agent_data = json.loads(file_path.read_text(encoding="utf-8"))
            agent_data["last_seen_at"] = datetime.now(UTC).isoformat()
            if command:
                agent_data["command"] = command
            if args_preview:
                agent_data["args_preview"] = args_preview
            if agent and agent != "?":
                agent_data["agent"] = agent
        except Exception as e:
            _log.warning(f"Failed to read discovered agent file {file_path}: {e}")
            agent_data = DiscoveredAgent(
                pid=pid,
                ppid=ppid,
                agent=agent,
                cwd=cwd,
                command=command,
                args_preview=args_preview,
            ).model_dump()
    else:
        agent_data = DiscoveredAgent(
            pid=pid,
            ppid=ppid,
            agent=agent,
            cwd=cwd,
            command=command,
            args_preview=args_preview,
        ).model_dump()

    # Store new optional fields
    if session_id:
        agent_data["session_id"] = session_id
    if token_usage:
        agent_data["token_usage"] = token_usage
    if mcp_errors:
        agent_data["mcp_errors"] = mcp_errors

    # Try to find associated tmux pane
    from thegent.skills.terminal import list_tmux_panes

    panes = list_tmux_panes()
    for p in panes:
        # This is a heuristic: if the pane path matches the agent CWD
        # and the pane command matches the agent name or its PID is in the pane's process tree
        if p.path == cwd:
            agent_data["tmux_pane"] = p.pane_id
            break

    file_path.write_bytes(json.dumps(agent_data, option=json.OPT_INDENT_2))
    return file_path


def list_discovered_agents(session_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all currently active discovered agents."""
    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    base_dir = session_dir or settings.session_dir.expanduser().resolve()
    discovery_dir = base_dir / "discovered"

    if not discovery_dir.exists():
        return []

    agents = []
    for f in discovery_dir.glob("ppid_*.json"):
        _parse_agent_discovery_file(agents, f)

    return sorted(agents, key=lambda x: x.get("last_seen_at", ""), reverse=True)


def _parse_agent_discovery_file(agents: list[dict[str, Any]], f: Path) -> None:
    """Parse a single agent discovery file safely."""
    from thegent.infra.process_helpers import is_pid_running as _is_pid_running

    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        ppid = data.get("ppid")
        if ppid and _is_pid_running(ppid):
            agents.append(data)
        else:
            # Cleanup stale discovery files
            with contextlib.suppress(Exception):
                f.unlink()
    except Exception:
        pass


def _is_triggered_by_agent_process() -> bool:
    """Check if the current process was triggered by an agent process.

    This checks the process tree (parent processes) to see if any ancestor
    is a known agent process (thegent, codex, copilot, claude, etc.).

    Returns:
        True if triggered by an agent process, False otherwise.
    """
    try:
        current = psutil.Process()

        # Check current process name
        current_name = current.name().lower()
        agent_names = {
            "thegent",
            "codex",
            "copilot",
            "claude",
            "cursor-agent",
            "opencode",
            "zen",
        }
        if any(agent in current_name for agent in agent_names):
            return True

        # Check parent process tree
        parent = current.parent()
        max_depth = 10  # Limit depth to avoid infinite loops
        depth = 0

        while parent and depth < max_depth:
            res, parent = _check_parent_agent(parent, agent_names)
            if res:
                return True
            depth += 1

        return False
    except Exception as e:
        _log.debug(f"Error checking if triggered by agent process: {e}")
        return False


def _check_parent_agent(parent: psutil.Process | None, agent_names: set[str]) -> tuple[bool, psutil.Process | None]:
    """Check a single parent process for agent markers and return next parent."""
    if not parent:
        return False, None
    try:
        parent_name = parent.name().lower()
        if any(agent in parent_name for agent in agent_names):
            return True, None

        # Check if parent is in discovered agents
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        discovery_dir = settings.session_dir.expanduser().resolve() / "discovered"
        if discovery_dir.exists():
            ppid_file = discovery_dir / f"ppid_{parent.pid}.json"
            if ppid_file.exists():
                return True, None

        return False, parent.parent()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False, None


def scan_agent_processes(pattern: str | None = None) -> list[dict[str, Any]]:
    """BKM-08: Scan for agent processes, preferring the native binary.

    Uses ``thegent-discovery processes`` when the binary is available (single
    subprocess, structured JSON).  Falls back to the psutil scanner in
    ``infra/discovery_v2.py`` otherwise.

    Args:
        pattern: Optional regex to filter process names/cmdlines.

    Returns:
        List of process dicts with at minimum: ``pid``, ``name``, ``cmd``.
    """
    client = _get_native_client()
    if client is not None:
        try:
            return client.processes(pattern)
        except Exception as exc:
            _log.warning("BKM-08: native process scan failed, falling back: %s", exc)

    # Fallback to the psutil-based AgentScanner
    try:
        from thegent.infra.discovery_v2 import AgentScanner

        scanner = AgentScanner()
        return scanner.scan()
    except Exception as exc:
        _log.error("scan_agent_processes fallback failed: %s", exc)
        return []


def scan_harness_agents() -> list[dict[str, Any]]:
    """WP-11005: Scan heliosShield harness for active agent sessions."""
    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    harness_sessions_dir = Path(settings.harness_root) / "var" / "thegent" / "sessions"

    if not harness_sessions_dir.exists():
        return []

    agents = []
    for session_path in harness_sessions_dir.iterdir():
        if not session_path.is_dir():
            continue

        # Session directory name is the session ID
        session_id = session_path.name
        meta_file = session_path / "meta.json"

        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                # Map harness session to DiscoveredAgent format
                agents.append(
                    {
                        "session_id": session_id,
                        "agent": data.get("agent", "unknown"),
                        "cwd": data.get("cwd", "unknown"),
                        "pid": data.get("pid", 0),
                        "ppid": data.get("ppid", 0),
                        "status": data.get("status", "unknown"),
                        "source": "harness",
                    }
                )
            except Exception as e:
                _log.debug(f"Failed to read harness session {session_id}: {e}")

    return agents
