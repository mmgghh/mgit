# tests/tui/test_app.py
from textual.widgets import TabbedContent, TabPane

from mgit.tui.app import MgitApp


async def test_app_shows_four_tabs(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test():
        tab_ids = [pane.id for pane in app.query(TabPane)]
        assert tab_ids == ["run-tab", "status-tab", "branches-tab", "log-tab"]


async def test_app_tab_content_is_rendered(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        tabbed_content = app.query_one(TabbedContent)
        for tab_id in ("run-tab", "status-tab", "branches-tab", "log-tab"):
            tabbed_content.active = tab_id
            await pilot.pause()
            await app.workers.wait_for_complete()
            pane = app.query_one(f"#{tab_id}", TabPane)
            assert pane.size.height > 0


async def test_app_shows_message_when_not_a_git_repo(tmp_path):
    app = MgitApp(str(tmp_path))
    async with app.run_test():
        assert len(app.query(TabPane)) == 0
        assert app.query_one("#not-a-repo")


async def test_running_a_mutating_command_refreshes_other_tabs(tmp_git_repo):
    from textual.widgets import Button, DataTable, Input, OptionList, TabbedContent

    from mgit.tui.run.discovery import discover_commands
    from mgit.cli.main import app as mgit_cli_app
    from mgit.tui.views.branches import BranchesView
    from mgit.tui.views.run import RunView
    from mgit.tui.views.status import StatusView

    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()

        run_view = app.query_one(RunView)
        entries = discover_commands(mgit_cli_app)
        target_index = next(i for i, e in enumerate(entries) if e.path == ["branch", "new"])
        option_list = run_view.query_one("#run-commands", OptionList)
        option_list.highlighted = target_index
        option_list.action_select()
        await pilot.pause()

        form = app.screen
        form.query(Input)[0].value = "refreshed-branch"
        form.query_one("#run-button", Button).press()
        await app.workers.wait_for_complete()
        await pilot.pause()
        form.dismiss()
        await pilot.pause()

        app.query_one(TabbedContent).active = "branches-tab"
        await pilot.pause()
        await app.workers.wait_for_complete()
        table = app.query_one("#branches-table", DataTable)
        names = [table.get_row_at(i)[1].plain for i in range(table.row_count)]
        assert "refreshed-branch" in names
