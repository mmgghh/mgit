import sys

import pytest
from typer.testing import CliRunner

from mgit.cli.main import app, main

runner = CliRunner()


def test_help_lists_every_command_group():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for group in [
        "branch", "stash", "tag", "remote", "flow",
        "rebase", "merge", "cherry-pick", "revert", "conflicts", "config",
    ]:
        assert group in result.stdout


def test_help_lists_every_flat_command():
    result = runner.invoke(app, ["--help"])
    for cmd in [
        "commit", "commit-empty", "amend", "undo", "push", "pull", "fetch", "sync",
        "log", "diff", "whoami", "root", "ignored", "aliases",
        "repo-info", "reset-hard", "nuke", "nuke-branch",
    ]:
        assert cmd in result.stdout


def test_error_boundary_prints_clean_message_not_traceback(tmp_git_repo, monkeypatch, capsys):
    monkeypatch.chdir(tmp_git_repo)
    monkeypatch.setattr(sys, "argv", ["mgit", "branch", "delete", "does-not-exist"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "Error:" in captured.err
