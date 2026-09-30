from textual.app import App, ComposeResult
from textual.widgets import Static

from mgit.git import delta
from mgit.tui.widgets.diff_view import DiffView

SAMPLE = "diff --git a/f.txt b/f.txt\n--- a/f.txt\n+++ b/f.txt\n@@ -1 +1 @@\n-old\n+new"


class _Harness(App):
    def __init__(self, text, cwd):
        super().__init__()
        self.text, self.cwd = text, cwd

    def compose(self) -> ComposeResult:
        yield DiffView(self.text, cwd=self.cwd)


def _fake_render(monkeypatch, output="\x1b[32mRENDERED\x1b[0m"):
    calls = []

    def fake(text, width, side_by_side=True, cwd=None):
        calls.append({"text": text, "width": width, "side_by_side": side_by_side})
        return output

    monkeypatch.setattr(delta, "render", fake)
    return calls


async def _settle(app, pilot):
    for _ in range(2):
        await pilot.pause()
        await app.workers.wait_for_complete()
    await pilot.pause()


def _body(app):
    return app.query_one(".diff-body", Static).content.plain


async def test_diff_view_shows_delta_output_at_its_width(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    calls = _fake_render(monkeypatch)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test(size=(100, 30)) as pilot:
        await _settle(app, pilot)
        assert _body(app) == "RENDERED"
        assert calls[-1]["width"] == 98  # 100 columns minus the reserved scrollbar
        assert calls[-1]["side_by_side"] is True


async def test_diff_view_falls_back_to_plain_text(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _fake_render(monkeypatch, output=None)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        assert "+new" in _body(app)


async def test_diff_view_uses_unified_layout_when_configured(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    with open(f"{tmp_git_repo}/.mgit.toml", "w") as f:
        f.write("[diff]\nside_by_side = false\n")
    calls = _fake_render(monkeypatch)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        assert calls[-1]["side_by_side"] is False


async def test_set_diff_replaces_content(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    calls = _fake_render(monkeypatch, output=None)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        view = app.query_one(DiffView)
        view.set_diff("+other change")
        await _settle(app, pilot)
        assert view.text == "+other change"
        assert "+other change" in _body(app)
        assert calls[-1]["text"] == "+other change"


async def test_resize_rerenders_at_new_width(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    calls = _fake_render(monkeypatch)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test(size=(100, 30)) as pilot:
        await _settle(app, pilot)
        await pilot.resize_terminal(120, 30)
        await _settle(app, pilot)
        assert calls[-1]["width"] == 118


async def test_empty_diff_shows_placeholder(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _fake_render(monkeypatch, output="")
    app = _Harness("", tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        assert _body(app) == "(no differences)"


async def test_malformed_config_does_not_crash_rendering(monkeypatch, tmp_git_repo, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    (home / ".config" / "mgit").mkdir(parents=True)
    (home / ".config" / "mgit" / "config.toml").write_text("[diff\n")
    calls = _fake_render(monkeypatch)
    app = _Harness(SAMPLE, tmp_git_repo)
    async with app.run_test() as pilot:
        await _settle(app, pilot)
        assert _body(app) == "RENDERED"
        assert calls[-1]["side_by_side"] is True
