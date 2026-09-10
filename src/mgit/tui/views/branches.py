# src/mgit/tui/views/branches.py
from __future__ import annotations

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable

from ...core import branches as branches_core
from ...git.repo import current_branch
from ...git.runner import GitCommandError


class BranchesView(Widget):
    BINDINGS = [("r", "refresh_branches", "Refresh")]

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        table = DataTable(id="branches-table", cursor_type="row")
        table.add_column("", key="current")
        table.add_column("Branch", key="name")
        yield table

    def on_mount(self) -> None:
        self.refresh_branches()

    def action_refresh_branches(self) -> None:
        self.refresh_branches()

    @work(thread=True, exclusive=True)
    def refresh_branches(self) -> None:
        try:
            names = branches_core.list_branches(self.cwd)
            current = current_branch(self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self._populate, names, current)

    def _populate(self, names: list[str], current: str | None) -> None:
        table = self.query_one("#branches-table", DataTable)
        table.clear()
        for name in names:
            marker = "*" if name == current else ""
            table.add_row(marker, Text(name), key=name)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.switch_to(event.row_key.value)

    @work(thread=True, exclusive=True)
    def switch_to(self, name: str) -> None:
        try:
            branches_core.switch_branch(name, self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self.app.notify, f"Switched to {name}", markup=False)
        self.app.call_from_thread(self.refresh_branches)
