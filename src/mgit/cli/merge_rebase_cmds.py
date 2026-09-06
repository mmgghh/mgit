from __future__ import annotations

import typer
from rich.console import Console

from ..core import merge_rebase as mr

console = Console()

rebase_app = typer.Typer(name="rebase", help="Rebase helpers")
merge_app = typer.Typer(name="merge", help="Merge helpers")
cherry_pick_app = typer.Typer(name="cherry-pick", help="Cherry-pick helpers")
revert_app = typer.Typer(name="revert", help="Revert helpers")
conflicts_app = typer.Typer(name="conflicts", help="Inspect merge conflicts")


@rebase_app.command("continue")
def rebase_continue_cmd() -> None:
    mr.rebase_continue()
    console.print("[green]Rebase continued[/green]")


@rebase_app.command("abort")
def rebase_abort_cmd() -> None:
    mr.rebase_abort()
    console.print("[yellow]Rebase aborted[/yellow]")


@rebase_app.command("skip")
def rebase_skip_cmd() -> None:
    mr.rebase_skip()
    console.print("[yellow]Rebase commit skipped[/yellow]")


@merge_app.command("continue")
def merge_continue_cmd() -> None:
    mr.merge_continue()
    console.print("[green]Merge continued[/green]")


@merge_app.command("abort")
def merge_abort_cmd() -> None:
    mr.merge_abort()
    console.print("[yellow]Merge aborted[/yellow]")


@cherry_pick_app.command("continue")
def cherry_pick_continue_cmd() -> None:
    mr.cherry_pick_continue()
    console.print("[green]Cherry-pick continued[/green]")


@cherry_pick_app.command("abort")
def cherry_pick_abort_cmd() -> None:
    mr.cherry_pick_abort()
    console.print("[yellow]Cherry-pick aborted[/yellow]")


@cherry_pick_app.command("skip")
def cherry_pick_skip_cmd() -> None:
    mr.cherry_pick_skip()
    console.print("[yellow]Cherry-pick commit skipped[/yellow]")


@revert_app.command("continue")
def revert_continue_cmd() -> None:
    mr.revert_continue()
    console.print("[green]Revert continued[/green]")


@revert_app.command("abort")
def revert_abort_cmd() -> None:
    mr.revert_abort()
    console.print("[yellow]Revert aborted[/yellow]")


@revert_app.command("skip")
def revert_skip_cmd() -> None:
    mr.revert_skip()
    console.print("[yellow]Revert commit skipped[/yellow]")


@conflicts_app.command("list")
def conflicts_list_cmd() -> None:
    conflicts = mr.list_conflicts()
    if not conflicts:
        console.print("No conflicts")
    for path, label in conflicts:
        console.print(f"{path}: [red]{label}[/red]")


@conflicts_app.command("base")
def conflicts_base_cmd(path: str) -> None:
    console.print(mr.conflict_side(path, "base"))


@conflicts_app.command("ours")
def conflicts_ours_cmd(path: str) -> None:
    console.print(mr.conflict_side(path, "ours"))


@conflicts_app.command("theirs")
def conflicts_theirs_cmd(path: str) -> None:
    console.print(mr.conflict_side(path, "theirs"))
