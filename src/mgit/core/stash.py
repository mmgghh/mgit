from __future__ import annotations

from ..git.runner import run


def _ref(index: int | None) -> str:
    return f"stash@{{{index if index is not None else 0}}}"


def has_changes(cwd: str | None = None) -> bool:
    return run(["status", "--porcelain"], cwd=cwd) != ""


def stash_save(message: str | None = None, cwd: str | None = None) -> str | None:
    if not has_changes(cwd):
        return None
    args = ["stash", "push", "-u"]
    if message:
        args += ["-m", message]
    return run(args, cwd=cwd)


def stash_list(cwd: str | None = None) -> list[str]:
    out = run(["stash", "list"], cwd=cwd)
    return out.splitlines() if out else []


def stash_pop(index: int | None = None, cwd: str | None = None) -> str:
    return run(["stash", "pop", _ref(index)], cwd=cwd)


def stash_apply(index: int | None = None, cwd: str | None = None) -> str:
    return run(["stash", "apply", _ref(index)], cwd=cwd)


def stash_drop(index: int | None = None, cwd: str | None = None) -> str:
    return run(["stash", "drop", _ref(index)], cwd=cwd)


def stash_clear(cwd: str | None = None) -> str:
    return run(["stash", "clear"], cwd=cwd)


def stash_show(index: int | None = None, cwd: str | None = None) -> str:
    ref = _ref(index)
    # Show tracked changes
    tracked = run(["stash", "show", "-p", ref], cwd=cwd)
    # Show untracked files (stored in stash@{n}^3) - don't fail if there are none
    untracked = run(["show", f"{ref}^3", "-p"], cwd=cwd, check=False)
    # Combine outputs
    parts = [tracked, untracked]
    return "\n".join(p for p in parts if p).strip()
