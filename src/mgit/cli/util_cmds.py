from __future__ import annotations

import typer

from .. import config as cfg
from ..core import repo_info
from .console import console, esc

config_app = typer.Typer(name="config", help="mgit configuration")


def whoami_cmd() -> None:
    """Show the configured git identity."""
    info = repo_info.whoami()
    console.print(f"{info['name']} <{info['email']}>", markup=False)


def root_cmd() -> None:
    """Print the repository root."""
    console.print(repo_info.summary()["root"], markup=False)


def ignored_cmd() -> None:
    """List ignored files."""
    for path in repo_info.ignored_files():
        console.print(path, markup=False)


def aliases_cmd() -> None:
    """List configured git aliases."""
    for line in repo_info.aliases():
        console.print(line, markup=False)


def repo_info_cmd() -> None:
    """Show a repository summary: root, branch, in-progress operation, remotes."""
    info = repo_info.summary()
    console.print(f"[bold]Root:[/bold] {esc(info['root'])}")
    console.print(f"[bold]Branch:[/bold] {esc(str(info['branch']))}")
    if info["in_progress"]:
        console.print(f"[bold red]In progress:[/bold red] {info['in_progress']}")
    console.print("[bold]Remotes:[/bold]")
    for remote in info["remotes"]:
        console.print(f"  {remote}", markup=False)


@config_app.command("get")
def config_get_cmd(key: str) -> None:
    """Read a config value."""
    console.print(cfg.get(key), markup=False)


@config_app.command("set")
def config_set_cmd(key: str, value: str, global_: bool = typer.Option(False, "--global")) -> None:
    """Write a config value (add --global for the global config file)."""
    cfg.set_value(key, value, global_=global_)
    console.print(f"[green]Set {esc(key)} = {esc(value)}[/green]")
