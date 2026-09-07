from __future__ import annotations

from pathlib import Path

from .runner import GitCommandError, run


def is_git_repo(cwd: str | None = None) -> bool:
    try:
        return run(["rev-parse", "--is-inside-work-tree"], cwd=cwd) == "true"
    except GitCommandError:
        return False


def repo_root(cwd: str | None = None) -> str:
    return run(["rev-parse", "--show-toplevel"], cwd=cwd)


def current_branch(cwd: str | None = None) -> str | None:
    name = run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    return None if name == "HEAD" else name


def is_detached(cwd: str | None = None) -> bool:
    return current_branch(cwd) is None


def require_branch(cwd: str | None = None) -> str:
    branch = current_branch(cwd)
    if branch is None:
        raise GitCommandError(["status"], 1, "HEAD is detached; checkout a branch first")
    return branch


def in_progress_operation(cwd: str | None = None) -> str | None:
    root = Path(repo_root(cwd))
    git_dir = Path(run(["rev-parse", "--git-dir"], cwd=cwd))
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    if (git_dir / "CHERRY_PICK_HEAD").exists():
        return "cherry-pick"
    if (git_dir / "REVERT_HEAD").exists():
        return "revert"
    if (git_dir / "MERGE_HEAD").exists():
        return "merge"
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        return "rebase"
    return None


def has_upstream(branch: str | None = None, cwd: str | None = None) -> bool:
    branch = branch or current_branch(cwd)
    if branch is None:
        return False
    return run(["rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"], cwd=cwd, check=False) != ""


def default_remote(cwd: str | None = None) -> str:
    remotes = [r for r in run(["remote"], cwd=cwd).splitlines() if r]
    if not remotes:
        raise GitCommandError(["remote"], 1, "no remotes configured")
    return "origin" if "origin" in remotes else remotes[0]


def infer_base_branch(cwd: str | None = None) -> str:
    for name in ("main", "master", "develop"):
        if run(["rev-parse", "--verify", "--quiet", name], cwd=cwd, check=False):
            return name
    try:
        remote = default_remote(cwd)
        head = run(["symbolic-ref", f"refs/remotes/{remote}/HEAD"], cwd=cwd, check=False)
        if head:
            return head.rsplit("/", 1)[-1]
    except GitCommandError:
        pass
    raise GitCommandError(["rev-parse"], 1, "could not infer a base branch")
