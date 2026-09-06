from __future__ import annotations

import typer
from rich.console import Console

from ..core import stash

app = typer.Typer(name="stash", help="Stash management")
console = Console()


@app.command("save")
def save_cmd(message: str = typer.Argument(None)) -> None:
    result = stash.stash_save(message)
    if result is None:
        console.print("Nothing to stash, working tree clean")
    else:
        console.print("[green]Stashed[/green]")


@app.command("list")
def list_cmd() -> None:
    for entry in stash.stash_list():
        console.print(entry)


@app.command("pop")
def pop_cmd(index: int = typer.Argument(None)) -> None:
    stash.stash_pop(index)
    console.print("[green]Stash popped[/green]")


@app.command("apply")
def apply_cmd(index: int = typer.Argument(None)) -> None:
    stash.stash_apply(index)
    console.print("[green]Stash applied[/green]")


@app.command("drop")
def drop_cmd(index: int = typer.Argument(None)) -> None:
    stash.stash_drop(index)
    console.print("[yellow]Stash dropped[/yellow]")


@app.command("clear")
def clear_cmd() -> None:
    stash.stash_clear()
    console.print("[yellow]All stashes cleared[/yellow]")


@app.command("show")
def show_cmd(index: int = typer.Argument(None)) -> None:
    console.print(stash.stash_show(index))
