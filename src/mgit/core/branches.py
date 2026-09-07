from __future__ import annotations

from ..git.repo import default_remote, infer_base_branch, require_branch
from ..git.runner import GitCommandError, run


def list_branches(cwd: str | None = None) -> list[str]:
    out = run(["branch", "--format=%(refname:short)"], cwd=cwd)
    return [b for b in out.splitlines() if b]


def new_branch(name: str, start_point: str | None = None, cwd: str | None = None) -> None:
    args = ["checkout", "-b", name]
    if start_point:
        args.append(start_point)
    run(args, cwd=cwd)


def switch_branch(name: str, cwd: str | None = None) -> None:
    if name in list_branches(cwd):
        run(["checkout", name], cwd=cwd)
        return
    if "/" in name:
        run(["checkout", "-b", name.split("/", 1)[1], "--track", name], cwd=cwd)
        return
    run(["checkout", name], cwd=cwd)


def delete_branch(name: str, force: bool = False, cwd: str | None = None) -> None:
    run(["branch", "-D" if force else "-d", name], cwd=cwd)


def delete_remote_branch(name: str, remote: str | None = None, cwd: str | None = None) -> None:
    if "/" in name and remote is None:
        remote, name = name.split("/", 1)
    remote = remote or default_remote(cwd)
    run(["push", remote, "--delete", name], cwd=cwd)


def rename_branch(old: str, new: str, cwd: str | None = None) -> None:
    if new in list_branches(cwd):
        raise GitCommandError(["branch", "-m", old, new], 1, f"branch '{new}' already exists")
    run(["branch", "-m", old, new], cwd=cwd)


def merged_branches(cwd: str | None = None) -> list[str]:
    out = run(["branch", "--merged"], cwd=cwd)
    return [line.replace("*", "").strip() for line in out.splitlines() if line.strip()]


def unmerged_branches(cwd: str | None = None) -> list[str]:
    out = run(["branch", "--no-merged"], cwd=cwd)
    return [line.replace("*", "").strip() for line in out.splitlines() if line.strip()]


def prune_gone(force: bool = False, cwd: str | None = None) -> list[str]:
    run(["fetch", "--prune"], cwd=cwd)
    out = run(["branch", "-vv"], cwd=cwd)
    gone = [
        line.replace("*", "").strip().split()[0]
        for line in out.splitlines()
        if ": gone]" in line
    ]
    for name in gone:
        delete_branch(name, force=force, cwd=cwd)
    return gone


def branch_report(branch: str | None = None, base: str | None = None, cwd: str | None = None) -> dict:
    branch = branch or require_branch(cwd)
    base = base or infer_base_branch(cwd)
    merge_base = run(["merge-base", base, branch], cwd=cwd)
    commits = [c for c in run(["log", "--oneline", f"{merge_base}..{branch}"], cwd=cwd).splitlines() if c]
    files = [f for f in run(["diff", "--name-status", f"{merge_base}..{branch}"], cwd=cwd).splitlines() if f]
    return {"branch": branch, "base": base, "merge_base": merge_base, "commits": commits, "files": files}
