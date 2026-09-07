from __future__ import annotations

import typer

from ..core import nuke
from ..git.repo import in_progress_operation
from .console import console, esc


def _in_progress_warning() -> str:
    op = in_progress_operation()
    if op is None:
        return ""
    if op == "rebase":
        return " A rebase is in progress; this will NOT abort it (run 'mgit rebase abort' first if you want to abandon it)."
    return f" A {op} is currently in progress and will be abandoned."


def reset_hard_cmd(ref: str, yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Hard-reset the current branch to a ref, discarding local commits."""
    if not yes:
        typer.confirm(f"Hard-reset the current branch to '{ref}'?{_in_progress_warning()} This discards local commits.", abort=True)
    nuke.reset_hard(ref)
    console.print(f"[yellow]Reset to {esc(ref)}[/yellow]")


def nuke_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Discard all uncommitted changes and untracked files."""
    if not yes:
        typer.confirm(f"This discards ALL uncommitted changes and untracked files.{_in_progress_warning()} Continue?", abort=True)
    nuke.nuke()
    console.print("[yellow]Working tree reset and cleaned[/yellow]")


def nuke_branch_cmd(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Reset the current branch to exactly match its upstream."""
    if not yes:
        typer.confirm(f"Reset the current branch to exactly match its upstream?{_in_progress_warning()} This discards local commits.", abort=True)
    nuke.nuke_branch()
    console.print("[yellow]Branch reset to match upstream[/yellow]")
