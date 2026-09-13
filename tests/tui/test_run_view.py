from textual.app import App, ComposeResult
from textual.widgets import Input, OptionList

from mgit.tui.run.discovery import discover_commands
from mgit.cli.main import app as mgit_cli_app
from mgit.tui.views.run import RunView


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd
        self.chosen = []

    def compose(self) -> ComposeResult:
        yield RunView(self.cwd)

    def on_run_view_command_chosen(self, message) -> None:
        self.chosen.append(message.entry)


async def test_run_view_lists_all_commands(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test():
        option_list = app.query_one("#run-commands", OptionList)
        assert option_list.option_count == len(discover_commands(mgit_cli_app))


async def test_run_view_search_filters_list(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        search = app.query_one("#run-search", Input)
        search.value = "branch new"
        search.post_message(Input.Changed(search, "branch new"))
        await pilot.pause()
        option_list = app.query_one("#run-commands", OptionList)
        assert option_list.option_count == 1


async def test_run_view_selecting_an_option_reports_the_entry(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["branch", "new"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()
        assert app.chosen == [target]
