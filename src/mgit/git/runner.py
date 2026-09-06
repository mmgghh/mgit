from __future__ import annotations

import subprocess


class GitCommandError(RuntimeError):
    def __init__(self, args: list[str], returncode: int, stderr: str) -> None:
        self.args = args
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git {' '.join(args)} failed ({returncode}): {stderr.strip()}")


def run(args: list[str], cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise GitCommandError(args, result.returncode, result.stderr)
    return result.stdout.rstrip("\n")
