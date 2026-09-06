from __future__ import annotations

from dataclasses import dataclass

from ..git.runner import run

_FIELD_SEP = "\x1f"
_FORMAT = f"%H{_FIELD_SEP}%h{_FIELD_SEP}%an{_FIELD_SEP}%ad{_FIELD_SEP}%s"


@dataclass
class LogFilter:
    author: str | None = None
    since: str | None = None
    until: str | None = None
    grep: str | None = None
    path: str | None = None
    branch: str | None = None
    merges: bool | None = None
    limit: int | None = None


@dataclass
class Commit:
    sha: str
    short_sha: str
    author: str
    date: str
    subject: str


def _build_args(f: LogFilter) -> list[str]:
    args = ["log", f"--format={_FORMAT}", "--date=iso-strict"]
    if f.author:
        args.append(f"--author={f.author}")
    if f.since:
        args.append(f"--since={f.since}")
    if f.until:
        args.append(f"--until={f.until}")
    if f.grep:
        args.append(f"--grep={f.grep}")
    if f.merges is True:
        args.append("--merges")
    elif f.merges is False:
        args.append("--no-merges")
    if f.limit:
        args.append(f"-n{f.limit}")
    if f.branch:
        args.append(f.branch)
    if f.path:
        args += ["--", f.path]
    return args


def search(f: LogFilter, cwd: str | None = None) -> list[Commit]:
    out = run(_build_args(f), cwd=cwd)
    commits = []
    for line in out.splitlines():
        if not line:
            continue
        sha, short_sha, author, date, subject = line.split(_FIELD_SEP, 4)
        commits.append(Commit(sha, short_sha, author, date, subject))
    return commits


def diff(staged: bool = False, ref_a: str | None = None, ref_b: str | None = None, cwd: str | None = None) -> str:
    args = ["diff"]
    if staged:
        args.append("--cached")
    if ref_a:
        args.append(ref_a)
    if ref_b:
        args.append(ref_b)
    return run(args, cwd=cwd)
