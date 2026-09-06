from __future__ import annotations

import sys

import typer
from rich.console import Console

from ..git.runner import GitCommandError
from .branch_cmds import app as branch_app

app = typer.Typer(
    name="mgit",
    help="A git wrapper with rich log search, git-flow helpers, and an optional modern TUI.",
    no_args_is_help=True,
)
app.add_typer(branch_app, name="branch")
console = Console(stderr=True)


def main() -> None:
    try:
        app()
    except GitCommandError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc.stderr.strip() or exc}")
        sys.exit(exc.returncode or 1)
