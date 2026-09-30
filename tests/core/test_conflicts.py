import subprocess
from pathlib import Path

import pytest

from mgit.core import conflicts
from mgit.core.merge_rebase import list_conflicts
from mgit.git.repo import in_progress_operation
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


def _status(repo):
    return subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout


def test_take_side_ours_and_theirs(merge_conflict_repo):
    conflicts.take_side("file.txt", "theirs", merge_conflict_repo)
    assert Path(merge_conflict_repo, "file.txt").read_text() == "feature\n"
    assert list_conflicts(merge_conflict_repo) == []


def test_take_side_in_rebase_takes_your_commit(rebase_conflict_repo):
    conflicts.take_side("file.txt", "theirs", rebase_conflict_repo)
    assert Path(rebase_conflict_repo, "file.txt").read_text() == "feature\n"
    assert list_conflicts(rebase_conflict_repo) == []


def test_take_side_ours_keeps_current(merge_conflict_repo):
    conflicts.take_side("file.txt", "ours", merge_conflict_repo)
    assert Path(merge_conflict_repo, "file.txt").read_text() == "main\n"
    assert list_conflicts(merge_conflict_repo) == []


def test_take_deleted_side_removes_file(delete_conflict_repo):
    conflicts.take_side("file.txt", "ours", delete_conflict_repo)
    assert not Path(delete_conflict_repo, "file.txt").exists()
    assert list_conflicts(delete_conflict_repo) == []
    assert "file.txt" not in _status(delete_conflict_repo)  # main already deleted it: matches HEAD


def test_take_side_from_subdirectory(merge_conflict_repo):
    sub = Path(merge_conflict_repo, "sub")
    sub.mkdir()
    [(path, _label)] = list_conflicts(str(sub))
    assert path == "../file.txt"
    conflicts.take_side(path, "theirs", str(sub))
    assert Path(merge_conflict_repo, "file.txt").read_text() == "feature\n"


def test_mark_resolved_stages_the_file(merge_conflict_repo):
    Path(merge_conflict_repo, "file.txt").write_text("resolved\n")
    conflicts.mark_resolved("file.txt", merge_conflict_repo)
    assert list_conflicts(merge_conflict_repo) == []


def test_mark_resolved_records_a_deleted_file(merge_conflict_repo):
    Path(merge_conflict_repo, "file.txt").unlink()
    conflicts.mark_resolved("file.txt", merge_conflict_repo)
    assert list_conflicts(merge_conflict_repo) == []


def test_has_conflict_markers(merge_conflict_repo):
    assert conflicts.has_conflict_markers("file.txt", merge_conflict_repo)
    Path(merge_conflict_repo, "file.txt").write_text("title\n=======\n")
    assert not conflicts.has_conflict_markers("file.txt", merge_conflict_repo)
    Path(merge_conflict_repo, "file.txt").write_text("x\n>>>>>>> feature\n")
    assert conflicts.has_conflict_markers("file.txt", merge_conflict_repo)


def test_file_path_is_absolute_working_tree_path(merge_conflict_repo):
    sub = Path(merge_conflict_repo, "sub")
    sub.mkdir()
    assert conflicts.file_path("../file.txt", str(sub)).resolve() == Path(merge_conflict_repo, "file.txt").resolve()


def test_continue_operation_finishes_rebase_without_an_editor(rebase_conflict_repo, monkeypatch):
    monkeypatch.setenv("GIT_EDITOR", "false")  # would fail the commit if git opened an editor
    conflicts.take_side("file.txt", "theirs", rebase_conflict_repo)
    conflicts.continue_operation(rebase_conflict_repo)
    assert in_progress_operation(rebase_conflict_repo) is None
    subject = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=rebase_conflict_repo,
                             capture_output=True, text=True).stdout.strip()
    assert subject == "add login"


def test_continue_operation_finishes_merge(merge_conflict_repo):
    conflicts.take_side("file.txt", "ours", merge_conflict_repo)
    conflicts.continue_operation(merge_conflict_repo)
    assert in_progress_operation(merge_conflict_repo) is None


def test_continue_into_next_conflict_raises_and_leaves_conflicts(tmp_git_repo, git_commit):
    repo = tmp_git_repo
    git_commit(repo, "file.txt", "base\n", "add file")
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "feature 1\n", "first")
    git_commit(repo, "file.txt", "feature 2\n", "second")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    git_commit(repo, "file.txt", "main\n", "main change")
    subprocess.run(["git", "checkout", "-q", "feature"], cwd=repo, check=True)
    subprocess.run(["git", "rebase", "main"], cwd=repo, capture_output=True)
    Path(repo, "file.txt").write_text("merged 1\n")
    conflicts.mark_resolved("file.txt", repo)
    with pytest.raises(GitCommandError):
        conflicts.continue_operation(repo)
    assert list_conflicts(repo) == [("file.txt", "both modified")]
    assert conflicts.conflict_context(repo).step == (2, 2)


def test_continue_and_abort_require_an_operation(tmp_git_repo):
    with pytest.raises(GitCommandError, match="No merge, rebase"):
        conflicts.continue_operation(tmp_git_repo)
    with pytest.raises(GitCommandError, match="No merge, rebase"):
        conflicts.abort_operation(tmp_git_repo)


def test_abort_operation_clears_rebase(rebase_conflict_repo):
    conflicts.abort_operation(rebase_conflict_repo)
    assert in_progress_operation(rebase_conflict_repo) is None


def test_has_conflict_markers_finds_label_less_markers_in_crlf_files(merge_conflict_repo):
    Path(merge_conflict_repo, "file.txt").write_bytes(b"<<<<<<<\r\nmain\r\n=======\r\nfeature\r\n>>>>>>>\r\n")
    assert conflicts.has_conflict_markers("file.txt", merge_conflict_repo)


def test_rebase_context_tolerates_non_utf8_branch_name(rebase_conflict_repo):
    Path(rebase_conflict_repo, ".git", "rebase-merge", "head-name").write_bytes(b"refs/heads/caf\xe9\n")
    ctx = conflicts.conflict_context(rebase_conflict_repo)
    assert ctx.headline.startswith("Rebasing caf� onto main")


def test_is_conflicted(merge_conflict_repo):
    assert conflicts.is_conflicted("file.txt", merge_conflict_repo)
    assert not conflicts.is_conflicted("README.md", merge_conflict_repo)
    assert not conflicts.is_conflicted("no-such-file.txt", merge_conflict_repo)
