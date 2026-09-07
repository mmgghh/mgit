from __future__ import annotations

import typer

from ..core import commit
from .console import console


def commit_cmd(message: str) -> None:
    """Stage everything and commit."""
    commit.commit(message)
    console.print("[green]Committed[/green]")


def commit_empty_cmd(message: str) -> None:
    """Create an empty commit."""
    commit.commit_empty(message)
    console.print("[green]Committed (empty)[/green]")


def amend_cmd(push: bool = typer.Option(False, "--push")) -> None:
    """Amend the last commit, optionally force-pushing."""
    commit.amend(push_after=push)
    console.print("[green]Amended" + (" and force-pushed" if push else "") + "[/green]")


def undo_cmd(hard: bool = typer.Option(False, "--hard")) -> None:
    """Undo the last commit, keeping or discarding its changes."""
    commit.undo(hard=hard)
    console.print("[yellow]Last commit undone" + (" (changes discarded)" if hard else " (changes kept)") + "[/yellow]")
