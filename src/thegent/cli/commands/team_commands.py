"""Team commands implementation.

This module contains the team-related CLI command implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


def team_create_cmd(
    *,
    name: str,
    leader: str | None = None,
    teammates: str | None = None,
    console: Console | None = None,
) -> None:
    """Create a new team.

    Args:
        name: Team name.
        leader: Leader agent name.
        teammates: Comma-separated teammate names.
        console: Rich console for output.
    """
    if console is None:
        from rich.console import Console
        console = Console()

    console.print(f"[bold]Creating team:[/bold] {name}")
    if leader:
        console.print(f"  Leader: {leader}")
    if teammates:
        console.print(f"  Teammates: {teammates}")


def team_task_add_cmd(
    *,
    team_id: str,
    title: str,
    description: str,
    console: Console | None = None,
) -> None:
    """Add a task to a team.

    Args:
        team_id: Team ID.
        title: Task title.
        description: Task description.
        console: Rich console for output.
    """
    if console is None:
        from rich.console import Console
        console = Console()

    console.print(f"[bold]Adding task to team {team_id}:[/bold] {title}")


def team_task_list_cmd(
    *,
    team_id: str,
    console: Console | None = None,
) -> None:
    """List tasks for a team.

    Args:
        team_id: Team ID.
        console: Rich console for output.
    """
    if console is None:
        from rich.console import Console
        console = Console()

    console.print(f"[bold]Tasks for team {team_id}:[/bold]")


__all__ = [
    "team_create_cmd",
    "team_task_add_cmd",
    "team_task_list_cmd",
]
