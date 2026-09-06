from __future__ import annotations

import typer
from rich.console import Console

from .. import config as cfg
from ..core import repo_info

console = Console()
config_app = typer.Typer(name="config", help="mgit configuration")


def whoami_cmd() -> None:
    info = repo_info.whoami()
    console.print(f"{info['name']} <{info['email']}>")


def root_cmd() -> None:
    console.print(repo_info.summary()["root"])


def ignored_cmd() -> None:
    for path in repo_info.ignored_files():
        console.print(path)


def aliases_cmd() -> None:
    for line in repo_info.aliases():
        console.print(line)


def repo_info_cmd() -> None:
    info = repo_info.summary()
    console.print(f"[bold]Root:[/bold] {info['root']}")
    console.print(f"[bold]Branch:[/bold] {info['branch']}")
    if info["in_progress"]:
        console.print(f"[bold red]In progress:[/bold red] {info['in_progress']}")
    console.print("[bold]Remotes:[/bold]")
    for remote in info["remotes"]:
        console.print(f"  {remote}")


@config_app.command("get")
def config_get_cmd(key: str) -> None:
    console.print(cfg.get(key))


@config_app.command("set")
def config_set_cmd(key: str, value: str, global_: bool = typer.Option(False, "--global")) -> None:
    cfg.set_value(key, value, global_=global_)
    console.print(f"[green]Set {key} = {value}[/green]")
