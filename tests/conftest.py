import subprocess
from pathlib import Path

import pytest


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def tmp_git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-b", "main"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test User"], repo)
    (repo / "README.md").write_text("hello\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "init"], repo)
    return str(repo)


@pytest.fixture
def tmp_git_remote(tmp_path):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", str(bare), str(clone)], check=True, capture_output=True)
    _git(["config", "user.email", "test@example.com"], clone)
    _git(["config", "user.name", "Test User"], clone)
    (clone / "README.md").write_text("hello\n")
    _git(["add", "."], clone)
    _git(["commit", "-m", "init"], clone)
    _git(["push", "-u", "origin", "main"], clone)
    return str(clone)


def commit_file(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    _git(["add", "."], repo)
    _git(["commit", "-m", message], repo)


@pytest.fixture
def git_commit():
    """git_commit(repo, filename, content, message): write, stage, and commit one file."""
    return commit_file


@pytest.fixture
def merge_conflict_repo(tmp_git_repo):
    """On main, `git merge feature` stopped on file.txt (main: "main", feature: "feature", base: "base")."""
    repo = tmp_git_repo
    commit_file(repo, "file.txt", "base\n", "add file")
    _git(["checkout", "-b", "feature"], repo)
    commit_file(repo, "file.txt", "feature\n", "feature change")
    _git(["checkout", "main"], repo)
    commit_file(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    return repo


@pytest.fixture
def rebase_conflict_repo(tmp_git_repo):
    """feature/login (2 commits) rebased onto main, stopped at step 2/2 ("add login") on file.txt."""
    repo = tmp_git_repo
    commit_file(repo, "file.txt", "base\n", "add file")
    _git(["checkout", "-b", "feature/login"], repo)
    commit_file(repo, "other.txt", "x\n", "unrelated")
    commit_file(repo, "file.txt", "feature\n", "add login")
    _git(["checkout", "main"], repo)
    commit_file(repo, "file.txt", "main\n", "main change")
    _git(["checkout", "feature/login"], repo)
    subprocess.run(["git", "rebase", "main"], cwd=repo, capture_output=True)
    return repo


@pytest.fixture
def delete_conflict_repo(tmp_git_repo):
    """On main (which deleted file.txt), `git merge feature` (which modified it) stopped: deleted by us."""
    repo = tmp_git_repo
    commit_file(repo, "file.txt", "base\n", "add file")
    _git(["checkout", "-b", "feature"], repo)
    commit_file(repo, "file.txt", "feature\n", "feature change")
    _git(["checkout", "main"], repo)
    _git(["rm", "-q", "file.txt"], repo)
    _git(["commit", "-m", "delete file"], repo)
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    return repo
