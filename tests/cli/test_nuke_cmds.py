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


def _mark_merge_in_progress(repo):
    git_dir = Path(subprocess.run(
        ["git", "rev-parse", "--git-dir"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip())
    if not git_dir.is_absolute():
        git_dir = Path(repo) / git_dir
    (git_dir / "MERGE_HEAD").write_text("")


def test_reset_hard_prompt_warns_rebase_will_not_be_aborted(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["reset-hard", "HEAD"], input="n\n")
    assert "will not abort it" in result.stdout.lower()


def test_nuke_prompt_warns_rebase_will_not_be_aborted(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["nuke"], input="n\n")
    assert "will not abort it" in result.stdout.lower()


def test_nuke_branch_prompt_warns_rebase_will_not_be_aborted(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_rebase_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["nuke-branch"], input="n\n")
    assert "will not abort it" in result.stdout.lower()


def test_nuke_prompt_warns_abandoned_for_in_progress_merge(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    _mark_merge_in_progress(tmp_git_repo)
    result = runner.invoke(app, ["nuke"], input="n\n")
    assert "abandoned" in result.stdout.lower()
