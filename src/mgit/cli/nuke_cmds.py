from __future__ import annotations

import typer

from ..core import nuke
from ..git.repo import in_progress_operation
from .console import console, esc


def reset_hard_cmd(ref: str, yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Hard-reset the current branch to a ref, discarding local commits."""
    if not yes:
        op = in_progress_operation()
        warning = f" A {op} is currently in progress and will be abandoned." if op else ""
        typer.confirm(f"Hard-reset the current branch to '{ref}'?{warning} This discards local commits.", abort=True)
    nuke.reset_hard(ref)
    console.print(f"[yellow]Reset to {esc(ref)}[/yellow]")


def nuke_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Discard all uncommitted changes and untracked files."""
    if not yes:
        op = in_progress_operation()
        warning = f" A {op} is currently in progress and will be abandoned." if op else ""
        typer.confirm(f"This discards ALL uncommitted changes and untracked files.{warning} Continue?", abort=True)
    nuke.nuke()
    console.print("[yellow]Working tree reset and cleaned[/yellow]")


def nuke_branch_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Reset the current branch to exactly match its upstream."""
    if not yes:
        op = in_progress_operation()
        warning = f" A {op} is currently in progress and will be abandoned." if op else ""
        typer.confirm(f"Reset the current branch to exactly match its upstream?{warning} This discards local commits.", abort=True)
    nuke.nuke_branch()
    console.print("[yellow]Branch reset to match upstream[/yellow]")
