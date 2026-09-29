"""Optional rendering of diffs through the external `delta` pager."""
from __future__ import annotations

import shutil
import subprocess


def delta_available() -> bool:
    return shutil.which("delta") is not None


def _layout_args(side_by_side: bool) -> list[str]:
    # delta has no flag that overrides `side-by-side = true` from gitconfig,
    # so the unified layout ignores gitconfig entirely.
    return ["--side-by-side"] if side_by_side else ["--no-gitconfig"]


def render(diff_text: str, width: int, side_by_side: bool = True, cwd: str | None = None) -> str | None:
    """delta's ANSI rendering of diff_text at `width` columns, or None if delta can't be used."""
    if not diff_text:
        return ""
    if not delta_available():
        return None
    args = ["delta", "--paging=never", f"--width={max(width, 1)}", *_layout_args(side_by_side)]
    try:
        result = subprocess.run(
            args, input=diff_text + "\n", cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def page(diff_text: str, side_by_side: bool = True, cwd: str | None = None) -> bool:
    """Show diff_text through delta on the attached terminal (delta pages it). False if delta can't be used."""
    if not delta_available():
        return False
    try:
        subprocess.run(
            ["delta", *_layout_args(side_by_side)], input=diff_text + "\n", cwd=cwd,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return False
    return True
