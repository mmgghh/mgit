from typer.testing import CliRunner

from mgit.cli.main import app

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
        "commit", "amend", "undo", "push", "pull", "fetch", "sync",
        "log", "diff", "whoami", "root", "ignored", "aliases",
        "repo-info", "reset-hard", "nuke", "nuke-branch",
    ]:
        assert cmd in result.stdout


def test_error_boundary_prints_clean_message_not_traceback(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    result = runner.invoke(app, ["branch", "delete", "does-not-exist"])
    assert result.exit_code != 0
    assert "Traceback" not in result.stdout
