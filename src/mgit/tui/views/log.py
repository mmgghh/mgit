from __future__ import annotations

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from ...core.log_search import Commit, LogFilter, diff, search
from ...git.runner import GitCommandError


class DiffScreen(ModalScreen[None]):
    BINDINGS = [("escape", "dismiss_screen", "Close")]

    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(Text(self._text))

    def action_dismiss_screen(self) -> None:
        self.dismiss()


class LogView(Widget):
    BINDINGS = [
        ("r", "refresh_log", "Refresh"),
        ("d", "show_selected_diff", "Diff"),
    ]

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd
        self._commits: list[Commit] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="author", id="filter-author")
            yield Input(placeholder="since", id="filter-since")
            yield Input(placeholder="until", id="filter-until")
            yield Input(placeholder="grep", id="filter-grep")
        table = DataTable(id="log-table", cursor_type="row")
        table.add_column("SHA", key="sha")
        table.add_column("Author", key="author")
        table.add_column("Date", key="date")
        table.add_column("Subject", key="subject")
        yield table

    def on_mount(self) -> None:
        self.refresh_log()

    def action_refresh_log(self) -> None:
        self.refresh_log()

    def action_show_selected_diff(self) -> None:
        table = self.query_one("#log-table", DataTable)
        row_index = table.cursor_coordinate.row
        if 0 <= row_index < len(self._commits):
            self.show_diff(self._commits[row_index].sha)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.refresh_log()

    def _current_filter(self) -> LogFilter:
        return LogFilter(
            author=self.query_one("#filter-author", Input).value or None,
            since=self.query_one("#filter-since", Input).value or None,
            until=self.query_one("#filter-until", Input).value or None,
            grep=self.query_one("#filter-grep", Input).value or None,
        )

    @work(thread=True, exclusive=True)
    def refresh_log(self) -> None:
        log_filter = self.app.call_from_thread(self._current_filter)
        try:
            commits = search(log_filter, self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self._populate, commits)

    def _populate(self, commits: list[Commit]) -> None:
        self._commits = commits
        table = self.query_one("#log-table", DataTable)
        table.clear()
        for commit in commits:
            table.add_row(
                Text(commit.short_sha),
                Text(commit.author),
                Text(commit.date),
                Text(commit.subject),
                key=commit.sha,
            )

    @work(thread=True, exclusive=True)
    def show_diff(self, sha: str) -> None:
        try:
            text = diff(ref_a=f"{sha}^", ref_b=sha, cwd=self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self.app.push_screen, DiffScreen(text))
