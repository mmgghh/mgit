from pathlib import Path
import subprocess

import pytest

from mgit.core import nuke, repo_info
from mgit.git.runner import GitCommandError


def _commit(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def test_reset_hard(tmp_git_repo):
    _commit(tmp_git_repo, "a.txt", "a", "add a")
    first_commit = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=tmp_git_repo, capture_output=True, text=True, check=True).stdout.strip()
    nuke.reset_hard(first_commit, cwd=tmp_git_repo)
    assert not Path(tmp_git_repo, "a.txt").exists()


def test_nuke_discards_changes_and_untracked(tmp_git_repo):
    Path(tmp_git_repo, "README.md").write_text("dirty")
    Path(tmp_git_repo, "untracked.txt").write_text("junk")
    nuke.nuke(cwd=tmp_git_repo)
    assert Path(tmp_git_repo, "README.md").read_text() == "hello\n"
    assert not Path(tmp_git_repo, "untracked.txt").exists()


def test_nuke_branch_matches_upstream(tmp_git_remote):
    Path(tmp_git_remote, "README.md").write_text("local edit")
    subprocess.run(["git", "add", "."], cwd=tmp_git_remote, check=True)
    subprocess.run(["git", "commit", "-m", "local only"], cwd=tmp_git_remote, check=True, capture_output=True)
    nuke.nuke_branch(cwd=tmp_git_remote)
    log = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=tmp_git_remote, capture_output=True, text=True, check=True).stdout.strip()
    assert log == "init"


def test_whoami(tmp_git_repo):
    info = repo_info.whoami(tmp_git_repo)
    assert info == {"name": "Test User", "email": "test@example.com"}


def test_ignored_files(tmp_git_repo):
    Path(tmp_git_repo, ".gitignore").write_text("ignored.txt\n")
    Path(tmp_git_repo, "ignored.txt").write_text("x")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "add gitignore"], cwd=tmp_git_repo, check=True, capture_output=True)
    assert "ignored.txt" in repo_info.ignored_files(tmp_git_repo)


def test_aliases_empty_by_default(tmp_git_repo):
    assert repo_info.aliases(tmp_git_repo) == []


def test_aliases_returns_configured_aliases(tmp_git_repo):
    subprocess.run(["git", "config", "alias.co", "checkout"], cwd=tmp_git_repo, check=True)
    result = repo_info.aliases(tmp_git_repo)
    assert any("alias.co" in line and "checkout" in line for line in result)


def test_summary(tmp_git_repo):
    info = repo_info.summary(tmp_git_repo)
    assert info["root"] == tmp_git_repo
    assert info["branch"] == "main"
    assert info["in_progress"] is None


def test_nuke_branch_raises_git_command_error_on_detached_head(tmp_git_remote):
    subprocess.run(["git", "checkout", "--detach"], cwd=tmp_git_remote, check=True, capture_output=True)
    with pytest.raises(GitCommandError):
        nuke.nuke_branch(cwd=tmp_git_remote)
