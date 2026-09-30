from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from ..core.merge_rebase import list_conflicts
from ..git.repo import is_git_repo
from ..git.runner import GitCommandError
from .views.branches import BranchesView
from .views.conflicts import ConflictsView
from .views.log import LogView
from .views.run import RunView
from .views.status import StatusView

HELP_TEXT = """\
[bold]Navigation[/bold]
  tab            next field
  shift+tab      previous field ([dim]ctrl+b if your terminal eats shift+tab[/dim])
  escape         back / close
  ctrl+r         run ([dim]a command's form[/dim])
  r              refresh ([dim]Status, Conflicts, Branches, Log tabs[/dim])
  d              show diff ([dim]Log tab[/dim])

[bold]Conflicts tab[/bold]
  1 / 2          take side 1 / side 2 for the selected file
  e              edit the file in $VISUAL / $EDITOR
  a              mark the file resolved
  m              cycle the diff: 1 ↔ 2, base → 1, base → 2
  C / A          continue / abort the merge, rebase, cherry-pick or revert

[bold]F1[/bold]  toggles this help"""


class HelpScreen(ModalScreen):
    """Keybinding reference, opened with F1 from anywhere in the app."""

    BINDINGS = [("escape,f1", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT, id="help-body")


class MgitApp(App):
    TITLE = "mgit"
    BINDINGS = [
        Binding("f1", "help", "Help"),
        # ctrl+b is a single control byte, not an escape sequence, so it
        # survives terminals/multiplexers that mangle shift+tab in transit.
        Binding("ctrl+b", "focus_previous", "Focus previous", show=False),
    ]

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd
        self._start_tab: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        if not is_git_repo(self.cwd):
            yield Static("Not a git repository.", id="not-a-repo")
        else:
            self._start_tab = self._initial_tab()
            with TabbedContent(initial=self._start_tab):
                with TabPane("Run", id="run-tab"):
                    yield RunView(self.cwd)
                with TabPane("Status", id="status-tab"):
                    yield StatusView(self.cwd)
                with TabPane("Conflicts", id="conflicts-tab"):
                    yield ConflictsView(self.cwd)
                with TabPane("Branches", id="branches-tab"):
                    yield BranchesView(self.cwd)
                with TabPane("Log", id="log-tab"):
                    yield LogView(self.cwd)
        yield Footer()

    def on_mount(self) -> None:
        # Opening on Conflicts means there's work to do: focus the file list
        # so its keys (1/2/e/a/m/C/A) work without tabbing in first.
        if self._start_tab == "conflicts-tab":
            self.query_one("#conflicts-table").focus()

    def _initial_tab(self) -> str:
        try:
            return "conflicts-tab" if list_conflicts(self.cwd) else "run-tab"
        except GitCommandError:
            return "run-tab"

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def refresh_other_views(self) -> None:
        self.query_one(StatusView).refresh_status()
        self.query_one(ConflictsView).refresh_conflicts()
        self.query_one(BranchesView).refresh_branches()
        self.query_one(LogView).refresh_log()
