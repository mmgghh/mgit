from __future__ import annotations

import typer

from ..core import stash
from .console import console, emit_raw

app = typer.Typer(name="stash", help="Stash management")


@app.command("save")
def save_cmd(message: str = typer.Argument(None)) -> None:
    """Stash uncommitted changes, including untracked files."""
    result = stash.stash_save(message)
    if result is None:
        console.print("Nothing to stash, working tree clean")
    else:
        console.print("[green]Stashed[/green]")


@app.command("list")
def list_cmd() -> None:
    """List stashes."""
    for entry in stash.stash_list():
        console.print(entry, markup=False)


@app.command("pop")
def pop_cmd(index: int = typer.Argument(None)) -> None:
    """Apply and drop a stash."""
    stash.stash_pop(index)
    console.print("[green]Stash popped[/green]")


@app.command("apply")
def apply_cmd(index: int = typer.Argument(None)) -> None:
    """Apply a stash without dropping it."""
    stash.stash_apply(index)
    console.print("[green]Stash applied[/green]")


@app.command("drop")
def drop_cmd(index: int = typer.Argument(None)) -> None:
    """Drop a stash."""
    stash.stash_drop(index)
    console.print("[yellow]Stash dropped[/yellow]")


@app.command("clear")
def clear_cmd() -> None:
    """Clear all stashes."""
    stash.stash_clear()
    console.print("[yellow]All stashes cleared[/yellow]")


@app.command("show")
def show_cmd(index: int = typer.Argument(None)) -> None:
    """Show a stash's diff."""
    emit_raw(stash.stash_show(index))
