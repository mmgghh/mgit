from __future__ import annotations

import os
import shlex
import subprocess

from rich.markup import escape
from rich.syntax import Syntax
from rich.text import Text
from textual import work
from textual.app import ComposeResult, SuspendNotSupported
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import DataTable, Static, TabbedContent, TabPane

from ...core import conflicts
from ...core.merge_rebase import list_conflicts
from ...git.runner import GitCommandError
from ..widgets.diff_view import DiffView
from .run import ConfirmScreen

IDLE_MESSAGE = "No merge, rebase, cherry-pick or revert in progress."
_MODE_TITLES = {"direct": "1 ↔ 2", "base-ours": "base → 1", "base-theirs": "base → 2"}


def _launch_editor(file_path: str) -> None:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    subprocess.run([*shlex.split(editor), file_path])


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
        Binding("1", "take_side('ours')", "Take 1"),
        Binding("2", "take_side('theirs')", "Take 2"),
        Binding("e", "edit", "Edit"),
        Binding("a", "mark_resolved", "Resolved"),
        Binding("m", "cycle_mode", "Diff mode"),
        Binding("C", "continue_operation", "Continue"),
        Binding("A", "abort_operation", "Abort"),
        Binding("r", "refresh_conflicts", "Refresh"),
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

    def _require_context(self) -> conflicts.ConflictContext | None:
        if self.context is None:
            self.app.notify("Nothing in progress", severity="warning")
        return self.context

    def _require_selected(self) -> str | None:
        if self._require_context() is None:
            return None
        path = self.selected_path
        if path is None:
            self.app.notify("No conflicted file selected", severity="warning")
        return path

    def action_take_side(self, side: str) -> None:
        path = self._require_selected()
        if path is None:
            return
        label = self.context.ours_label if side == "ours" else self.context.theirs_label
        self.app.push_screen(
            ConfirmScreen(f"Replace {escape(path)} with {escape(label)} and mark it resolved?"),
            lambda confirmed: self._on_take_confirmed(confirmed, path, side),
        )

    def _on_take_confirmed(self, confirmed: bool | None, path: str, side: str) -> None:
        if confirmed:
            self._run_action(conflicts.take_side, path, side)

    def action_mark_resolved(self) -> None:
        path = self._require_selected()
        if path is None:
            return
        if conflicts.has_conflict_markers(path, self.cwd):
            self.app.push_screen(
                ConfirmScreen(f"{escape(path)} still contains conflict markers. Mark it resolved anyway?"),
                lambda confirmed: self._on_resolve_confirmed(confirmed, path),
            )
            return
        self._run_action(conflicts.mark_resolved, path)

    def _on_resolve_confirmed(self, confirmed: bool | None, path: str) -> None:
        if confirmed:
            self._run_action(conflicts.mark_resolved, path)

    def action_edit(self) -> None:
        path = self._require_selected()
        if path is None:
            return
        try:
            target = str(conflicts.file_path(path, self.cwd))
            with self.app.suspend():
                _launch_editor(target)
        except SuspendNotSupported:
            self.app.notify("This terminal can't hand over to an editor", severity="error")
            return
        except (GitCommandError, OSError) as exc:
            self.app.notify(str(exc), severity="error", markup=False)
            return
        self.refresh_conflicts()

    def action_continue_operation(self) -> None:
        if self._require_context() is None:
            return
        if self.files:
            self.app.notify(f"{len(self.files)} file(s) still unresolved", severity="warning")
            return
        self._continue()

    @work(thread=True, group="conflicts-action")
    def _continue(self) -> None:
        try:
            conflicts.continue_operation(self.cwd)
        except GitCommandError as exc:
            try:
                remaining = list_conflicts(self.cwd)
            except GitCommandError:
                remaining = []
            if remaining:
                message = f"Continued, then stopped on new conflicts in {len(remaining)} file(s)"
                self.app.call_from_thread(self.app.notify, message, severity="warning")
            else:
                self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
        self.app.call_from_thread(self._after_action)

    def action_abort_operation(self) -> None:
        context = self._require_context()
        if context is None:
            return
        self.app.push_screen(
            ConfirmScreen(f"Abort the {context.operation}? Resolutions made so far will be lost."),
            self._on_abort_confirmed,
        )

    def _on_abort_confirmed(self, confirmed: bool | None) -> None:
        if confirmed:
            self._run_action(conflicts.abort_operation)

    def _run_action(self, fn, *args) -> None:
        self._action(fn, args)

    @work(thread=True, group="conflicts-action")
    def _action(self, fn, args: tuple) -> None:
        try:
            fn(*args, cwd=self.cwd)
        except GitCommandError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
        self.app.call_from_thread(self._after_action)

    def _after_action(self) -> None:
        # Inside MgitApp, refresh_other_views also refreshes this view.
        if hasattr(self.app, "refresh_other_views"):
            self.app.refresh_other_views()
        else:
            self.refresh_conflicts()
