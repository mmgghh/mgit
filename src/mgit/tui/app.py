from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from ..git.repo import is_git_repo
from .views.branches import BranchesView
from .views.status import StatusView


class MgitApp(App):
    TITLE = "mgit"

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        yield Header()
        if not is_git_repo(self.cwd):
            yield Static("Not a git repository.", id="not-a-repo")
        else:
            with TabbedContent(initial="status-tab"):
                with TabPane("Status", id="status-tab"):
                    yield StatusView(self.cwd)
                with TabPane("Branches", id="branches-tab"):
                    yield BranchesView(self.cwd)
                with TabPane("Log", id="log-tab"):
                    yield Static("Log", id="log-placeholder")
        yield Footer()
