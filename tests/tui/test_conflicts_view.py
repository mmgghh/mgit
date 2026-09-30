import subprocess
from contextlib import nullcontext
from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.content import Content
from textual.widgets import Button, DataTable, Static, TabbedContent

from mgit.core import conflicts as conflicts_core
from mgit.core.merge_rebase import list_conflicts
from mgit.git import delta
from mgit.git.repo import in_progress_operation
from mgit.tui.views import conflicts as conflicts_view
from mgit.tui.views.conflicts import IDLE_MESSAGE, ConflictsView
from mgit.tui.views.run import ConfirmScreen
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


async def _press_on_table(app, pilot, *keys):
    app.query_one("#conflicts-table", DataTable).focus()
    await pilot.press(*keys)
    await _settle(app, pilot)


async def _confirm(app, pilot):
    app.screen.query_one("#confirm-yes", Button).press()
    await _settle(app, pilot)


def _confirm_text(app):
    return Content.from_markup(app.screen.query_one("#confirm-message", Static).content).plain


async def test_take_side_two_after_confirming(rebase_conflict_repo):
    app = _Harness(rebase_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "2")
        assert isinstance(app.screen, ConfirmScreen)
        assert "Your commit: " in _confirm_text(app)
        await _confirm(app, pilot)
        assert Path(rebase_conflict_repo, "file.txt").read_text() == "feature\n"
        assert _rows(app) == []
        assert "all conflicts resolved" in _headline(app)


async def test_cancelling_take_side_changes_nothing(merge_conflict_repo):
    app = _Harness(merge_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "1")
        await pilot.press("escape")
        await _settle(app, pilot)
        assert list_conflicts(merge_conflict_repo) == [("file.txt", "both modified")]


async def test_mark_resolved_confirms_when_markers_remain(merge_conflict_repo):
    app = _Harness(merge_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "a")
        assert isinstance(app.screen, ConfirmScreen)
        assert "conflict markers" in _confirm_text(app)
        await pilot.press("escape")
        await _settle(app, pilot)
        Path(merge_conflict_repo, "file.txt").write_text("resolved\n")
        await _press_on_table(app, pilot, "a")
        assert not isinstance(app.screen, ConfirmScreen)
        assert list_conflicts(merge_conflict_repo) == []


async def test_edit_opens_editor_then_refreshes(merge_conflict_repo, monkeypatch):
    opened = []

    def fake_editor(file_path):
        opened.append(file_path)
        Path(file_path).write_text("edited\n")

    monkeypatch.setattr(conflicts_view, "_launch_editor", fake_editor)
    app = _Harness(merge_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        monkeypatch.setattr(app, "suspend", lambda: nullcontext())
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "e")
        assert Path(opened[0]).resolve() == Path(merge_conflict_repo, "file.txt").resolve()
        await _press_on_table(app, pilot, "a")
        assert list_conflicts(merge_conflict_repo) == []


async def test_continue_refused_while_conflicts_remain(merge_conflict_repo):
    app = _Harness(merge_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "C")
        assert ("1 file(s) still unresolved", "warning") in app.notices
        assert in_progress_operation(merge_conflict_repo) == "merge"


async def test_continue_finishes_after_resolving(rebase_conflict_repo, monkeypatch):
    monkeypatch.setenv("GIT_EDITOR", "false")
    app = _Harness(rebase_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "2")
        await _confirm(app, pilot)
        await _press_on_table(app, pilot, "C")
        assert in_progress_operation(rebase_conflict_repo) is None
        assert _headline(app) == IDLE_MESSAGE


async def test_continue_into_next_conflict_warns_and_reloads(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    git_commit(repo, "file.txt", "base\n", "add file")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "feature 1\n", "first")
    git_commit(repo, "file.txt", "feature 2\n", "second")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "checkout", "-q", "feature"], cwd=repo, check=True)
    subprocess.run(["git", "rebase", "main"], cwd=repo, capture_output=True)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        # Keep main's version so the second commit ("feature 1" -> "feature 2") conflicts too.
        await _press_on_table(app, pilot, "1")
        await _confirm(app, pilot)
        await _press_on_table(app, pilot, "C")
        assert any(sev == "warning" and "new conflicts" in msg for msg, sev in app.notices)
        assert "(step 2/2)" in _headline(app)
        assert _rows(app) == ["file.txt"]


async def test_abort_asks_first(rebase_conflict_repo):
    app = _Harness(rebase_conflict_repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "A")
        assert isinstance(app.screen, ConfirmScreen)
        assert "Abort the rebase?" in _confirm_text(app)
        await _confirm(app, pilot)
        assert in_progress_operation(rebase_conflict_repo) is None
        assert _headline(app) == IDLE_MESSAGE


async def test_actions_when_idle_just_notify(tmp_git_repo):
    app = _Harness(tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "1")
        await _press_on_table(app, pilot, "C")
        assert not isinstance(app.screen, ConfirmScreen)
        assert ("Nothing in progress", "warning") in app.notices


async def test_confirm_message_shows_brackets_literally(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    name = "notes [draft].md"
    git_commit(repo, name, "base\n", "add notes")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, name, "feature\n", "feature notes")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, name, "main\n", "main notes")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        await _press_on_table(app, pilot, "1")
        assert "Replace notes [draft].md with Current: main (HEAD)" in _confirm_text(app)
        await _confirm(app, pilot)
        assert Path(repo, name).read_text() == "main\n"


async def test_git_am_conflict_is_labeled_and_abort_names_it(tmp_git_repo, git_commit, tmp_path):
    repo = tmp_git_repo
    git_commit(repo, "file.txt", "base\n", "add file")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "format-patch", "-q", "-1", "-o", str(tmp_path / "p")], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "am", "-3", *map(str, (tmp_path / "p").iterdir())], cwd=repo, capture_output=True)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        assert 'Applying patch "feature change" onto main' in _headline(app)
        assert _tab_label(app, "side-theirs-pane") == '2 · Patch: "feature change"'
        await _press_on_table(app, pilot, "A")
        assert "Abort the git am?" in _confirm_text(app)
        await _confirm(app, pilot)
        assert in_progress_operation(repo) is None


async def test_each_refresh_or_move_loads_the_selected_file_once(merge_conflict_repo, git_commit, monkeypatch):
    repo = merge_conflict_repo
    subprocess.run(["git", "merge", "--abort"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "feature"], cwd=repo, check=True)
    git_commit(repo, "zzz.txt", "feature z\n", "feature z")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "zzz.txt", "main z\n", "main z")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    loads = []
    real_side_diff = conflicts_core.side_diff

    def counting_side_diff(path, mode, cwd=None):
        loads.append(path)
        return real_side_diff(path, mode, cwd)

    monkeypatch.setattr(conflicts_core, "side_diff", counting_side_diff)
    app = _Harness(repo)
    async with app.run_test(size=(120, 40)) as pilot:
        await _settle(app, pilot)
        assert loads == ["file.txt"]
        loads.clear()
        app.query_one(ConflictsView).refresh_conflicts()
        await _settle(app, pilot)
        assert loads == ["file.txt"]
        loads.clear()
        await _press_on_table(app, pilot, "down")
        assert loads == ["zzz.txt"]
