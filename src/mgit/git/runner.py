from __future__ import annotations

import os
import subprocess


class GitCommandError(RuntimeError):
    def __init__(self, args: list[str], returncode: int, stderr: str) -> None:
        self.command = args
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git {' '.join(args)} failed ({returncode}): {stderr.strip()}")


def run(args: list[str], cwd: str | None = None, check: bool = True, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=None if env is None else {**os.environ, **env},
    )
    if check and result.returncode != 0:
        raise GitCommandError(args, result.returncode, result.stderr)
    return result.stdout.rstrip("\n")


def run_bytes(args: list[str], cwd: str | None = None) -> bytes:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        raise GitCommandError(args, result.returncode, result.stderr.decode("utf-8", errors="replace"))
    return result.stdout
