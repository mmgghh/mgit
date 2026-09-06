from mgit.core import remotes, tags


def test_new_and_list_tags(tmp_git_repo):
    tags.new_tag("v1.0.0", "first release", cwd=tmp_git_repo)
    assert "v1.0.0" in tags.list_tags(tmp_git_repo)


def test_delete_tag(tmp_git_remote):
    import subprocess
    tags.new_tag("v0.1.0", cwd=tmp_git_remote)
    tags.push_tag("v0.1.0", cwd=tmp_git_remote)
    remote_before = subprocess.run(["git", "ls-remote", "--tags", "origin"], cwd=tmp_git_remote, capture_output=True, text=True, check=True).stdout
    assert "v0.1.0" in remote_before
    tags.delete_tag("v0.1.0", cwd=tmp_git_remote)
    assert "v0.1.0" not in tags.list_tags(tmp_git_remote)
    remote_after = subprocess.run(["git", "ls-remote", "--tags", "origin"], cwd=tmp_git_remote, capture_output=True, text=True, check=True).stdout
    assert "v0.1.0" not in remote_after


def test_push_all_tags(tmp_git_remote):
    tags.new_tag("v1.0.0", cwd=tmp_git_remote)
    tags.new_tag("v2.0.0", cwd=tmp_git_remote)
    tags.push_tag(cwd=tmp_git_remote)
    import subprocess
    out = subprocess.run(["git", "ls-remote", "--tags", "origin"], cwd=tmp_git_remote, capture_output=True, text=True, check=True)
    assert "v1.0.0" in out.stdout and "v2.0.0" in out.stdout


def test_list_remotes(tmp_git_remote):
    entries = remotes.list_remotes(tmp_git_remote)
    assert any("origin" in e for e in entries)


def test_add_and_delete_remote(tmp_git_repo, tmp_path):
    bare = tmp_path / "upstream.git"
    import subprocess
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    remotes.add_remote("upstream", str(bare), cwd=tmp_git_repo)
    assert any("upstream" in e for e in remotes.list_remotes(tmp_git_repo))
    remotes.delete_remote("upstream", cwd=tmp_git_repo)
    assert not any("upstream" in e for e in remotes.list_remotes(tmp_git_repo))
