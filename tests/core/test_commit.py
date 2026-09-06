from pathlib import Path

from mgit.core import commit
from mgit.git.runner import run


def test_commit_stages_and_commits(tmp_git_repo):
    Path(tmp_git_repo, "new.txt").write_text("content")
    commit.commit("add new.txt", cwd=tmp_git_repo)
    log = run(["log", "-1", "--format=%s"], cwd=tmp_git_repo)
    assert log == "add new.txt"
    assert run(["status", "--porcelain"], cwd=tmp_git_repo) == ""


def test_commit_empty(tmp_git_repo):
    commit.commit_empty("chore: trigger", cwd=tmp_git_repo)
    log = run(["log", "-1", "--format=%s"], cwd=tmp_git_repo)
    assert log == "chore: trigger"


def test_amend_changes_last_message_content(tmp_git_repo):
    Path(tmp_git_repo, "a.txt").write_text("a")
    commit.commit("first", cwd=tmp_git_repo)
    Path(tmp_git_repo, "b.txt").write_text("b")
    run(["add", "."], cwd=tmp_git_repo)
    commit.amend(cwd=tmp_git_repo)
    count = run(["rev-list", "--count", "HEAD"], cwd=tmp_git_repo)
    assert count == "2"
    files = run(["show", "--name-only", "--format=", "HEAD"], cwd=tmp_git_repo).splitlines()
    assert "b.txt" in files


def test_undo_keeps_files(tmp_git_repo):
    Path(tmp_git_repo, "c.txt").write_text("c")
    commit.commit("add c", cwd=tmp_git_repo)
    commit.undo(cwd=tmp_git_repo)
    assert Path(tmp_git_repo, "c.txt").exists()
    assert run(["status", "--porcelain"], cwd=tmp_git_repo) != ""


def test_undo_hard_discards_files(tmp_git_repo):
    Path(tmp_git_repo, "d.txt").write_text("d")
    commit.commit("add d", cwd=tmp_git_repo)
    commit.undo(hard=True, cwd=tmp_git_repo)
    assert not Path(tmp_git_repo, "d.txt").exists()


def test_amend_push_after_force_pushes(tmp_git_remote):
    Path(tmp_git_remote, "e.txt").write_text("e")
    commit.commit("add e", cwd=tmp_git_remote)
    run(["push"], cwd=tmp_git_remote)
    Path(tmp_git_remote, "f.txt").write_text("f")
    run(["add", "."], cwd=tmp_git_remote)
    commit.amend(cwd=tmp_git_remote, push_after=True)
    remote_subject = run(["log", "origin/main", "-1", "--format=%s"], cwd=tmp_git_remote)
    assert remote_subject == "add e"
    remote_files = run(["ls-tree", "-r", "--name-only", "origin/main"], cwd=tmp_git_remote).splitlines()
    assert "f.txt" in remote_files
