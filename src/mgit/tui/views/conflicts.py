from __future__ import annotations

from rich.syntax import Syntax
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import DataTable, Static, TabbedContent, TabPane

from ...core import conflicts
from ...core.merge_rebase import list_conflicts
from ...git.runner import GitCommandError
from ..widgets.diff_view import DiffView

IDLE_MESSAGE = "No merge, rebase, cherry-pick or revert in progress."
_MODE_TITLES = {"direct": "1 ↔ 2", "base-ours": "base → 1", "base-theirs": "base → 2"}


def _side_renderable(path: str | None, content: conflicts.SideContent | None):
    if path is None or content is None:
        return Text("")
    if content.missing:
        return Text("(deleted on this side)", style="dim italic")
    if content.binary:
        return Text("(binary file)", style="dim italic")
    lexer = Syntax.guess_lexer(path, content.text)
    return Syntax(content.text, lexer, line_numbers=True, background_color="default")


class ConflictsView(Widget):
    DEFAULT_CSS = """
    ConflictsView { height: 1fr; }
    ConflictsView #conflicts-headline { padding: 0 1; text-style: bold; }
    ConflictsView #conflicts-table { height: auto; max-height: 8; }
    ConflictsView #conflicts-panes { height: 1fr; }
    """
    BINDINGS = [
        ("m", "cycle_mode", "Diff mode"),
        ("r", "refresh_conflicts", "Refresh"),
    ]
    can_focus = True

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd
        self.context: conflicts.ConflictContext | None = None
        self.files: list[tuple[str, str]] = []
        self.mode = "direct"
        self._load_generation = 0

    def compose(self) -> ComposeResult:
        yield Static(IDLE_MESSAGE, id="conflicts-headline")
        table = DataTable(id="conflicts-table", cursor_type="row")
        table.add_column("File", key="path")
        table.add_column("Status", key="status")
        yield table
        with TabbedContent(id="conflicts-panes"):
            with TabPane("1", id="side-ours-pane"):
                with VerticalScroll():
                    yield Static(id="side-ours-body")
            with TabPane("2", id="side-theirs-pane"):
                with VerticalScroll():
                    yield Static(id="side-theirs-body")
            with TabPane(self._diff_title(), id="side-diff-pane"):
                yield DiffView(cwd=self.cwd, id="conflicts-diff")

    def on_mount(self) -> None:
        self.refresh_conflicts()

    @property
    def selected_path(self) -> str | None:
        row = self.query_one("#conflicts-table", DataTable).cursor_row
        return self.files[row][0] if 0 <= row < len(self.files) else None

    def action_refresh_conflicts(self) -> None:
        self.refresh_conflicts()

    @work(thread=True, exclusive=True, group="conflicts-refresh")
    def refresh_conflicts(self) -> None:
        try:
            context = conflicts.conflict_context(self.cwd)
            files = list_conflicts(self.cwd) if context else []
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self._apply_state, context, files)

    def _headline(self) -> str:
        if self.context is None:
            return IDLE_MESSAGE
        if not self.files:
            return f"{self.context.headline} — all conflicts resolved, press C to continue"
        return f"{self.context.headline} — {len(self.files)} unresolved"

    def _apply_state(self, context: conflicts.ConflictContext | None, files: list[tuple[str, str]]) -> None:
        previous = self.selected_path
        self.context, self.files = context, files
        self.query_one("#conflicts-headline", Static).update(Text(self._headline()))
        panes = self.query_one("#conflicts-panes", TabbedContent)
        panes.get_tab("side-ours-pane").label = Text(f"1 · {context.ours_label}" if context else "1")
        panes.get_tab("side-theirs-pane").label = Text(f"2 · {context.theirs_label}" if context else "2")
        table = self.query_one("#conflicts-table", DataTable)
        table.clear()
        for path, label in files:
            table.add_row(Text(path), Text(label), key=path)
        paths = [path for path, _ in files]
        if previous in paths:
            table.move_cursor(row=paths.index(previous))
        self._load_selected()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "conflicts-table":
            self._load_selected()

    def _load_selected(self) -> None:
        self._load_generation += 1
        path = self.selected_path
        if path is None:
            self._show_file(self._load_generation, None, None, None, "")
            return
        self._load_file(path, self.mode, self._load_generation)

    @work(thread=True, group="conflicts-load")
    def _load_file(self, path: str, mode: str, generation: int) -> None:
        try:
            ours = conflicts.side_content(path, "ours", self.cwd)
            theirs = conflicts.side_content(path, "theirs", self.cwd)
            diff_text = conflicts.side_diff(path, mode, self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            return
        self.app.call_from_thread(self._show_file, generation, path, ours, theirs, diff_text)

    def _show_file(self, generation, path, ours, theirs, diff_text: str) -> None:
        # A newer selection or refresh supersedes this load.
        if generation != self._load_generation:
            return
        self.query_one("#side-ours-body", Static).update(_side_renderable(path, ours))
        self.query_one("#side-theirs-body", Static).update(_side_renderable(path, theirs))
        self.query_one("#conflicts-diff", DiffView).set_diff(diff_text)

    def _diff_title(self) -> str:
        return f"Diff · {_MODE_TITLES[self.mode]}"

    def action_cycle_mode(self) -> None:
        modes = conflicts.DIFF_MODES
        self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]
        panes = self.query_one("#conflicts-panes", TabbedContent)
        panes.get_tab("side-diff-pane").label = Text(self._diff_title())
        panes.active = "side-diff-pane"
        self._load_selected()
