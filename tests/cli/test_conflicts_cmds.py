from typer.testing import CliRunner

from mgit.cli.main import app
from mgit.git.runner import GitCommandError
from mgit.tui.run.discovery import discover_commands

runner = CliRunner()


def test_show_labels_both_sides_then_diffs(rebase_conflict_repo, monkeypatch):
    monkeypatch.chdir(rebase_conflict_repo)
    result = runner.invoke(app, ["conflicts", "show", "file.txt"])
    assert result.exit_code == 0, result.output
    assert "Rebasing feature/login onto main (step 2/2)" in result.stdout
    assert "ours   = Upstream: main (" in result.stdout
    assert 'theirs = Your commit: ' in result.stdout
    assert "-main" in result.stdout and "+feature" in result.stdout


def test_show_base_mode(merge_conflict_repo, monkeypatch):
    monkeypatch.chdir(merge_conflict_repo)
    result = runner.invoke(app, ["conflicts", "show", "file.txt", "--mode", "base-theirs"])
    assert result.exit_code == 0, result.output
    assert "-base" in result.stdout and "+feature" in result.stdout


def test_show_rejects_unknown_mode(merge_conflict_repo, monkeypatch):
    monkeypatch.chdir(merge_conflict_repo)
    result = runner.invoke(app, ["conflicts", "show", "file.txt", "--mode", "sideways"])
    assert isinstance(result.exception, GitCommandError)
    assert "Merging" not in result.stdout


def test_show_errors_when_idle(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    result = runner.invoke(app, ["conflicts", "show", "README.md"])
    assert isinstance(result.exception, GitCommandError)
    assert "No merge, rebase" in str(result.exception)


def test_show_is_discoverable_in_run_tab():
    assert ("conflicts", "show") in {tuple(e.path) for e in discover_commands(app)}


def test_show_says_when_the_path_is_not_conflicted(merge_conflict_repo, monkeypatch):
    monkeypatch.chdir(merge_conflict_repo)
    result = runner.invoke(app, ["conflicts", "show", "README.md"])
    assert isinstance(result.exception, GitCommandError)
    assert "README.md has no conflict" in str(result.exception)
    assert "Merging" not in result.stdout
