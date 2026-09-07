import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mgit import config as cfg
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


def test_log_and_diff_preserve_bracketed_content(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    Path(tmp_git_repo, "a.txt").write_text("def f(x: list[str]) -> dict[str, int]:\n    return {}\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fix [bug] in parser"],
        cwd=tmp_git_repo, check=True, capture_output=True,
    )
    log_result = runner.invoke(app, ["log"])
    assert log_result.exit_code == 0
    assert "fix [bug] in parser" in log_result.stdout

    diff_result = runner.invoke(app, ["diff", "HEAD~1", "HEAD"])
    assert diff_result.exit_code == 0
    assert "list[str]" in diff_result.stdout
    assert "dict[str, int]" in diff_result.stdout


def test_log_falls_back_to_configured_limit(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_git_repo)
    Path(tmp_git_repo, "b.txt").write_text("b")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=tmp_git_repo, check=True, capture_output=True)
    cfg.set_value("log.limit", "1", cwd=tmp_git_repo)
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert result.stdout.count("\n") == 1


def test_log_falls_back_to_default_on_non_numeric_configured_limit(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_git_repo)
    cfg.set_value("log.limit", "high", cwd=tmp_git_repo)
    result = runner.invoke(app, ["log"])
    assert result.exit_code == 0
    assert "Traceback" not in result.stdout


def test_help_text_present_for_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "List local branches" not in result.stdout  # group help only shows group names at top level, not per-command descriptions
    branch_result = runner.invoke(app, ["branch", "--help"])
    assert "Create a new branch and switch to it." in branch_result.stdout
