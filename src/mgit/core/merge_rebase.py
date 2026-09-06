from __future__ import annotations

from ..git.runner import GitCommandError, run

_CONFLICT_LABELS = {
    "UU": "both modified",
    "AA": "both added",
    "AU": "added by us",
    "UA": "added by them",
    "DU": "deleted by us",
    "UD": "deleted by them",
    "DD": "both deleted",
}
_STAGE = {"base": "1", "ours": "2", "theirs": "3"}


def rebase_continue(cwd: str | None = None) -> str:
    return run(["rebase", "--continue"], cwd=cwd)


def rebase_abort(cwd: str | None = None) -> str:
    return run(["rebase", "--abort"], cwd=cwd)


def rebase_skip(cwd: str | None = None) -> str:
    return run(["rebase", "--skip"], cwd=cwd)


def merge_continue(cwd: str | None = None) -> str:
    return run(["commit", "--no-edit"], cwd=cwd)


def merge_abort(cwd: str | None = None) -> str:
    return run(["merge", "--abort"], cwd=cwd)


def cherry_pick_continue(cwd: str | None = None) -> str:
    return run(["cherry-pick", "--continue"], cwd=cwd)


def cherry_pick_abort(cwd: str | None = None) -> str:
    return run(["cherry-pick", "--abort"], cwd=cwd)


def cherry_pick_skip(cwd: str | None = None) -> str:
    return run(["cherry-pick", "--skip"], cwd=cwd)


def revert_continue(cwd: str | None = None) -> str:
    return run(["revert", "--continue"], cwd=cwd)


def revert_abort(cwd: str | None = None) -> str:
    return run(["revert", "--abort"], cwd=cwd)


def revert_skip(cwd: str | None = None) -> str:
    return run(["revert", "--skip"], cwd=cwd)


def list_conflicts(cwd: str | None = None) -> list[tuple[str, str]]:
    out = run(["status", "--porcelain=v2"], cwd=cwd)
    result = []
    for line in out.splitlines():
        if line.startswith("u "):
            # Fixed fields are "u XY sub m1 m2 m3 mW h1 h2 h3" (10 tokens);
            # everything after is the path, which may itself contain spaces.
            parts = line.split(maxsplit=10)
            xy, path = parts[1], parts[10]
            result.append((path, _CONFLICT_LABELS.get(xy, xy)))
    return result


def conflict_side(path: str, side: str, cwd: str | None = None) -> str:
    if side not in _STAGE:
        raise GitCommandError(["show", f":{side}:{path}"], 1, f"invalid side '{side}', expected 'base', 'ours', or 'theirs'")
    stage = _STAGE[side]
    return run(["show", f":{stage}:{path}"], cwd=cwd)
