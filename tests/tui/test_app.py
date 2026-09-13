# tests/tui/test_app.py
from textual.widgets import TabbedContent, TabPane

from mgit.tui.app import MgitApp


async def test_app_shows_three_tabs(tmp_git_repo):
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
