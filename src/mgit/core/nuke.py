from __future__ import annotations

from ..git.repo import require_branch
from ..git.runner import run


def reset_hard(ref: str, cwd: str | None = None) -> str:
    return run(["reset", "--hard", ref], cwd=cwd)


def nuke(cwd: str | None = None) -> str:
    run(["reset", "--hard"], cwd=cwd)
    return run(["clean", "-fd"], cwd=cwd)


def nuke_branch(cwd: str | None = None) -> str:
    branch = require_branch(cwd)
    return run(["reset", "--hard", f"{branch}@{{upstream}}"], cwd=cwd)
