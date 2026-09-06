import pytest
from mgit.git.runner import run, GitCommandError


def test_run_returns_stdout(tmp_git_repo):
    assert run(["rev-parse", "--is-inside-work-tree"], cwd=tmp_git_repo) == "true"


def test_run_raises_on_failure(tmp_git_repo):
    with pytest.raises(GitCommandError) as exc:
        run(["not-a-real-command"], cwd=tmp_git_repo)
    assert exc.value.returncode != 0
    assert "not-a-real-command" in str(exc.value)


def test_run_no_check_does_not_raise(tmp_git_repo):
    out = run(["not-a-real-command"], cwd=tmp_git_repo, check=False)
    assert out == ""
