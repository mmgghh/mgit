from __future__ import annotations

import typer
from rich.console import Console

from ..core import tags

app = typer.Typer(name="tag", help="Tag management")
console = Console()


@app.command("list")
def list_cmd() -> None:
    for name in tags.list_tags():
        console.print(name)


@app.command("new")
def new_cmd(name: str, message: str = typer.Argument(None)) -> None:
    tags.new_tag(name, message)
    console.print(f"[green]Created tag {name}[/green]")


@app.command("delete")
def delete_cmd(name: str) -> None:
    tags.delete_tag(name)
    console.print(f"[yellow]Deleted tag {name} locally and on remote[/yellow]")


@app.command("push")
def push_cmd(name: str = typer.Argument(None)) -> None:
    tags.push_tag(name)
    console.print("[green]Pushed tag(s)[/green]")
