from __future__ import annotations

import typer
from rich.console import Console

from ..core import commit

console = Console()


def commit_cmd(message: str) -> None:
    commit.commit(message)
    console.print("[green]Committed[/green]")


def commit_empty_cmd(message: str) -> None:
    commit.commit_empty(message)
    console.print("[green]Committed (empty)[/green]")


def amend_cmd(push: bool = typer.Option(False, "--push")) -> None:
    commit.amend(push_after=push)
    console.print("[green]Amended" + (" and force-pushed" if push else "") + "[/green]")


def undo_cmd(hard: bool = typer.Option(False, "--hard")) -> None:
    commit.undo(hard=hard)
    console.print("[yellow]Last commit undone" + (" (changes discarded)" if hard else " (changes kept)") + "[/yellow]")
