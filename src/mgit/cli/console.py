from __future__ import annotations

from rich.console import Console
from rich.markup import escape as esc

console = Console()
err_console = Console(stderr=True)


def emit_raw(text: str) -> None:
    console.print(text, markup=False, highlight=False, soft_wrap=True)
