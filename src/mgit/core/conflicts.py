from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

from ..git.repo import current_branch, git_dir, in_progress_operation, repo_root
from ..git.runner import GitCommandError, run, run_bytes
from . import merge_rebase as mr

NOTHING_IN_PROGRESS = "No merge, rebase, cherry-pick or revert in progress"
DIFF_MODES = ("direct", "base-ours", "base-theirs")
_MODE_STAGES = {"direct": ("2", "3"), "base-ours": ("1", "2"), "base-theirs": ("1", "3")}
_SIDE_STAGES = {"ours": "2", "theirs": "3"}
# git's empty blob; it isn't in every object store, so _empty_blob() writes it.
_EMPTY_BLOB = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


@dataclass
class ConflictContext:
    operation: str
    headline: str
    ours_label: str
    theirs_label: str
    step: tuple[int, int] | None = None


@dataclass
class SideContent:
    text: str
    missing: bool = False
    binary: bool = False


def conflict_context(cwd: str | None = None) -> ConflictContext | None:
    operation = in_progress_operation(cwd)
    if operation is None:
        return None
    gd = git_dir(cwd)
    if operation == "rebase":
        return _rebase_context(gd, cwd)
    branch = current_branch(cwd) or "detached HEAD"
    if operation == "merge":
        sha = _first_line(gd / "MERGE_HEAD")
        name = _branch_name(sha, cwd)
        short = _short(sha, cwd)
        incoming = name or short
        theirs = f"Incoming: {name} ({short})" if name else f"Incoming: {short}"
        return ConflictContext("merge", f"Merging {incoming} into {branch}", f"Current: {branch} (HEAD)", theirs)
    head_file = "CHERRY_PICK_HEAD" if operation == "cherry-pick" else "REVERT_HEAD"
    sha = _first_line(gd / head_file)
    short = _short(sha, cwd)
    if operation == "cherry-pick":
        return ConflictContext(
            "cherry-pick", f"Cherry-picking {short}", f"Current: {branch}", f"Picked: {_describe(sha, cwd)}"
        )
    return ConflictContext(
        "revert", f"Reverting {short}", f"Current: {branch}", f"Revert of {_describe(sha, cwd)}"
    )


def _rebase_context(gd: Path, cwd: str | None) -> ConflictContext:
    state, step_files = gd / "rebase-merge", ("msgnum", "end")
    if not state.is_dir():
        state, step_files = gd / "rebase-apply", ("next", "last")
    branch = (_read(state / "head-name") or "detached HEAD").removeprefix("refs/heads/")
    onto = _read(state / "onto")
    upstream = _branch_name(onto, cwd) or _short(onto, cwd)
    picked = _read(gd / "REBASE_HEAD") or _read(state / "stopped-sha") or _read(state / "original-commit")
    step = _step(state, step_files)
    headline = f"Rebasing {branch} onto {upstream}"
    if step:
        headline += f" (step {step[0]}/{step[1]})"
    return ConflictContext(
        "rebase",
        headline,
        f"Upstream: {upstream} ({_short('HEAD', cwd)})",
        f"Your commit: {_describe(picked, cwd)}",
        step,
    )


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip() or None
    except OSError:
        return None


def _first_line(path: Path) -> str | None:
    text = _read(path)
    return text.splitlines()[0] if text else None


def _step(state: Path, names: tuple[str, str]) -> tuple[int, int] | None:
    try:
        return int(_read(state / names[0]) or ""), int(_read(state / names[1]) or "")
    except ValueError:
        return None


def _summary(sha: str | None, cwd: str | None) -> tuple[str, str]:
    if not sha:
        return "?", ""
    out = run(["log", "-1", "--format=%h%x1f%s", sha], cwd=cwd, check=False)
    if "\x1f" not in out:
        return sha[:7], ""
    short, subject = out.split("\x1f", 1)
    return short, subject


def _short(sha: str | None, cwd: str | None) -> str:
    return _summary(sha, cwd)[0]


def _describe(sha: str | None, cwd: str | None) -> str:
    short, subject = _summary(sha, cwd)
    return f'{short} "{subject}"' if subject else short


def _branch_name(sha: str | None, cwd: str | None) -> str | None:
    if not sha:
        return None
    name = run(
        ["name-rev", "--name-only", "--no-undefined", "--refs=refs/heads/*", "--refs=refs/remotes/*", sha],
        cwd=cwd,
        check=False,
    )
    return name.removeprefix("remotes/") or None


def _locate(path: str, cwd: str | None) -> tuple[str, str]:
    """(repo root, root-relative path) for a path given relative to cwd, as `git status` prints it."""
    root = repo_root(cwd)
    prefix = run(["rev-parse", "--show-prefix"], cwd=cwd)
    return root, posixpath.normpath(prefix + path)


def _literal(path: str) -> str:
    return f":(literal){path}"


def _stages(rel: str, root: str) -> dict[str, str]:
    """Unmerged index stages of a root-relative path, as {stage: blob sha}."""
    stages: dict[str, str] = {}
    for line in run(["ls-files", "-u", "--", _literal(rel)], cwd=root).splitlines():
        meta, _, entry_path = line.partition("\t")
        if entry_path == rel:
            _mode, sha, stage = meta.split()
            stages[stage] = sha
    return stages


def _empty_blob(root: str) -> str:
    return run(["hash-object", "-w", "/dev/null"], cwd=root)


def _side_stage(side: str) -> str:
    if side not in _SIDE_STAGES:
        raise GitCommandError(["checkout"], 1, f"invalid side '{side}', expected 'ours' or 'theirs'")
    return _SIDE_STAGES[side]


def side_diff(path: str, mode: str, cwd: str | None = None) -> str:
    if mode not in _MODE_STAGES:
        raise GitCommandError(["diff"], 1, f"invalid mode '{mode}', expected one of: {', '.join(DIFF_MODES)}")
    root, rel = _locate(path, cwd)
    stages = _stages(rel, root)
    a, b = _MODE_STAGES[mode]
    if a not in stages and b not in stages:
        return ""
    left = f":{a}:{rel}" if a in stages else _empty_blob(root)
    right = f":{b}:{rel}" if b in stages else _empty_blob(root)
    out = run(["diff", left, right], cwd=root)
    # A missing side is diffed as the empty blob; name it after the file.
    return out.replace(f"a/{_EMPTY_BLOB}", f"a/{rel}").replace(f"b/{_EMPTY_BLOB}", f"b/{rel}")


def side_content(path: str, side: str, cwd: str | None = None) -> SideContent:
    stage = _side_stage(side)
    root, rel = _locate(path, cwd)
    sha = _stages(rel, root).get(stage)
    if sha is None:
        return SideContent("", missing=True)
    data = run_bytes(["cat-file", "blob", sha], cwd=root)
    if b"\0" in data[:8000]:  # git's own binary heuristic
        return SideContent("", binary=True)
    return SideContent(data.decode("utf-8", errors="replace"))


# Continue in a captured subprocess must never launch an editor; git keeps the original message.
_NO_EDITOR = {"GIT_EDITOR": "true"}
_CONTINUE = {
    "rebase": mr.rebase_continue,
    "merge": mr.merge_continue,
    "cherry-pick": mr.cherry_pick_continue,
    "revert": mr.revert_continue,
}
_ABORT = {
    "rebase": mr.rebase_abort,
    "merge": mr.merge_abort,
    "cherry-pick": mr.cherry_pick_abort,
    "revert": mr.revert_abort,
}
_MARKER = re.compile(rb"^(?:<{7}|>{7})(?: |\r?$)", re.MULTILINE)


def take_side(path: str, side: str, cwd: str | None = None) -> None:
    stage = _side_stage(side)
    root, rel = _locate(path, cwd)
    if stage in _stages(rel, root):
        run(["checkout", f"--{side}", "--", _literal(rel)], cwd=root)
        run(["add", "--", _literal(rel)], cwd=root)
    else:
        # That side deleted the file: taking it means deleting it.
        run(["rm", "--quiet", "--", _literal(rel)], cwd=root)


def mark_resolved(path: str, cwd: str | None = None) -> None:
    root, rel = _locate(path, cwd)
    run(["add", "-A", "--", _literal(rel)], cwd=root)


def file_path(path: str, cwd: str | None = None) -> Path:
    root, rel = _locate(path, cwd)
    return Path(root) / rel


def has_conflict_markers(path: str, cwd: str | None = None) -> bool:
    try:
        data = file_path(path, cwd).read_bytes()
    except OSError:
        return False
    return _MARKER.search(data) is not None


def _require_operation(cwd: str | None) -> str:
    operation = in_progress_operation(cwd)
    if operation is None:
        raise GitCommandError(["status"], 1, NOTHING_IN_PROGRESS)
    return operation


def continue_operation(cwd: str | None = None) -> str:
    return _CONTINUE[_require_operation(cwd)](cwd, env=_NO_EDITOR)


def abort_operation(cwd: str | None = None) -> str:
    return _ABORT[_require_operation(cwd)](cwd)
