from __future__ import annotations

from ..git.repo import default_remote, has_upstream, require_branch
from ..git.runner import run


def fetch_all(cwd: str | None = None) -> str:
    return run(["fetch", "--all", "--prune"], cwd=cwd)


def pull(cwd: str | None = None) -> str:
    require_branch(cwd)
    return run(["pull", "--rebase"], cwd=cwd)


def push(force: bool = False, cwd: str | None = None) -> str:
    branch = require_branch(cwd)
    if not has_upstream(branch, cwd):
        remote = default_remote(cwd)
        return run(["push", "-u", remote, branch], cwd=cwd)
    args = ["push"]
    if force:
        args.append("--force-with-lease")
    return run(args, cwd=cwd)


def sync(cwd: str | None = None) -> str:
    require_branch(cwd)
    fetch_all(cwd)
    return run(["rebase", "@{upstream}"], cwd=cwd)
