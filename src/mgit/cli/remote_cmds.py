from __future__ import annotations

import typer

from ..core import remotes
from .console import console, esc

app = typer.Typer(name="remote", help="Remote management")


@app.command("list")
def list_cmd() -> None:
    """List configured remotes."""
    for entry in remotes.list_remotes():
        console.print(entry, markup=False)


@app.command("add")
def add_cmd(name: str, url: str) -> None:
    """Add a remote."""
    remotes.add_remote(name, url)
    console.print(f"[green]Added remote {esc(name)}[/green]")


@app.command("delete")
def delete_cmd(name: str) -> None:
    """Remove a remote."""
    remotes.delete_remote(name)
    console.print(f"[yellow]Removed remote {esc(name)}[/yellow]")
