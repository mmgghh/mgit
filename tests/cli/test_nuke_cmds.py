import subprocess
from pathlib import Path

from typer.testing import CliRunner

from mgit.cli.main import app

runner = CliRunner()


def _mark_rebase_in_progress(repo):
    git_dir = Path(subprocess.run(
        ["git", "rev-parse", "--git-dir"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip())
    if not git_dir.is_absolute():
        git_dir = Path(repo) / git_dir
    (git_dir / "rebase-merge").mkdir()


def test_reset_hard_prompt_flags_in_progress_rebase(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["reset-hard", "HEAD"], input="n\n")
    assert "rebase" in result.stdout.lower()


def test_nuke_prompt_flags_in_progress_rebase(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["nuke"], input="n\n")
    assert "rebase" in result.stdout.lower()


def test_nuke_branch_prompt_flags_in_progress_rebase(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["nuke-branch"], input="n\n")
    assert "rebase" in result.stdout.lower()
