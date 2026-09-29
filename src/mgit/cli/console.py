from __future__ import annotations

import sys

from rich.console import Console
from rich.markup import escape as esc

from .. import config as cfg
from ..git import delta

console = Console()
err_console = Console(stderr=True)


def emit_raw(text: str) -> None:
    console.print(text, markup=False, highlight=False, soft_wrap=True)


def _is_terminal() -> bool:
    # Deliberately not rich's is_terminal: the TUI's Run tab sets FORCE_COLOR,
    # which rich treats as a terminal, but its output is a pipe.
    return sys.stdout.isatty()


def emit_diff(text: str, cwd: str | None = None) -> None:
    """Show a diff through delta when writing to a terminal; plain text otherwise."""
    if _is_terminal():
        sys.stdout.flush()
        if delta.page(text, side_by_side=cfg.get_bool("diff.side_by_side", cwd), cwd=cwd):
            return
    emit_raw(text)
