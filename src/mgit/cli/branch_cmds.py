from __future__ import annotations

import typer

from ..core import branches
from ..git.repo import current_branch
from .console import console, esc

app = typer.Typer(name="branch", help="Branch management")


@app.command("list")
def list_cmd() -> None:
    """List local branches, marking the current one."""
    current = current_branch()
    for name in branches.list_branches():
        marker = "*" if name == current else " "
        console.print(f"{marker} {name}", markup=False)


@app.command("new")
def new_cmd(name: str, start_point: str = typer.Argument(None)) -> None:
    """Create a new branch and switch to it."""
    branches.new_branch(name, start_point)
    console.print(f"[green]Created and switched to {esc(name)}[/green]")


@app.command("switch")
def switch_cmd(name: str) -> None:
    """Switch to an existing local or remote-tracking branch."""
    branches.switch_branch(name)
    console.print(f"[green]Switched to {esc(name)}[/green]")


@app.command("delete")
def delete_cmd(name: str, force: bool = typer.Option(False, "--force", "-f")) -> None:
    """Delete a local branch."""
    branches.delete_branch(name, force=force)
    console.print(f"[green]Deleted {esc(name)}[/green]")


@app.command("delete-remote")
def delete_remote_cmd(name: str, remote: str = typer.Option(None, "--remote")) -> None:
    """Delete a branch on a remote."""
    branches.delete_remote_branch(name, remote=remote)
    console.print(f"[green]Deleted remote branch {esc(name)}[/green]")


@app.command("rename")
def rename_cmd(old: str, new: str) -> None:
    """Rename a branch."""
    branches.rename_branch(old, new)
    console.print(f"[green]Renamed {esc(old)} -> {esc(new)}[/green]")


@app.command("merged")
def merged_cmd() -> None:
    """List local branches already merged into the current branch."""
    for name in branches.merged_branches():
        console.print(name, markup=False)


@app.command("unmerged")
def unmerged_cmd() -> None:
    """List local branches not yet merged into the current branch."""
    for name in branches.unmerged_branches():
        console.print(name, markup=False)


@app.command("prune")
def prune_cmd(force: bool = typer.Option(False, "--force", "-f")) -> None:
    """Delete local branches whose tracked remote branch is gone."""
    deleted = branches.prune_gone(force=force)
    if not deleted:
        console.print("Nothing to prune")
    for name in deleted:
        console.print(f"[yellow]Pruned {esc(name)}[/yellow]")


@app.command("report")
def report_cmd(branch: str = typer.Argument(None), base: str = typer.Argument(None)) -> None:
    """Show commits and changed files for a branch against a base."""
    data = branches.branch_report(branch, base)
    console.print(f"[bold]{esc(data['branch'])}[/bold] vs [bold]{esc(data['base'])}[/bold] (merge-base {data['merge_base'][:8]})")
    for c in data["commits"]:
        console.print(f"  {c}", markup=False)
    console.print("[bold]Changed files:[/bold]")
    for f in data["files"]:
        console.print(f"  {f}", markup=False)
