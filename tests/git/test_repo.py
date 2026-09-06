from mgit.git import repo


def test_is_git_repo_true(tmp_git_repo):
    assert repo.is_git_repo(tmp_git_repo) is True


def test_is_git_repo_false(tmp_path):
    assert repo.is_git_repo(str(tmp_path)) is False


def test_repo_root(tmp_git_repo):
    assert repo.repo_root(tmp_git_repo) == tmp_git_repo


def test_current_branch(tmp_git_repo):
    assert repo.current_branch(tmp_git_repo) == "main"


def test_is_detached_false_on_branch(tmp_git_repo):
    assert repo.is_detached(tmp_git_repo) is False


def test_in_progress_operation_none(tmp_git_repo):
    assert repo.in_progress_operation(tmp_git_repo) is None


def test_has_upstream_false_without_remote(tmp_git_repo):
    assert repo.has_upstream(cwd=tmp_git_repo) is False


def test_has_upstream_true_after_push(tmp_git_remote):
    assert repo.has_upstream(cwd=tmp_git_remote) is True


def test_default_remote(tmp_git_remote):
    assert repo.default_remote(tmp_git_remote) == "origin"


def test_infer_base_branch_main(tmp_git_repo):
    assert repo.infer_base_branch(tmp_git_repo) == "main"
