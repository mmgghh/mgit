from textual.app import App, ComposeResult
from textual.widgets import Button, Input, OptionList, RichLog, Select, Static, Switch

from mgit.tui.run.discovery import discover_commands
from mgit.cli.main import app as mgit_cli_app
from mgit.tui.views.run import RunView, CommandFormScreen, ConfirmScreen
from mgit.core.branches import list_branches


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd
        self.chosen = []

    def compose(self) -> ComposeResult:
        yield RunView(self.cwd)

    def on_run_view_command_chosen(self, message) -> None:
        self.chosen.append(message.entry)
        self.push_screen(CommandFormScreen(message.entry, self.cwd))


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


async def test_selecting_a_command_opens_its_form(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["branch", "delete"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, CommandFormScreen)
        assert isinstance(screen.query_one(Select), Select)  # git-aware "name" field
        assert isinstance(screen.query_one(Switch), Switch)  # "force" flag


async def test_form_preview_updates_when_a_flag_is_toggled(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["branch", "delete"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()

        screen = app.screen
        screen.query_one(Switch).value = True
        await pilot.pause()
        preview = screen.query_one("#run-preview", Static).renderable
        assert "--force" in str(preview)


async def test_confirm_gated_command_hides_its_yes_flag_and_shows_no_switch(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["nuke"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, CommandFormScreen)
        assert len(screen.query(Switch)) == 0  # "yes" flag is suppressed, not shown as a toggle


async def test_running_confirm_gated_command_shows_confirm_screen_first(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["tag", "delete"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()

        form = app.screen
        form.query_one("#run-button", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)


async def test_running_a_command_streams_output_and_takes_effect(tmp_git_repo):
    entries = discover_commands(mgit_cli_app)
    target = next(e for e in entries if e.path == ["branch", "new"])

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        option_list = app.query_one("#run-commands", OptionList)
        index = next(i for i, e in enumerate(entries) if e.path == target.path)
        option_list.highlighted = index
        option_list.action_select()
        await pilot.pause()

        form = app.screen
        text_inputs = form.query(Input)
        text_inputs[0].value = "from-run-tab"  # "name" argument

        form.query_one("#run-button", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        output = form.query_one("#run-output", RichLog)
        assert output.lines  # something was written
        assert "from-run-tab" in list_branches(tmp_git_repo)
