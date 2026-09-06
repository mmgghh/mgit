from __future__ import annotations

import typer
from rich.console import Console

from ..core import nuke

console = Console()


def reset_hard_cmd(ref: str, yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    if not yes:
        typer.confirm(f"Hard-reset the current branch to '{ref}'? This discards local commits.", abort=True)
    nuke.reset_hard(ref)
    console.print(f"[yellow]Reset to {ref}[/yellow]")


def nuke_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    if not yes:
        typer.confirm("This discards ALL uncommitted changes and untracked files. Continue?", abort=True)
    nuke.nuke()
    console.print("[yellow]Working tree reset and cleaned[/yellow]")


def nuke_branch_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    if not yes:
        typer.confirm("Reset the current branch to exactly match its upstream? This discards local commits.", abort=True)
    nuke.nuke_branch()
    console.print("[yellow]Branch reset to match upstream[/yellow]")
