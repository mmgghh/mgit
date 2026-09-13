from __future__ import annotations

from dataclasses import dataclass

import typer
import typer.core
import typer.main


@dataclass
class CommandEntry:
    path: list[str]
    command: typer.core.TyperCommand
    help: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CommandEntry):
            return NotImplemented
        return self.path == other.path and self.help == other.help


def discover_commands(typer_app: typer.Typer) -> list[CommandEntry]:
    root = typer.main.get_command(typer_app)
    ctx = typer.Context(root, info_name="mgit")
    entries: list[CommandEntry] = []
    _walk(root, ctx, [], entries)
    entries.sort(key=lambda e: e.path)
    return entries


def _walk(group: typer.core.TyperGroup, ctx: typer.Context, path: list[str], entries: list[CommandEntry]) -> None:
    for name in sorted(group.list_commands(ctx)):
        command = group.get_command(ctx, name)
        if command is None or command.hidden:
            continue
        sub_path = [*path, name]
        if isinstance(command, typer.core.TyperGroup):
            sub_ctx = typer.Context(command, info_name=name, parent=ctx)
            _walk(command, sub_ctx, sub_path, entries)
        else:
            entries.append(
                CommandEntry(path=sub_path, command=command, help=command.get_short_help_str(limit=70).strip())
            )
