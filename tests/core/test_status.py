from pathlib import Path
import subprocess

from mgit.core import status as st


def test_working_tree_status_clean(tmp_git_repo):
    result = st.working_tree_status(tmp_git_repo)
    assert result == st.WorkingTreeStatus([], [], [])


def test_working_tree_status_staged_and_unstaged(tmp_git_repo):
    Path(tmp_git_repo, "file.txt").write_text("v1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "add file"], cwd=tmp_git_repo, check=True, capture_output=True)

    Path(tmp_git_repo, "file.txt").write_text("v2\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    Path(tmp_git_repo, "file.txt").write_text("v3\n")

    result = st.working_tree_status(tmp_git_repo)
    assert result.staged == [st.FileEntry("file.txt", "M")]
    assert result.unstaged == [st.FileEntry("file.txt", "M")]
    assert result.untracked == []


def test_working_tree_status_untracked(tmp_git_repo):
    Path(tmp_git_repo, "new.txt").write_text("hi\n")
    result = st.working_tree_status(tmp_git_repo)
    assert result.staged == []
    assert result.unstaged == []
    assert result.untracked == ["new.txt"]
