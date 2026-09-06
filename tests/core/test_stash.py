from pathlib import Path

from mgit.core import stash


def test_has_changes_false_on_clean_repo(tmp_git_repo):
    assert stash.has_changes(tmp_git_repo) is False


def test_stash_save_noop_on_clean_repo(tmp_git_repo):
    assert stash.stash_save(cwd=tmp_git_repo) is None


def test_stash_save_and_list(tmp_git_repo):
    Path(tmp_git_repo, "dirty.txt").write_text("wip")
    stash.stash_save("WIP: dirty", cwd=tmp_git_repo)
    entries = stash.stash_list(tmp_git_repo)
    assert len(entries) == 1
    assert "WIP: dirty" in entries[0]
    assert stash.has_changes(tmp_git_repo) is False


def test_stash_pop_restores_changes(tmp_git_repo):
    Path(tmp_git_repo, "dirty.txt").write_text("wip")
    stash.stash_save(cwd=tmp_git_repo)
    stash.stash_pop(cwd=tmp_git_repo)
    assert Path(tmp_git_repo, "dirty.txt").read_text() == "wip"
    assert stash.stash_list(tmp_git_repo) == []


def test_stash_apply_keeps_stash_entry(tmp_git_repo):
    Path(tmp_git_repo, "dirty.txt").write_text("wip")
    stash.stash_save(cwd=tmp_git_repo)
    stash.stash_apply(cwd=tmp_git_repo)
    assert Path(tmp_git_repo, "dirty.txt").read_text() == "wip"
    assert len(stash.stash_list(tmp_git_repo)) == 1


def test_stash_drop(tmp_git_repo):
    Path(tmp_git_repo, "dirty.txt").write_text("wip")
    stash.stash_save(cwd=tmp_git_repo)
    stash.stash_drop(cwd=tmp_git_repo)
    assert stash.stash_list(tmp_git_repo) == []


def test_stash_clear(tmp_git_repo):
    Path(tmp_git_repo, "a.txt").write_text("a")
    stash.stash_save(cwd=tmp_git_repo)
    Path(tmp_git_repo, "b.txt").write_text("b")
    stash.stash_save(cwd=tmp_git_repo)
    stash.stash_clear(tmp_git_repo)
    assert stash.stash_list(tmp_git_repo) == []


def test_stash_show_diff(tmp_git_repo):
    Path(tmp_git_repo, "dirty.txt").write_text("wip")
    stash.stash_save(cwd=tmp_git_repo)
    diff = stash.stash_show(cwd=tmp_git_repo)
    assert "dirty.txt" in diff


def test_stash_operations_with_explicit_index(tmp_git_repo):
    Path(tmp_git_repo, "first.txt").write_text("first")
    stash.stash_save("first stash", cwd=tmp_git_repo)
    Path(tmp_git_repo, "second.txt").write_text("second")
    stash.stash_save("second stash", cwd=tmp_git_repo)
    entries = stash.stash_list(tmp_git_repo)
    assert len(entries) == 2
    assert "first stash" in entries[1]
    diff = stash.stash_show(index=1, cwd=tmp_git_repo)
    assert "first.txt" in diff
    stash.stash_drop(index=1, cwd=tmp_git_repo)
    remaining = stash.stash_list(tmp_git_repo)
    assert len(remaining) == 1
    assert "second stash" in remaining[0]
