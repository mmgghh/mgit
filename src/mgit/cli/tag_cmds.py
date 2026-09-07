from __future__ import annotations

import typer

from ..core import tags
from .console import console, esc

app = typer.Typer(name="tag", help="Tag management")


@app.command("list")
def list_cmd() -> None:
    """List tags."""
    for name in tags.list_tags():
        console.print(name, markup=False)


@app.command("new")
def new_cmd(name: str, message: str = typer.Argument(None)) -> None:
    """Create an annotated tag."""
    tags.new_tag(name, message)
    console.print(f"[green]Created tag {esc(name)}[/green]")


@app.command("delete")
def delete_cmd(name: str, yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Delete a tag locally and on the remote."""
    if not yes:
        typer.confirm(f"Delete tag '{name}' locally and on the remote?", abort=True)
    tags.delete_tag(name)
    console.print(f"[yellow]Deleted tag {esc(name)} locally and on remote[/yellow]")


@app.command("push")
def push_cmd(name: str = typer.Argument(None)) -> None:
    """Push one tag, or all tags, to the remote."""
    tags.push_tag(name)
    console.print("[green]Pushed tag(s)[/green]")
