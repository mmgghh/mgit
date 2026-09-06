from pathlib import Path
import subprocess

from mgit.core import flow
from mgit.git.runner import run


def _commit(repo, filename, content, message):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def test_init_flow_creates_develop_and_config(tmp_git_repo):
    flow.init_flow(cwd=tmp_git_repo)
    branches = run(["branch", "--format=%(refname:short)"], cwd=tmp_git_repo).splitlines()
    assert "develop" in branches
    assert run(["config", "--get", "gitflow.prefix.feature"], cwd=tmp_git_repo) == "feature/"


def test_feature_start_and_list(tmp_git_repo):
    flow.init_flow(cwd=tmp_git_repo)
    flow.feature_start("login", cwd=tmp_git_repo)
    from mgit.git.repo import current_branch
    assert current_branch(tmp_git_repo) == "feature/login"
    assert flow.feature_list(tmp_git_repo) == ["feature/login"]


def test_feature_finish_merges_into_develop(tmp_git_repo):
    flow.init_flow(cwd=tmp_git_repo)
    flow.feature_start("login", cwd=tmp_git_repo)
    _commit(tmp_git_repo, "login.txt", "code", "add login")
    flow.feature_finish("login", cwd=tmp_git_repo)
    from mgit.git.repo import current_branch
    assert current_branch(tmp_git_repo) == "develop"
    assert Path(tmp_git_repo, "login.txt").exists()
    branches = run(["branch", "--format=%(refname:short)"], cwd=tmp_git_repo).splitlines()
    assert "feature/login" not in branches


def test_release_start_finish_tags_and_merges_both(tmp_git_repo):
    flow.init_flow(cwd=tmp_git_repo)
    flow.release_start("1.0.0", cwd=tmp_git_repo)
    _commit(tmp_git_repo, "CHANGELOG.md", "1.0.0", "prep release")
    flow.release_finish("1.0.0", cwd=tmp_git_repo)
    from mgit.git.repo import current_branch
    assert current_branch(tmp_git_repo) == "develop"
    assert "1.0.0" in run(["tag"], cwd=tmp_git_repo).splitlines()
    main_files = run(["ls-tree", "-r", "--name-only", "main"], cwd=tmp_git_repo).splitlines()
    assert "CHANGELOG.md" in main_files


def test_hotfix_start_finish_tags_and_merges_both(tmp_git_repo):
    flow.init_flow(cwd=tmp_git_repo)
    flow.hotfix_start("1.0.1", cwd=tmp_git_repo)
    _commit(tmp_git_repo, "fix.txt", "fix", "urgent fix")
    flow.hotfix_finish("1.0.1", cwd=tmp_git_repo)
    assert "1.0.1" in run(["tag"], cwd=tmp_git_repo).splitlines()
    develop_files = run(["ls-tree", "-r", "--name-only", "develop"], cwd=tmp_git_repo).splitlines()
    assert "fix.txt" in develop_files
