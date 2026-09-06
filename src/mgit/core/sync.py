from __future__ import annotations

from ..git.repo import current_branch, default_remote, has_upstream, is_detached
from ..git.runner import GitCommandError, run


def _require_branch(cwd: str | None = None) -> str:
    if is_detached(cwd):
        raise GitCommandError(["status"], 1, "HEAD is detached; checkout a branch first")
    return current_branch(cwd)


def fetch_all(cwd: str | None = None) -> str:
    return run(["fetch", "--all", "--prune"], cwd=cwd)


def pull(cwd: str | None = None) -> str:
    _require_branch(cwd)
    return run(["pull", "--rebase"], cwd=cwd)


def push(force: bool = False, cwd: str | None = None) -> str:
    branch = _require_branch(cwd)
    if not has_upstream(branch, cwd):
        remote = default_remote(cwd)
        return run(["push", "-u", remote, branch], cwd=cwd)
    args = ["push"]
    if force:
        args.append("--force-with-lease")
    return run(args, cwd=cwd)


def sync(cwd: str | None = None) -> str:
    _require_branch(cwd)
    fetch_all(cwd)
    return run(["rebase", "@{upstream}"], cwd=cwd)
