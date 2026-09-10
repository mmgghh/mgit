from __future__ import annotations

from .console import err_console, esc


def tui_cmd() -> None:
    """Launch the interactive TUI."""
    try:
        from ..tui.app import MgitApp
    except ImportError:
        err_console.print(
            f"[bold red]Error:[/bold red] the TUI needs the 'tui' extra. "
            f"Install it with: pip install mgit{esc('[tui]')}"
        )
        raise SystemExit(1)
    MgitApp().run()
