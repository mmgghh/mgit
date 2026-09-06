import subprocess
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
