# tests/tui/test_log_view.py
from pathlib import Path
import subprocess

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Static

from mgit.tui.views.log import LogView


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        yield LogView(self.cwd)


def _commit(repo, filename, content, message, author=None):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    args = ["git", "commit", "-m", message]
    if author:
        args += ["--author", author]
    subprocess.run(args, cwd=repo, check=True, capture_output=True)


async def test_log_view_lists_commits(tmp_git_repo):
    _commit(tmp_git_repo, "a.txt", "a\n", "add a")
    app = _Harness(tmp_git_repo)
    async with app.run_test():
        await app.workers.wait_for_complete()
        table = app.query_one("#log-table", DataTable)
        subjects = [table.get_row_at(i)[3].plain for i in range(table.row_count)]
        assert "add a" in subjects
        assert "init" in subjects


async def test_author_filter_narrows_results(tmp_git_repo):
    _commit(tmp_git_repo, "a.txt", "a\n", "from alice", author="Alice <alice@example.com>")
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        app.query_one("#filter-author", Input).focus()
        for ch in "alice":
            await pilot.press(ch)
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        table = app.query_one("#log-table", DataTable)
        subjects = [table.get_row_at(i)[3].plain for i in range(table.row_count)]
        assert subjects == ["from alice"]


async def test_d_key_opens_diff_screen(tmp_git_repo):
    _commit(tmp_git_repo, "a.txt", "a\n", "add a")
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        app.query_one("#log-table", DataTable).focus()
        await pilot.press("d")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert len(app.screen_stack) == 2
        modal_static = app.screen.query_one(Static)
        assert "a.txt" in modal_static.content.plain


async def test_d_key_on_root_commit_shows_diff(tmp_git_repo):
    _commit(tmp_git_repo, "a.txt", "a\n", "add a")
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        table = app.query_one("#log-table", DataTable)
        table.focus()
        for _ in range(table.row_count - 1):
            await pilot.press("down")
        await pilot.press("d")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert len(app.screen_stack) == 2
        modal_static = app.screen.query_one(Static)
        assert "README.md" in modal_static.content.plain
