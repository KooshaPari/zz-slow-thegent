"""Advanced runtime helpers for CLI operations.

This module provides higher-level runtime helpers for thegent CLI
including session management, configuration resolution, and output formatting.
"""

from __future__ import annotations

import getpass
import os
from pathlib import Path
from typing import Any

import typer

from thegent.config import ThegentSettings

# Health payload schema version
HEALTH_PAYLOAD_SCHEMA_VERSION = "3.0"


def resolve_cwd(cwd: Path | None) -> Path | None:
    """Resolve the working directory for the CLI.

    Args:
        cwd: Explicitly specified directory, or None to infer.

    Returns:
        Resolved Path or None if ambiguous.

    Raises:
        typer.BadParameter: If explicitly specified directory doesn't exist.
    """
    if cwd is not None:
        expanded = cwd.expanduser()
        if not expanded.exists():
            raise typer.BadParameter(f"Directory does not exist: {cwd}")
        return expanded.resolve()

    # Try to infer from project indicators
    current = Path.cwd()

    # Check current and parents for .git, .factory, or pyproject.toml
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
        if (parent / ".factory").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent

    return None  # Ambiguous


def resolve_droids_dir(cwd: Path | None, settings: ThegentSettings) -> Path:
    """Resolve the droids directory.

    Args:
        cwd: The working directory.
        settings: Thegent settings.

    Returns:
        Path to the droids directory.
    """
    if cwd is not None:
        factory_droids = cwd / ".factory" / "droids"
        if factory_droids.exists():
            return factory_droids.resolve()

    return settings.factory_droids_dir.expanduser().resolve()


def compose_owner_tag(
    user: str | None,
    cwd: Path,
    scope: str | None = None,
) -> str:
    """Compose the owner tag for a session.

    Args:
        user: The username, or None to use current user.
        cwd: The working directory.
        scope: Optional scope suffix.

    Returns:
        Composed owner tag.
    """
    if user is None:
        user = getpass.getuser()

    base = f"{user}:{cwd.name}"
    if scope:
        # Expand placeholders
        scope = scope.replace("{pid}", str(os.getpid()))
        scope = scope.replace("{cwd}", cwd.name)
        return f"{base}:{scope}"
    return base


def default_owner_tag(cwd: Path) -> str:
    """Get the default owner tag for the given directory.

    Args:
        cwd: The working directory.

    Returns:
        Default owner tag.
    """
    return compose_owner_tag(getpass.getuser(), cwd)


def inject_time_constraint(prompt: str, timeout: int) -> str:
    """Inject time constraint into prompt.

    Args:
        prompt: The prompt to inject constraint into.
        timeout: Timeout in seconds.

    Returns:
        Prompt with time constraint injected.
    """
    tool_calls = max(1, round(timeout / 2.3))
    constraint = (
        f"\n\n[TIME CONSTRAINT] Complete in {timeout}s (~{tool_calls} tool calls).\n"
    )
    return prompt + constraint


def validate_image_capability(image_path: str | Path) -> bool:
    """Validate that image capability is available.

    Args:
        image_path: Path to the image file.

    Returns:
        True if image exists, False otherwise.
    """
    return Path(image_path).exists()


def resolve_audio_transcript_for_output(transcript: dict[str, Any]) -> dict[str, Any]:
    """Resolve audio transcript for output.

    Args:
        transcript: Raw transcript dictionary.

    Returns:
        Formatted transcript for output.
    """
    return {
        "transcript": transcript.get("text", ""),
        "duration": transcript.get("duration", 0.0),
    }


def resolve_grounding_sources_for_output(sources: list[dict]) -> list[dict[str, Any]]:
    """Resolve grounding sources for output.

    Args:
        sources: List of source dictionaries.

    Returns:
        Formatted sources list (truncated content).
    """
    return [
        {"source": s.get("source", ""), "content": s.get("content", "")[:100]}
        for s in sources
    ]


def get_terminal_width() -> int:
    """Get the terminal width.

    Returns:
        Terminal width in columns, defaulting to 80.
    """
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def truncate_output(text: str, max_length: int = 1000) -> str:
    """Truncate output text with ellipsis.

    Args:
        text: Text to truncate.
        max_length: Maximum length before truncation.

    Returns:
        Truncated text with "..." suffix if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
