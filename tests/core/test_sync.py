from pathlib import Path
import subprocess

import pytest

from mgit.core import sync
from mgit.git.runner import GitCommandError


def _commit(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def test_push_sets_upstream_when_missing(tmp_git_repo, tmp_path):
    bare = tmp_path / "origin2.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=tmp_git_repo, check=True)
    sync.push(cwd=tmp_git_repo)
    from mgit.git.repo import has_upstream
    assert has_upstream(cwd=tmp_git_repo) is True


def test_push_after_upstream_exists(tmp_git_remote):
    _commit(tmp_git_remote, "a.txt", "a", "add a")
    sync.push(cwd=tmp_git_remote)
    out = subprocess.run(["git", "log", "origin/main", "--oneline"], cwd=tmp_git_remote, capture_output=True, text=True, check=True)
    assert "add a" in out.stdout


def test_fetch_all(tmp_git_remote):
    out = sync.fetch_all(cwd=tmp_git_remote)
    assert isinstance(out, str)


def test_pull_rebases(tmp_git_remote, tmp_path):
    other_clone = tmp_path / "other"
    subprocess.run(["git", "clone", subprocess.run(["git", "remote", "get-url", "origin"], cwd=tmp_git_remote, capture_output=True, text=True, check=True).stdout.strip(), str(other_clone)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=other_clone, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=other_clone, check=True)
    _commit(other_clone, "b.txt", "b", "add b from other")
    subprocess.run(["git", "push"], cwd=other_clone, check=True, capture_output=True)
    sync.pull(cwd=tmp_git_remote)
    assert Path(tmp_git_remote, "b.txt").exists()


def test_pull_requires_branch_not_detached(tmp_git_repo):
    subprocess.run(["git", "checkout", "--detach", "HEAD"], cwd=tmp_git_repo, check=True, capture_output=True)
    with pytest.raises(GitCommandError):
        sync.pull(cwd=tmp_git_repo)


def test_sync_fetches_and_rebases(tmp_git_remote, tmp_path):
    origin_url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=tmp_git_remote, capture_output=True, text=True, check=True).stdout.strip()
    other_clone = tmp_path / "other_sync"
    subprocess.run(["git", "clone", origin_url, str(other_clone)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=other_clone, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=other_clone, check=True)
    _commit(other_clone, "sync.txt", "s", "add sync file")
    subprocess.run(["git", "push"], cwd=other_clone, check=True, capture_output=True)
    sync.sync(cwd=tmp_git_remote)
    assert Path(tmp_git_remote, "sync.txt").exists()
