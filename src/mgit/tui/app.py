from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from ..git.repo import is_git_repo
from .views.branches import BranchesView
from .views.log import LogView
from .views.run import RunView
from .views.status import StatusView

HELP_TEXT = """\
[bold]Navigation[/bold]
  tab            next field
  shift+tab      previous field ([dim]ctrl+b if your terminal eats shift+tab[/dim])
  escape         back / close
  ctrl+r         run ([dim]a command's form[/dim])
  r              refresh ([dim]Status, Branches, Log tabs[/dim])
  d              show diff ([dim]Log tab[/dim])

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

    def compose(self) -> ComposeResult:
        yield Header()
        if not is_git_repo(self.cwd):
            yield Static("Not a git repository.", id="not-a-repo")
        else:
            with TabbedContent(initial="run-tab"):
                with TabPane("Run", id="run-tab"):
                    yield RunView(self.cwd)
                with TabPane("Status", id="status-tab"):
                    yield StatusView(self.cwd)
                with TabPane("Branches", id="branches-tab"):
                    yield BranchesView(self.cwd)
                with TabPane("Log", id="log-tab"):
                    yield LogView(self.cwd)
        yield Footer()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def refresh_other_views(self) -> None:
        self.query_one(StatusView).refresh_status()
        self.query_one(BranchesView).refresh_branches()
        self.query_one(LogView).refresh_log()
