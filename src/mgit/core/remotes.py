from __future__ import annotations

from ..git.runner import run


def list_remotes(cwd: str | None = None) -> list[str]:
    out = run(["remote", "-v"], cwd=cwd)
    return out.splitlines() if out else []


def add_remote(name: str, url: str, cwd: str | None = None) -> None:
    run(["remote", "add", name, url], cwd=cwd)


def delete_remote(name: str, cwd: str | None = None) -> None:
    run(["remote", "remove", name], cwd=cwd)
