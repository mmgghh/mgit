import subprocess

from mgit.tui.run.gitrefs import REF_HINTS, branch_options, remote_options, stash_options, tag_options


def test_branch_options_lists_real_branches(tmp_git_repo):
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    options = branch_options(tmp_git_repo)
    assert ("feature", "feature") in options
    assert ("main", "main") in options


def test_tag_options_lists_real_tags(tmp_git_repo):
    subprocess.run(["git", "tag", "v1.0"], cwd=tmp_git_repo, check=True, capture_output=True)
    assert tag_options(tmp_git_repo) == [("v1.0", "v1.0")]


def test_remote_options_lists_real_remotes(tmp_git_remote):
    assert remote_options(tmp_git_remote) == [("origin", "origin")]


def test_stash_options_pairs_message_with_numeric_index(tmp_git_repo):
    (tmp_git_repo + "/README.md",)  # noop; keep flake8 happy about unused import style
    with open(tmp_git_repo + "/README.md", "a") as f:
        f.write("changed\n")
    subprocess.run(["git", "stash", "push", "-u", "-m", "wip"], cwd=tmp_git_repo, check=True, capture_output=True)
    options = stash_options(tmp_git_repo)
    assert len(options) == 1
    label, value = options[0]
    assert "wip" in label
    assert value == "0"


def test_ref_hints_covers_expected_parameters():
    assert REF_HINTS[("branch", "delete", "name")] is branch_options
    assert REF_HINTS[("branch", "delete-remote", "name")] is branch_options
    assert REF_HINTS[("branch", "delete-remote", "remote")] is remote_options
    assert REF_HINTS[("branch", "switch", "name")] is branch_options
    assert REF_HINTS[("branch", "rename", "old")] is branch_options
    assert REF_HINTS[("tag", "delete", "name")] is tag_options
    assert REF_HINTS[("tag", "push", "name")] is tag_options
    assert REF_HINTS[("remote", "delete", "name")] is remote_options
    for cmd in ("pop", "apply", "drop", "show"):
        assert REF_HINTS[("stash", cmd, "index")] is stash_options
