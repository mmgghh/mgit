from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from ...cli.main import app as mgit_cli_app
from ..run.discovery import CommandEntry, discover_commands


class RunView(Widget):
    DEFAULT_CSS = "RunView { height: 1fr; }"
    can_focus = True

    class CommandChosen(Message):
        bubble = True

        def __init__(self, entry: CommandEntry) -> None:
            self.entry = entry
            super().__init__()

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd
        self._entries = discover_commands(mgit_cli_app)
        self._filtered = self._entries

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search mgit commands...", id="run-search")
        yield OptionList(*self._options(self._entries), id="run-commands")

    def _options(self, entries: list[CommandEntry]):
        for i, entry in enumerate(entries):
            yield Option(f"{' '.join(entry.path)}  {entry.help}", id=str(i))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "run-search":
            return
        query = event.value.strip().lower()

        def matches(entry: CommandEntry) -> bool:
            path_str = " ".join(entry.path).lower()
            help_str = entry.help.lower()
            # Check if the query appears as a substring in the path (word boundary aware)
            # Only matches if query is not a substring of a hyphenated component
            # E.g., "branch delete" matches "branch delete" but not "branch delete-remote"
            path_lower = [p.lower() for p in entry.path]
            query_words = query.split()
            # First check: query words appear consecutively as complete components
            for i in range(len(path_lower) - len(query_words) + 1):
                if path_lower[i:i + len(query_words)] == query_words:
                    return True
            # Second check: query appears in help text only (not in path)
            if query in help_str:
                return True
            return False

        self._filtered = [e for e in self._entries if matches(e)]
        option_list = self.query_one("#run-commands", OptionList)
        option_list.clear_options()
        option_list.add_options(self._options(self._filtered))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "run-commands":
            return
        index = int(event.option.id)
        self.post_message(self.CommandChosen(self._filtered[index]))
