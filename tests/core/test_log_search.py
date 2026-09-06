import os
import subprocess
from pathlib import Path

from mgit.core.log_search import LogFilter, diff, search


def _commit_as(repo, filename, content, message, author_name, author_email, date):
    Path(repo, filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email,
        "GIT_COMMITTER_DATE": date,
    })
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True, env=env)


def _seed(repo):
    _commit_as(repo, "a.txt", "a", "alice: add a", "Alice", "alice@example.com", "2026-01-01T10:00:00")
    _commit_as(repo, "b.txt", "b", "bob: add b", "Bob", "bob@example.com", "2026-02-01T10:00:00")
    _commit_as(repo, "c.txt", "c", "alice: fix bug", "Alice", "alice@example.com", "2026-03-01T10:00:00")


def test_search_by_author(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(author="Alice"), cwd=tmp_git_repo)
    assert {c.subject for c in commits} == {"alice: add a", "alice: fix bug"}


def test_search_by_date_range(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(since="2026-01-15", until="2026-02-15"), cwd=tmp_git_repo)
    assert [c.subject for c in commits] == ["bob: add b"]


def test_search_by_grep(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(grep="fix"), cwd=tmp_git_repo)
    assert [c.subject for c in commits] == ["alice: fix bug"]


def test_search_by_path(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(path="b.txt"), cwd=tmp_git_repo)
    assert [c.subject for c in commits] == ["bob: add b"]


def test_search_limit(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(limit=1), cwd=tmp_git_repo)
    assert len(commits) == 1
    assert commits[0].subject == "alice: fix bug"


def test_search_no_merges_excludes_merge_commits(tmp_git_repo):
    _seed(tmp_git_repo)
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit_as(tmp_git_repo, "d.txt", "d", "feature commit", "Alice", "alice@example.com", "2026-03-02T10:00:00")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "merge", "--no-ff", "-m", "merge feature", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    no_merges = search(LogFilter(merges=False), cwd=tmp_git_repo)
    only_merges = search(LogFilter(merges=True), cwd=tmp_git_repo)
    assert "merge feature" not in [c.subject for c in no_merges]
    assert [c.subject for c in only_merges] == ["merge feature"]


def test_diff_staged(tmp_git_repo):
    Path(tmp_git_repo, "staged.txt").write_text("new")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    out = diff(staged=True, cwd=tmp_git_repo)
    assert "staged.txt" in out


def test_diff_between_refs(tmp_git_repo):
    _seed(tmp_git_repo)
    out = diff(ref_a="HEAD~2", ref_b="HEAD", cwd=tmp_git_repo)
    assert "b.txt" in out and "c.txt" in out


def test_search_by_branch(tmp_git_repo):
    _seed(tmp_git_repo)
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmp_git_repo, check=True, capture_output=True)
    _commit_as(tmp_git_repo, "d.txt", "d", "feature commit", "Alice", "alice@example.com", "2026-03-02T10:00:00")
    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    commits_main = search(LogFilter(), cwd=tmp_git_repo)
    commits_feature = search(LogFilter(branch="feature"), cwd=tmp_git_repo)
    assert "feature commit" not in [c.subject for c in commits_main]
    assert "feature commit" in [c.subject for c in commits_feature]


def test_search_returns_full_commit_metadata(tmp_git_repo):
    _seed(tmp_git_repo)
    commits = search(LogFilter(limit=1), cwd=tmp_git_repo)
    commit = commits[0]
    assert commit.subject == "alice: fix bug"
    assert commit.author == "Alice"
    assert commit.date.startswith("2026-03-01")
    assert len(commit.sha) == 40
    assert commit.sha.startswith(commit.short_sha)


def test_search_handles_subject_with_field_separator_byte(tmp_git_repo):
    Path(tmp_git_repo, "weird.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "odd\x1fsubject"], cwd=tmp_git_repo, check=True, capture_output=True)
    commits = search(LogFilter(limit=1), cwd=tmp_git_repo)
    assert commits[0].subject == "odd\x1fsubject"
