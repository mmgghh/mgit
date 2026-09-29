# tests/tui/test_app.py
from textual.widgets import Input, TabbedContent, TabPane

from mgit.tui.app import HelpScreen, MgitApp


MAIN_TABS = ["run-tab", "status-tab", "conflicts-tab", "branches-tab", "log-tab"]


def _main_tab_ids(app):
    # The Conflicts view nests its own panes; main tabs are the ones ending in "-tab".
    return [pane.id for pane in app.query(TabPane) if pane.id.endswith("-tab")]


async def test_app_shows_five_tabs(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test():
        assert _main_tab_ids(app) == MAIN_TABS


async def test_app_tab_content_is_rendered(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        tabbed_content = app.query_one(TabbedContent)
        for tab_id in MAIN_TABS:
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


async def test_f1_opens_and_closes_help(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        await pilot.press("f1")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("f1")
        assert not isinstance(app.screen, HelpScreen)


async def test_ctrl_b_moves_focus_back(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        search = app.query_one("#run-search", Input)
        search.focus()
        await pilot.pause()
        await pilot.press("tab")
        assert app.focused is not search
        await pilot.press("ctrl+b")
        assert app.focused is search


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
        await pilot.pause()
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


async def test_app_opens_on_run_tab_normally(tmp_git_repo):
    app = MgitApp(tmp_git_repo)
    async with app.run_test():
        assert app.query_one(TabbedContent).active == "run-tab"


async def test_app_opens_on_conflicts_tab_during_a_conflict(rebase_conflict_repo):
    app = MgitApp(rebase_conflict_repo)
    async with app.run_test():
        assert app.query_one(TabbedContent).active == "conflicts-tab"


async def test_refresh_other_views_picks_up_new_conflicts(tmp_git_repo, git_commit):
    import subprocess

    from mgit.tui.views.conflicts import ConflictsView

    app = MgitApp(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        repo = tmp_git_repo
        git_commit(repo, "file.txt", "base\n", "add file")
        subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
        git_commit(repo, "file.txt", "feature\n", "feature change")
        subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
        git_commit(repo, "file.txt", "main\n", "main change")
        subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
        app.refresh_other_views()
        for _ in range(3):
            await pilot.pause()
            await app.workers.wait_for_complete()
        assert app.query_one(ConflictsView).files == [("file.txt", "both modified")]


def test_help_mentions_conflict_keys():
    from mgit.tui.app import HELP_TEXT

    assert "Conflicts" in HELP_TEXT
    assert "take side 1 / side 2" in HELP_TEXT
