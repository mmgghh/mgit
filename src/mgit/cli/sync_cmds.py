from __future__ import annotations

import typer
from rich.console import Console

from ..core import sync

console = Console()


def push_cmd(force: bool = typer.Option(False, "--force", "-f")) -> None:
    sync.push(force=force)
    console.print("[green]Pushed[/green]")


def pull_cmd() -> None:
    sync.pull()
    console.print("[green]Pulled (rebased)[/green]")


def fetch_cmd() -> None:
    sync.fetch_all()
    console.print("[green]Fetched all remotes[/green]")


def sync_cmd() -> None:
    sync.sync()
    console.print("[green]Synced (fetched + rebased)[/green]")
