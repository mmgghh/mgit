from __future__ import annotations

from ..git.repo import default_remote
from ..git.runner import run


def list_tags(cwd: str | None = None) -> list[str]:
    out = run(["tag", "--sort=-creatordate"], cwd=cwd)
    return out.splitlines() if out else []


def new_tag(name: str, message: str | None = None, cwd: str | None = None) -> str:
    return run(["tag", "-a", name, "-m", message or name], cwd=cwd)


def delete_tag(name: str, cwd: str | None = None) -> None:
    run(["tag", "-d", name], cwd=cwd)
    run(["push", default_remote(cwd), "--delete", name], cwd=cwd)


def push_tag(name: str | None = None, cwd: str | None = None) -> str:
    remote = default_remote(cwd)
    if name:
        return run(["push", remote, name], cwd=cwd)
    return run(["push", remote, "--tags"], cwd=cwd)
