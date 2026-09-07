from __future__ import annotations

import typer

from ..core import sync
from .console import console


def push_cmd(force: bool = typer.Option(False, "--force", "-f")) -> None:
    """Push the current branch, publishing it if it has no upstream."""
    sync.push(force=force)
    console.print("[green]Pushed[/green]")


def pull_cmd() -> None:
    """Pull the current branch with rebase."""
    sync.pull()
    console.print("[green]Pulled (rebased)[/green]")


def fetch_cmd() -> None:
    """Fetch and prune all remotes."""
    sync.fetch_all()
    console.print("[green]Fetched all remotes[/green]")


def sync_cmd() -> None:
    """Fetch and rebase the current branch onto its upstream."""
    sync.sync()
    console.print("[green]Synced (fetched + rebased)[/green]")
