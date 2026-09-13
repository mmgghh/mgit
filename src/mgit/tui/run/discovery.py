from __future__ import annotations

from dataclasses import dataclass

from typer._click import core as click
import typer.core
import typer.main


@dataclass
class CommandEntry:
    path: list[str]
    command: click.Command
    help: str


def discover_commands(typer_app: typer.Typer) -> list[CommandEntry]:
    root = typer.main.get_command(typer_app)
    ctx = click.Context(root, info_name="mgit")
    entries: list[CommandEntry] = []
    _walk(root, ctx, [], entries)
    entries.sort(key=lambda e: e.path)
    return entries


def _walk(group: click.Command, ctx: click.Context, path: list[str], entries: list[CommandEntry]) -> None:
    for name in sorted(group.list_commands(ctx)):
        command = group.get_command(ctx, name)
        if command is None or command.hidden:
            continue
        sub_path = [*path, name]
        if isinstance(command, typer.core.TyperGroup):
            sub_ctx = click.Context(command, info_name=name, parent=ctx)
            _walk(command, sub_ctx, sub_path, entries)
        else:
            entries.append(
                CommandEntry(path=sub_path, command=command, help=command.get_short_help_str(limit=70).strip())
            )
