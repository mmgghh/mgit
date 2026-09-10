# src/mgit/tui/views/status.py
from __future__ import annotations

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ...core import repo_info
from ...core import status as status_core
from ...git.runner import GitCommandError


def _render_status(info: dict, tree: status_core.WorkingTreeStatus) -> Text:
    text = Text()
    text.append(f"Root: {info['root']}\n")
    text.append(f"Branch: {info['branch'] or '(detached HEAD)'}\n")
    if info["in_progress"]:
        text.append(f"In progress: {info['in_progress']}\n", style="bold red")
    text.append("Remotes:\n")
    for remote in info["remotes"]:
        text.append(f"  {remote}\n")
    text.append(f"\nStaged ({len(tree.staged)}):\n", style="bold green")
    for entry in tree.staged:
        text.append(f"  {entry.code} {entry.path}\n")
    text.append(f"\nUnstaged ({len(tree.unstaged)}):\n", style="bold yellow")
    for entry in tree.unstaged:
        text.append(f"  {entry.code} {entry.path}\n")
    text.append(f"\nUntracked ({len(tree.untracked)}):\n", style="bold blue")
    for path in tree.untracked:
        text.append(f"  {path}\n")
    return text


class StatusView(Widget):
    BINDINGS = [("r", "refresh_status", "Refresh")]
    can_focus = True

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        yield Static(id="status-body")

    def on_mount(self) -> None:
        self.refresh_status()

    def action_refresh_status(self) -> None:
        self.refresh_status()

    @work(thread=True, exclusive=True)
    def refresh_status(self) -> None:
        try:
            info = repo_info.summary(self.cwd)
            tree = status_core.working_tree_status(self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        text = _render_status(info, tree)
        self.app.call_from_thread(self._apply, text)

    def _apply(self, text: Text) -> None:
        self.query_one("#status-body", Static).update(text)
