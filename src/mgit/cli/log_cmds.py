from __future__ import annotations

import typer
from rich.console import Console

from ..core.log_search import LogFilter, diff as diff_core, search

console = Console()


def log_cmd(
    author: str = typer.Option(None, "--author"),
    since: str = typer.Option(None, "--since"),
    until: str = typer.Option(None, "--until"),
    grep: str = typer.Option(None, "--grep"),
    path: str = typer.Option(None, "--path"),
    branch: str = typer.Option(None, "--branch"),
    merges: bool = typer.Option(False, "--merges"),
    no_merges: bool = typer.Option(False, "--no-merges"),
    limit: int = typer.Option(None, "--limit", "-n"),
) -> None:
    merge_filter = True if merges else (False if no_merges else None)
    f = LogFilter(
        author=author, since=since, until=until, grep=grep,
        path=path, branch=branch, merges=merge_filter, limit=limit,
    )
    for c in search(f):
        console.print(f"[yellow]{c.short_sha}[/yellow] [cyan]{c.date[:10]}[/cyan] [green]{c.author}[/green] {c.subject}")


def diff_cmd(
    ref_a: str = typer.Argument(None),
    ref_b: str = typer.Argument(None),
    staged: bool = typer.Option(False, "--staged"),
) -> None:
    console.print(diff_core(staged=staged, ref_a=ref_a, ref_b=ref_b))
