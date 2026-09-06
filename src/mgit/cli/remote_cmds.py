from __future__ import annotations

import typer
from rich.console import Console

from ..core import remotes

app = typer.Typer(name="remote", help="Remote management")
console = Console()


@app.command("list")
def list_cmd() -> None:
    for entry in remotes.list_remotes():
        console.print(entry)


@app.command("add")
def add_cmd(name: str, url: str) -> None:
    remotes.add_remote(name, url)
    console.print(f"[green]Added remote {name}[/green]")


@app.command("delete")
def delete_cmd(name: str) -> None:
    remotes.delete_remote(name)
    console.print(f"[yellow]Removed remote {name}[/yellow]")
