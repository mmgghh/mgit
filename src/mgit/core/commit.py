from __future__ import annotations

from ..git.runner import run
from .sync import push as push_branch


def commit(message: str, cwd: str | None = None) -> str:
    run(["add", "-A"], cwd=cwd)
    return run(["commit", "-m", message], cwd=cwd)


def commit_empty(message: str, cwd: str | None = None) -> str:
    return run(["commit", "--allow-empty", "-m", message], cwd=cwd)


def amend(cwd: str | None = None, push_after: bool = False) -> str:
    out = run(["commit", "--amend", "--no-edit"], cwd=cwd)
    if push_after:
        push_branch(force=True, cwd=cwd)
    return out


def undo(hard: bool = False, cwd: str | None = None) -> str:
    return run(["reset", "--hard" if hard else "--mixed", "HEAD~1"], cwd=cwd)
