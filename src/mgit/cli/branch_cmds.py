from __future__ import annotations

import typer
from rich.console import Console

from ..core import branches
from ..git.repo import current_branch

app = typer.Typer(name="branch", help="Branch management")
console = Console()


@app.command("list")
def list_cmd() -> None:
    current = current_branch()
    for name in branches.list_branches():
        marker = "*" if name == current else " "
        console.print(f"{marker} {name}")


@app.command("new")
def new_cmd(name: str, start_point: str = typer.Argument(None)) -> None:
    branches.new_branch(name, start_point)
    console.print(f"[green]Created and switched to {name}[/green]")


@app.command("switch")
def switch_cmd(name: str) -> None:
    branches.switch_branch(name)
    console.print(f"[green]Switched to {name}[/green]")


@app.command("delete")
def delete_cmd(name: str, force: bool = typer.Option(False, "--force", "-f")) -> None:
    branches.delete_branch(name, force=force)
    console.print(f"[green]Deleted {name}[/green]")


@app.command("delete-remote")
def delete_remote_cmd(name: str, remote: str = typer.Option(None, "--remote")) -> None:
    branches.delete_remote_branch(name, remote=remote)
    console.print(f"[green]Deleted remote branch {name}[/green]")


@app.command("rename")
def rename_cmd(old: str, new: str) -> None:
    branches.rename_branch(old, new)
    console.print(f"[green]Renamed {old} -> {new}[/green]")


@app.command("merged")
def merged_cmd() -> None:
    for name in branches.merged_branches():
        console.print(name)


@app.command("unmerged")
def unmerged_cmd() -> None:
    for name in branches.unmerged_branches():
        console.print(name)


@app.command("prune")
def prune_cmd(force: bool = typer.Option(False, "--force", "-f")) -> None:
    deleted = branches.prune_gone(force=force)
    if not deleted:
        console.print("Nothing to prune")
    for name in deleted:
        console.print(f"[yellow]Pruned {name}[/yellow]")


@app.command("report")
def report_cmd(branch: str = typer.Argument(None), base: str = typer.Argument(None)) -> None:
    data = branches.branch_report(branch, base)
    console.print(f"[bold]{data['branch']}[/bold] vs [bold]{data['base']}[/bold] (merge-base {data['merge_base'][:8]})")
    for c in data["commits"]:
        console.print(f"  {c}")
    console.print("[bold]Changed files:[/bold]")
    for f in data["files"]:
        console.print(f"  {f}")
