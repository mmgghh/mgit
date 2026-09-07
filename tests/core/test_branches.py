from pathlib import Path
import subprocess

import pytest

from mgit.core import branches
from mgit.git.runner import GitCommandError


def _commit(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def test_new_and_list_branches(tmp_git_repo):
    branches.new_branch("feature/x", cwd=tmp_git_repo)
    names = branches.list_branches(tmp_git_repo)
    assert "main" in names and "feature/x" in names


def test_switch_branch(tmp_git_repo):
    branches.new_branch("feature/x", cwd=tmp_git_repo)
    branches.switch_branch("main", cwd=tmp_git_repo)
    from mgit.git.repo import current_branch
    assert current_branch(tmp_git_repo) == "main"


def test_delete_branch(tmp_git_repo):
    branches.new_branch("throwaway", cwd=tmp_git_repo)
    branches.switch_branch("main", cwd=tmp_git_repo)
    branches.delete_branch("throwaway", cwd=tmp_git_repo)
    assert "throwaway" not in branches.list_branches(tmp_git_repo)


def test_rename_branch(tmp_git_repo):
    branches.new_branch("old-name", cwd=tmp_git_repo)
    branches.rename_branch("old-name", "new-name", cwd=tmp_git_repo)
    names = branches.list_branches(tmp_git_repo)
    assert "new-name" in names and "old-name" not in names


def test_merged_and_unmerged(tmp_git_repo):
    branches.new_branch("merged-branch", cwd=tmp_git_repo)
    branches.switch_branch("main", cwd=tmp_git_repo)
    subprocess.run(["git", "merge", "--no-ff", "-m", "merge", "merged-branch"], cwd=tmp_git_repo, check=True, capture_output=True)
    branches.new_branch("unmerged-branch", cwd=tmp_git_repo)
    _commit(tmp_git_repo, "f.txt", "x", "unmerged commit")
    branches.switch_branch("main", cwd=tmp_git_repo)
    assert "merged-branch" in branches.merged_branches(tmp_git_repo)
    assert "unmerged-branch" in branches.unmerged_branches(tmp_git_repo)
    assert "unmerged-branch" not in branches.merged_branches(tmp_git_repo)


def test_prune_gone(tmp_git_remote):
    subprocess.run(["git", "checkout", "-b", "to-delete"], cwd=tmp_git_remote, check=True, capture_output=True)
    subprocess.run(["git", "push", "-u", "origin", "to-delete"], cwd=tmp_git_remote, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_remote, check=True, capture_output=True)
    subprocess.run(["git", "push", "origin", "--delete", "to-delete"], cwd=tmp_git_remote, check=True, capture_output=True)
    deleted = branches.prune_gone(force=True, cwd=tmp_git_remote)
    assert "to-delete" in deleted
    assert "to-delete" not in branches.list_branches(tmp_git_remote)


def test_branch_report(tmp_git_repo):
    branches.new_branch("feature/y", cwd=tmp_git_repo)
    _commit(tmp_git_repo, "y.txt", "content", "add y")
    report = branches.branch_report("feature/y", "main", cwd=tmp_git_repo)
    assert report["branch"] == "feature/y"
    assert report["base"] == "main"
    assert len(report["commits"]) == 1
    assert any("y.txt" in f for f in report["files"])


def test_rename_branch_refuses_existing_name(tmp_git_repo):
    branches.new_branch("existing", cwd=tmp_git_repo)
    branches.switch_branch("main", cwd=tmp_git_repo)
    branches.new_branch("to-rename", cwd=tmp_git_repo)
    with pytest.raises(GitCommandError):
        branches.rename_branch("to-rename", "existing", cwd=tmp_git_repo)


def test_branch_report_raises_git_command_error_on_detached_head(tmp_git_repo):
    subprocess.run(["git", "checkout", "--detach"], cwd=tmp_git_repo, check=True, capture_output=True)
    with pytest.raises(GitCommandError):
        branches.branch_report(cwd=tmp_git_repo)
