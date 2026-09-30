from pathlib import Path

from typer.testing import CliRunner

from mgit import config as cfg
from mgit.cli import console as console_mod
from mgit.cli.main import app
from mgit.git import delta

runner = CliRunner()


def _record_page(monkeypatch, result=True):
    calls = []

    def fake_page(text, side_by_side=True, cwd=None):
        calls.append((text, side_by_side))
        return result

    monkeypatch.setattr(delta, "page", fake_page)
    return calls


def test_emit_diff_pages_through_delta_on_a_terminal(monkeypatch, tmp_git_repo, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(console_mod, "_is_terminal", lambda: True)
    calls = _record_page(monkeypatch)
    console_mod.emit_diff("some diff", cwd=tmp_git_repo)
    assert calls == [("some diff", True)]
    assert "some diff" not in capsys.readouterr().out


def test_emit_diff_honours_side_by_side_config(monkeypatch, tmp_git_repo, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    cfg.set_value("diff.side_by_side", "false", cwd=tmp_git_repo)
    monkeypatch.setattr(console_mod, "_is_terminal", lambda: True)
    calls = _record_page(monkeypatch)
    console_mod.emit_diff("some diff", cwd=tmp_git_repo)
    assert calls == [("some diff", False)]


def test_emit_diff_falls_back_to_plain_without_delta(monkeypatch, tmp_git_repo, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(console_mod, "_is_terminal", lambda: True)
    _record_page(monkeypatch, result=False)
    console_mod.emit_diff("some diff", cwd=tmp_git_repo)
    assert "some diff" in capsys.readouterr().out


def test_piped_mgit_diff_stays_plain(monkeypatch, tmp_git_repo):
    monkeypatch.chdir(tmp_git_repo)
    calls = _record_page(monkeypatch)
    Path(tmp_git_repo, "README.md").write_text("changed\n")
    result = runner.invoke(app, ["diff"])
    assert result.exit_code == 0
    assert calls == []
    assert "+changed" in result.stdout
    assert "\x1b[" not in result.stdout


def test_emit_diff_survives_a_malformed_config(monkeypatch, tmp_git_repo, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    (home / ".config" / "mgit").mkdir(parents=True)
    (home / ".config" / "mgit" / "config.toml").write_text("[diff\n")
    monkeypatch.setattr(console_mod, "_is_terminal", lambda: True)
    calls = _record_page(monkeypatch)
    console_mod.emit_diff("some diff", cwd=tmp_git_repo)
    assert calls == [("some diff", True)]
