# tests/tui/test_branches_view.py
import subprocess

from textual.app import App, ComposeResult
from textual.widgets import DataTable

from mgit.git.repo import current_branch
from mgit.tui.views.branches import BranchesView


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        yield BranchesView(self.cwd)


async def test_branches_table_lists_and_marks_current(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)

    app = _Harness(tmp_git_repo)
    async with app.run_test():
        await app.workers.wait_for_complete()
        table = app.query_one("#branches-table", DataTable)
        rows = [(table.get_row_at(i)[0], table.get_row_at(i)[1].plain) for i in range(table.row_count)]
        assert rows == [("", "feature"), ("*", "main")]


async def test_enter_switches_to_selected_branch(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)

    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        # cursor starts at row 0, which is "feature" (alphabetically before "main")
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        assert current_branch(tmp_git_repo) == "feature"


async def test_r_key_refreshes_branch_list(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        subprocess.run(["git", "checkout", "-b", "new-branch"], cwd=tmp_git_repo, check=True, capture_output=True)
        await pilot.press("r")
        await app.workers.wait_for_complete()
        table = app.query_one("#branches-table", DataTable)
        names = [table.get_row_at(i)[1].plain for i in range(table.row_count)]
        assert "new-branch" in names
