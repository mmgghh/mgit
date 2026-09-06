from pathlib import Path
import subprocess

import pytest

from mgit.core import merge_rebase as mr
from mgit.git.runner import GitCommandError


def _commit(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def _make_merge_conflict(repo):
    _commit(repo, "file.txt", "initial\n", "initial file")
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True, capture_output=True)
    _commit(repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=repo, check=True, capture_output=True)
    _commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)


def test_list_conflicts(tmp_git_repo):
    _make_merge_conflict(tmp_git_repo)
    conflicts = mr.list_conflicts(tmp_git_repo)
    assert conflicts == [("file.txt", "both modified")]


def test_conflict_sides(tmp_git_repo):
    _make_merge_conflict(tmp_git_repo)
    assert mr.conflict_side("file.txt", "ours", tmp_git_repo).strip() == "main"
    assert mr.conflict_side("file.txt", "theirs", tmp_git_repo).strip() == "feature"


def test_merge_abort_clears_conflict(tmp_git_repo):
    _make_merge_conflict(tmp_git_repo)
    mr.merge_abort(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_merge_continue_after_resolving(tmp_git_repo):
    _make_merge_conflict(tmp_git_repo)
    Path(tmp_git_repo, "file.txt").write_text("resolved\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    mr.merge_continue(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_rebase_abort_clears_conflict(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "checkout", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "rebase", "main"], cwd=tmp_git_repo, capture_output=True)
    mr.rebase_abort(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_cherry_pick_abort_clears_conflict(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    feature_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_git_repo, capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "cherry-pick", feature_sha], cwd=tmp_git_repo, capture_output=True)
    mr.cherry_pick_abort(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_rebase_continue_after_resolving(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "checkout", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "rebase", "main"], cwd=tmp_git_repo, capture_output=True)
    Path(tmp_git_repo, "file.txt").write_text("resolved\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    mr.rebase_continue(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []
    assert Path(tmp_git_repo, "file.txt").read_text() == "resolved\n"


def test_rebase_skip_drops_conflicting_commit(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "checkout", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "rebase", "main"], cwd=tmp_git_repo, capture_output=True)
    mr.rebase_skip(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []
    assert Path(tmp_git_repo, "file.txt").read_text() == "main\n"


def test_cherry_pick_continue_after_resolving(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    feature_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_git_repo, capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "cherry-pick", feature_sha], cwd=tmp_git_repo, capture_output=True)
    Path(tmp_git_repo, "file.txt").write_text("resolved\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    mr.cherry_pick_continue(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_cherry_pick_skip(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    feature_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_git_repo, capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "cherry-pick", feature_sha], cwd=tmp_git_repo, capture_output=True)
    mr.cherry_pick_skip(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []
    assert Path(tmp_git_repo, "file.txt").read_text() == "main\n"


def test_revert_abort_clears_conflict(tmp_git_repo):
    _commit(tmp_git_repo, "file.txt", "v1\n", "v1")
    _commit(tmp_git_repo, "file.txt", "v2\n", "v2")
    subprocess.run(["git", "revert", "--no-edit", "HEAD~1"], cwd=tmp_git_repo, capture_output=True)
    mr.revert_abort(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_revert_continue_after_resolving(tmp_git_repo):
    _commit(tmp_git_repo, "file.txt", "v1\n", "v1")
    _commit(tmp_git_repo, "file.txt", "v2\n", "v2")
    subprocess.run(["git", "revert", "--no-edit", "HEAD~1"], cwd=tmp_git_repo, capture_output=True)
    Path(tmp_git_repo, "file.txt").write_text("resolved\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    mr.revert_continue(tmp_git_repo)
    assert mr.list_conflicts(tmp_git_repo) == []


def test_list_conflicts_path_with_space(tmp_git_repo):
    _commit(tmp_git_repo, "file name.txt", "initial\n", "initial file")
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file name.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file name.txt", "main\n", "main change")
    subprocess.run(["git", "merge", "feature"], cwd=tmp_git_repo, capture_output=True)
    conflicts = mr.list_conflicts(tmp_git_repo)
    assert conflicts == [("file name.txt", "both modified")]


def test_conflict_side_invalid_side_raises(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit(tmp_git_repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "merge", "feature"], cwd=tmp_git_repo, capture_output=True)
    with pytest.raises(GitCommandError):
        mr.conflict_side("file.txt", "bogus", tmp_git_repo)
