import subprocess
from pathlib import Path

import pytest

from mgit.core import conflicts
from mgit.core.merge_rebase import list_conflicts
from mgit.git.runner import GitCommandError


def test_context_is_none_when_idle(tmp_git_repo):
    assert conflicts.conflict_context(tmp_git_repo) is None


def test_rebase_context_names_sides(rebase_conflict_repo):
    ctx = conflicts.conflict_context(rebase_conflict_repo)
    assert ctx.operation == "rebase"
    assert ctx.headline == "Rebasing feature/login onto main (step 2/2)"
    assert ctx.ours_label.startswith("Upstream: main (")
    assert ctx.theirs_label.startswith("Your commit: ")
    assert ctx.theirs_label.endswith('"add login"')
    assert ctx.step == (2, 2)


def test_merge_context_names_sides(merge_conflict_repo):
    ctx = conflicts.conflict_context(merge_conflict_repo)
    assert ctx.operation == "merge"
    assert ctx.headline == "Merging feature into main"
    assert ctx.ours_label == "Current: main (HEAD)"
    assert ctx.theirs_label.startswith("Incoming: feature (")
    assert ctx.step is None


def test_cherry_pick_context_names_sides(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    git_commit(repo, "file.txt", "base\n", "add file")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "feature\n", "feature change")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "cherry-pick", "feature"], cwd=repo, capture_output=True)
    ctx = conflicts.conflict_context(repo)
    assert ctx.operation == "cherry-pick"
    assert ctx.headline.startswith("Cherry-picking ")
    assert ctx.ours_label == "Current: main"
    assert ctx.theirs_label.startswith("Picked: ")
    assert ctx.theirs_label.endswith('"feature change"')


def test_side_diff_direct_compares_the_two_sides(merge_conflict_repo):
    out = conflicts.side_diff("file.txt", "direct", merge_conflict_repo)
    assert "--- a/file.txt" in out and "+++ b/file.txt" in out
    assert "-main" in out and "+feature" in out


def test_side_diff_base_modes_show_each_sides_change(merge_conflict_repo):
    ours = conflicts.side_diff("file.txt", "base-ours", merge_conflict_repo)
    theirs = conflicts.side_diff("file.txt", "base-theirs", merge_conflict_repo)
    assert "-base" in ours and "+main" in ours
    assert "-base" in theirs and "+feature" in theirs


def test_side_diff_rejects_unknown_mode(merge_conflict_repo):
    with pytest.raises(GitCommandError):
        conflicts.side_diff("file.txt", "sideways", merge_conflict_repo)


def test_side_diff_missing_side_names_the_file(delete_conflict_repo):
    out = conflicts.side_diff("file.txt", "direct", delete_conflict_repo)
    assert "+feature" in out
    assert "a/file.txt" in out and "b/file.txt" in out
    assert "e69de29" not in out.split("\n", 1)[0]  # header names the file, not the empty blob


def test_side_content_returns_each_version(merge_conflict_repo):
    assert conflicts.side_content("file.txt", "ours", merge_conflict_repo).text == "main\n"
    assert conflicts.side_content("file.txt", "theirs", merge_conflict_repo).text == "feature\n"


def test_side_content_flags_missing_side(delete_conflict_repo):
    ours = conflicts.side_content("file.txt", "ours", delete_conflict_repo)
    assert ours.missing and ours.text == ""
    assert conflicts.side_content("file.txt", "theirs", delete_conflict_repo).text == "feature\n"


def test_side_content_flags_binary(tmp_git_repo):
    repo = tmp_git_repo
    Path(repo, "img.bin").write_bytes(b"\x00base")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "bin"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    Path(repo, "img.bin").write_bytes(b"\x00feature")
    subprocess.run(["git", "commit", "-qam", "bin feature"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    Path(repo, "img.bin").write_bytes(b"\x00main")
    subprocess.run(["git", "commit", "-qam", "bin main"], cwd=repo, check=True)
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    assert conflicts.side_content("img.bin", "ours", repo).binary


def test_side_content_decodes_non_utf8(tmp_git_repo):
    repo = tmp_git_repo
    Path(repo, "l1.txt").write_bytes(b"base\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "l1"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    Path(repo, "l1.txt").write_bytes(b"caf\xe9\n")
    subprocess.run(["git", "commit", "-qam", "l1 feature"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    Path(repo, "l1.txt").write_bytes(b"main\n")
    subprocess.run(["git", "commit", "-qam", "l1 main"], cwd=repo, check=True)
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    assert conflicts.side_content("l1.txt", "theirs", repo).text == "caf�\n"
    assert "+caf�" in conflicts.side_diff("l1.txt", "direct", repo)


def test_side_content_rejects_unknown_side(merge_conflict_repo):
    with pytest.raises(GitCommandError):
        conflicts.side_content("file.txt", "both", merge_conflict_repo)


def test_paths_with_spaces_and_brackets(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    name = "notes [draft] v1.md"
    git_commit(repo, name, "base\n", "add notes")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, name, "feature\n", "feature notes")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, name, "main\n", "main notes")
    subprocess.run(["git", "merge", "feature"], cwd=repo, capture_output=True)
    assert [p for p, _ in list_conflicts(repo)] == [name]
    assert conflicts.side_content(name, "theirs", repo).text == "feature\n"
    assert "+feature" in conflicts.side_diff(name, "direct", repo)
