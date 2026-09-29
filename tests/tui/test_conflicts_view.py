import subprocess
from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static, TabbedContent

from mgit.git import delta
from mgit.tui.views.conflicts import IDLE_MESSAGE, ConflictsView
from mgit.tui.widgets.diff_view import DiffView


class _Harness(App):
    def __init__(self, cwd):
        super().__init__()
        self.cwd = cwd
        self.notices: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        yield ConflictsView(self.cwd)

    def notify(self, message, *, severity="information", **kwargs):
        self.notices.append((str(message), severity))
        super().notify(message, severity=severity, **kwargs)


async def _settle(app, pilot):
    for _ in range(3):
        await pilot.pause()
        await app.workers.wait_for_complete()
    await pilot.pause()


def _headline(app):
    return app.query_one("#conflicts-headline", Static).content.plain


def _tab_label(app, pane_id):
    return app.query_one("#conflicts-panes", TabbedContent).get_tab(pane_id).label.plain


def _rows(app):
    table = app.query_one("#conflicts-table", DataTable)
    return [table.get_row_at(i)[0].plain for i in range(table.row_count)]


async def test_idle_repo_shows_idle_message(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        assert _headline(app) == IDLE_MESSAGE
        assert _rows(app) == []


async def test_rebase_conflict_is_labeled(rebase_conflict_repo, monkeypatch):
    monkeypatch.setattr(delta, "render", lambda *a, **k: None)
    app = _Harness(rebase_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        assert "Rebasing feature/login onto main (step 2/2)" in _headline(app)
        assert "1 unresolved" in _headline(app)
        assert _rows(app) == ["file.txt"]
        assert _tab_label(app, "side-ours-pane").startswith("1 · Upstream: main (")
        assert _tab_label(app, "side-theirs-pane").startswith("2 · Your commit: ")
        ours = app.query_one("#side-ours-body", Static).content
        theirs = app.query_one("#side-theirs-body", Static).content
        assert isinstance(ours, Syntax) and ours.code == "main\n"
        assert isinstance(theirs, Syntax) and theirs.code == "feature\n"
        diff_text = app.query_one("#conflicts-diff", DiffView).text
        assert "-main" in diff_text and "+feature" in diff_text


async def test_m_cycles_diff_modes(merge_conflict_repo, monkeypatch):
    monkeypatch.setattr(delta, "render", lambda *a, **k: None)
    app = _Harness(merge_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        app.query_one("#conflicts-table", DataTable).focus()
        await pilot.press("m")
        await _settle(app, pilot)
        view = app.query_one(ConflictsView)
        assert view.mode == "base-ours"
        assert _tab_label(app, "side-diff-pane") == "Diff · base → 1"
        assert app.query_one("#conflicts-panes", TabbedContent).active == "side-diff-pane"
        diff_text = app.query_one("#conflicts-diff", DiffView).text
        assert "-base" in diff_text and "+main" in diff_text
        await pilot.press("m", "m")
        await _settle(app, pilot)
        assert view.mode == "direct"
        assert _tab_label(app, "side-diff-pane") == "Diff · 1 ↔ 2"


async def test_deleted_side_shows_placeholder(delete_conflict_repo):
    app = _Harness(delete_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        ours = app.query_one("#side-ours-body", Static).content
        assert ours.plain == "(deleted on this side)"


async def test_labels_with_brackets_render_literally(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    git_commit(repo, "file.txt", "base\n", "add file")
    subprocess.run(["git", "checkout", "-q", "-b", "fix"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "fix\n", "fix [bug] in parser")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "cherry-pick", "fix"], cwd=repo, capture_output=True)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        assert _tab_label(app, "side-theirs-pane").endswith('"fix [bug] in parser"')


async def test_selecting_a_row_loads_that_file(merge_conflict_repo, monkeypatch, git_commit):
    monkeypatch.setattr(delta, "render", lambda *a, **k: None)
    repo = merge_conflict_repo
    subprocess.run(["git", "merge", "--abort"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "feature"], cwd=repo, check=True)
    git_commit(repo, "zzz.txt", "feature z\n", "feature z")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "zzz.txt", "main z\n", "main z")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        assert _rows(app) == ["file.txt", "zzz.txt"]
        app.query_one("#conflicts-table", DataTable).focus()
        await pilot.press("down")
        await _settle(app, pilot)
        assert app.query_one(ConflictsView).selected_path == "zzz.txt"
        assert app.query_one("#side-theirs-body", Static).content.code == "feature z\n"
