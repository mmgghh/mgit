from __future__ import annotations

from ..git.repo import current_branch, in_progress_operation, repo_root
from ..git.runner import run


def whoami(cwd: str | None = None) -> dict:
    return {
        "name": run(["config", "user.name"], cwd=cwd, check=False),
        "email": run(["config", "user.email"], cwd=cwd, check=False),
    }


def ignored_files(cwd: str | None = None) -> list[str]:
    out = run(["status", "--ignored", "--porcelain"], cwd=cwd)
    return [line[3:] for line in out.splitlines() if line.startswith("!!")]


def aliases(cwd: str | None = None) -> list[str]:
    out = run(["config", "--get-regexp", r"^alias\."], cwd=cwd, check=False)
    return out.splitlines() if out else []


def summary(cwd: str | None = None) -> dict:
    return {
        "root": repo_root(cwd),
        "branch": current_branch(cwd),
        "in_progress": in_progress_operation(cwd),
        "remotes": [r for r in run(["remote", "-v"], cwd=cwd).splitlines() if r],
    }
