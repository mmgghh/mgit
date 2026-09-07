from __future__ import annotations

import typer

from ..core import flow
from .console import console, esc

app = typer.Typer(name="flow", help="git-flow branch model")
feature_app = typer.Typer(name="feature", help="Feature branches")
release_app = typer.Typer(name="release", help="Release branches")
hotfix_app = typer.Typer(name="hotfix", help="Hotfix branches")
app.add_typer(feature_app, name="feature")
app.add_typer(release_app, name="release")
app.add_typer(hotfix_app, name="hotfix")


@app.command("init")
def init_cmd(main: str = typer.Option("main"), develop: str = typer.Option("develop")) -> None:
    """Initialize git-flow branch prefixes and base branches."""
    flow.init_flow(main, develop)
    console.print(f"[green]Initialized git-flow ({esc(main)} / {esc(develop)})[/green]")


@feature_app.command("start")
def feature_start_cmd(name: str) -> None:
    """Start a new feature branch."""
    flow.feature_start(name)
    console.print(f"[green]Started feature/{esc(name)}[/green]")


@feature_app.command("finish")
def feature_finish_cmd(name: str) -> None:
    """Merge a feature branch into develop and delete it."""
    flow.feature_finish(name)
    console.print(f"[green]Finished feature/{esc(name)}[/green]")


@feature_app.command("list")
def feature_list_cmd() -> None:
    """List feature branches."""
    for b in flow.feature_list():
        console.print(b, markup=False)


@release_app.command("start")
def release_start_cmd(version: str) -> None:
    """Start a new release branch."""
    flow.release_start(version)
    console.print(f"[green]Started release/{esc(version)}[/green]")


@release_app.command("finish")
def release_finish_cmd(version: str) -> None:
    """Merge a release branch into main and develop, tag it, and delete it."""
    flow.release_finish(version)
    console.print(f"[green]Finished release/{esc(version)}, tagged {esc(version)}[/green]")


@release_app.command("list")
def release_list_cmd() -> None:
    """List release branches."""
    for b in flow.release_list():
        console.print(b, markup=False)


@hotfix_app.command("start")
def hotfix_start_cmd(version: str) -> None:
    """Start a new hotfix branch."""
    flow.hotfix_start(version)
    console.print(f"[green]Started hotfix/{esc(version)}[/green]")


@hotfix_app.command("finish")
def hotfix_finish_cmd(version: str) -> None:
    """Merge a hotfix branch into main and develop, tag it, and delete it."""
    flow.hotfix_finish(version)
    console.print(f"[green]Finished hotfix/{esc(version)}, tagged {esc(version)}[/green]")


@hotfix_app.command("list")
def hotfix_list_cmd() -> None:
    """List hotfix branches."""
    for b in flow.hotfix_list():
        console.print(b, markup=False)
