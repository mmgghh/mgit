import sys

from typer.testing import CliRunner

from mgit.cli.main import app

runner = CliRunner()


def test_tui_command_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tui" in result.stdout


def test_tui_missing_dependency_shows_friendly_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "mgit.tui.app", None)
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 1
    assert "pip install mgit[tui]" in result.stdout
