# tests/tui/test_status_view.py
from pathlib import Path
import subprocess

from textual.app import App, ComposeResult

from mgit.core import status as status_core
from mgit.tui.views.status import StatusView, _render_status


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd

    def compose(self) -> ComposeResult:
        yield StatusView(self.cwd)


def test_render_status_includes_in_progress_banner():
    info = {"root": "/r", "branch": "main", "in_progress": "rebase", "remotes": []}
    tree = status_core.WorkingTreeStatus(staged=[], unstaged=[], untracked=[])
    text = _render_status(info, tree)
    assert "rebase" in text.plain


async def test_status_view_shows_branch_and_staged_file(tmp_git_repo):
    Path(tmp_git_repo, "new.txt").write_text("hi\n")
    subprocess.run(["git", "add", "new.txt"], cwd=tmp_git_repo, check=True)

    app = _Harness(tmp_git_repo)
    async with app.run_test():
        await app.workers.wait_for_complete()
        body = app.query_one("#status-body")
        rendered = body.content.plain
        assert "main" in rendered
        assert "new.txt" in rendered


async def test_r_key_refreshes_status(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        Path(tmp_git_repo, "later.txt").write_text("hi\n")
        subprocess.run(["git", "add", "later.txt"], cwd=tmp_git_repo, check=True)
        await pilot.press("r")
        await app.workers.wait_for_complete()
        body = app.query_one("#status-body")
        assert "later.txt" in body.content.plain
