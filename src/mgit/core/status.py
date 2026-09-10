from __future__ import annotations

from dataclasses import dataclass

from ..git.runner import run


@dataclass
class FileEntry:
    path: str
    code: str


@dataclass
class WorkingTreeStatus:
    staged: list[FileEntry]
    unstaged: list[FileEntry]
    untracked: list[str]


def working_tree_status(cwd: str | None = None) -> WorkingTreeStatus:
    out = run(["status", "--porcelain=v2", "--untracked-files=all"], cwd=cwd)
    staged: list[FileEntry] = []
    unstaged: list[FileEntry] = []
    untracked: list[str] = []
    for line in out.splitlines():
        if not line:
            continue
        if line.startswith("1 "):
            parts = line.split(maxsplit=8)
            xy, path = parts[1], parts[8]
            if xy[0] != ".":
                staged.append(FileEntry(path, xy[0]))
            if xy[1] != ".":
                unstaged.append(FileEntry(path, xy[1]))
        elif line.startswith("2 "):
            parts = line.split(maxsplit=9)
            xy, rest = parts[1], parts[9]
            path = rest.split("\t", 1)[0]
            if xy[0] != ".":
                staged.append(FileEntry(path, xy[0]))
            if xy[1] != ".":
                unstaged.append(FileEntry(path, xy[1]))
        elif line.startswith("? "):
            untracked.append(line[2:])
    return WorkingTreeStatus(staged, unstaged, untracked)
