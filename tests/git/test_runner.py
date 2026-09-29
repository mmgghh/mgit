import pytest
from mgit.git.runner import run, GitCommandError


def test_run_returns_stdout(tmp_git_repo):
    assert run(["rev-parse", "--is-inside-work-tree"], cwd=tmp_git_repo) == "true"


def test_run_raises_on_failure(tmp_git_repo):
    with pytest.raises(GitCommandError) as exc:
        run(["not-a-real-command"], cwd=tmp_git_repo)
    assert exc.value.returncode != 0
    assert "not-a-real-command" in str(exc.value)
    assert exc.value.command == ["not-a-real-command"]


def test_run_no_check_does_not_raise(tmp_git_repo):
    out = run(["not-a-real-command"], cwd=tmp_git_repo, check=False)
    assert out == ""


import subprocess
from pathlib import Path

from mgit.git.runner import run_bytes


def _commit_bytes(repo, name, data):
    Path(repo, name).write_bytes(data)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", f"add {name}"], cwd=repo, check=True, capture_output=True)


def test_run_env_override_reaches_git(tmp_git_repo):
    assert run(["var", "GIT_EDITOR"], cwd=tmp_git_repo, env={"GIT_EDITOR": "my-editor"}) == "my-editor"


def test_run_decodes_invalid_utf8_without_raising(tmp_git_repo):
    _commit_bytes(tmp_git_repo, "latin1.txt", b"caf\xe9\n")
    assert run(["show", "HEAD:latin1.txt"], cwd=tmp_git_repo) == "caf�"


def test_run_bytes_returns_raw_bytes(tmp_git_repo):
    _commit_bytes(tmp_git_repo, "latin1.txt", b"caf\xe9\n")
    assert run_bytes(["show", "HEAD:latin1.txt"], cwd=tmp_git_repo) == b"caf\xe9\n"


def test_run_bytes_raises_on_failure(tmp_git_repo):
    with pytest.raises(GitCommandError):
        run_bytes(["show", "HEAD:missing.txt"], cwd=tmp_git_repo)
