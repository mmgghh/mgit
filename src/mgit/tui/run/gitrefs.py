from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...core import branches, remotes, stash, tags


@dataclass
class RefField:
    label: str
    opt: str | None
    loader: Callable[[str | None], list[tuple[str, str]]]
    required: bool = False


def branch_options(cwd: str | None) -> list[tuple[str, str]]:
    return [(name, name) for name in branches.list_branches(cwd)]


def tag_options(cwd: str | None) -> list[tuple[str, str]]:
    return [(name, name) for name in tags.list_tags(cwd)]


def remote_options(cwd: str | None) -> list[tuple[str, str]]:
    # git remote -v returns lines like "origin	url (fetch)"
    # Extract unique remote names from the first field
    seen = set()
    result = []
    for line in remotes.list_remotes(cwd):
        if line:
            name = line.split()[0]
            if name not in seen:
                seen.add(name)
                result.append((name, name))
    return result


def stash_options(cwd: str | None) -> list[tuple[str, str]]:
    return [(line, str(i)) for i, line in enumerate(stash.stash_list(cwd))]


REF_HINTS: dict[tuple[str, ...], Callable[[str | None], list[tuple[str, str]]]] = {
    ("branch", "delete", "name"): branch_options,
    ("branch", "delete-remote", "name"): branch_options,
    ("branch", "delete-remote", "remote"): remote_options,
    ("branch", "switch", "name"): branch_options,
    ("branch", "rename", "old"): branch_options,
    ("tag", "delete", "name"): tag_options,
    ("tag", "push", "name"): tag_options,
    ("remote", "delete", "name"): remote_options,
    ("stash", "pop", "index"): stash_options,
    ("stash", "apply", "index"): stash_options,
    ("stash", "drop", "index"): stash_options,
    ("stash", "show", "index"): stash_options,
}
