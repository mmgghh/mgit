from __future__ import annotations

import typer
from rich.console import Console

from ..core import flow

console = Console()
app = typer.Typer(name="flow", help="git-flow branch model")
feature_app = typer.Typer(name="feature", help="Feature branches")
release_app = typer.Typer(name="release", help="Release branches")
hotfix_app = typer.Typer(name="hotfix", help="Hotfix branches")
app.add_typer(feature_app, name="feature")
app.add_typer(release_app, name="release")
app.add_typer(hotfix_app, name="hotfix")


@app.command("init")
def init_cmd(main: str = typer.Option("main"), develop: str = typer.Option("develop")) -> None:
    flow.init_flow(main, develop)
    console.print(f"[green]Initialized git-flow ({main} / {develop})[/green]")


@feature_app.command("start")
def feature_start_cmd(name: str) -> None:
    flow.feature_start(name)
    console.print(f"[green]Started feature/{name}[/green]")


@feature_app.command("finish")
def feature_finish_cmd(name: str) -> None:
    flow.feature_finish(name)
    console.print(f"[green]Finished feature/{name}[/green]")


@feature_app.command("list")
def feature_list_cmd() -> None:
    for b in flow.feature_list():
        console.print(b)


@release_app.command("start")
def release_start_cmd(version: str) -> None:
    flow.release_start(version)
    console.print(f"[green]Started release/{version}[/green]")


@release_app.command("finish")
def release_finish_cmd(version: str) -> None:
    flow.release_finish(version)
    console.print(f"[green]Finished release/{version}, tagged {version}[/green]")


@release_app.command("list")
def release_list_cmd() -> None:
    for b in flow.release_list():
        console.print(b)


@hotfix_app.command("start")
def hotfix_start_cmd(version: str) -> None:
    flow.hotfix_start(version)
    console.print(f"[green]Started hotfix/{version}[/green]")


@hotfix_app.command("finish")
def hotfix_finish_cmd(version: str) -> None:
    flow.hotfix_finish(version)
    console.print(f"[green]Finished hotfix/{version}, tagged {version}[/green]")


@hotfix_app.command("list")
def hotfix_list_cmd() -> None:
    for b in flow.hotfix_list():
        console.print(b)
