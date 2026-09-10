from __future__ import annotations

import sys

import typer

from ..git.runner import GitCommandError
from .console import err_console, esc
from .branch_cmds import app as branch_app
from .stash_cmds import app as stash_app
from .tag_cmds import app as tag_app
from .remote_cmds import app as remote_app
from .flow_cmds import app as flow_app
from . import sync_cmds
from . import commit_cmds
from . import log_cmds
from . import tui_cmds
from .merge_rebase_cmds import (
    cherry_pick_app,
    conflicts_app,
    merge_app,
    rebase_app,
    revert_app,
)
from . import nuke_cmds, util_cmds

app = typer.Typer(
    name="mgit",
    help="A git wrapper with rich log search, git-flow helpers, and an optional modern TUI.",
    no_args_is_help=True,
)
app.add_typer(branch_app, name="branch")
app.add_typer(stash_app, name="stash")
app.add_typer(tag_app, name="tag")
app.add_typer(remote_app, name="remote")
app.add_typer(flow_app, name="flow")
app.add_typer(rebase_app, name="rebase")
app.add_typer(merge_app, name="merge")
app.add_typer(cherry_pick_app, name="cherry-pick")
app.add_typer(revert_app, name="revert")
app.add_typer(conflicts_app, name="conflicts")
app.command("push")(sync_cmds.push_cmd)
app.command("pull")(sync_cmds.pull_cmd)
app.command("fetch")(sync_cmds.fetch_cmd)
app.command("sync")(sync_cmds.sync_cmd)
app.command("commit")(commit_cmds.commit_cmd)
app.command("commit-empty")(commit_cmds.commit_empty_cmd)
app.command("amend")(commit_cmds.amend_cmd)
app.command("undo")(commit_cmds.undo_cmd)
app.command("log")(log_cmds.log_cmd)
app.command("diff")(log_cmds.diff_cmd)
app.command("reset-hard")(nuke_cmds.reset_hard_cmd)
app.command("nuke")(nuke_cmds.nuke_cmd)
app.command("nuke-branch")(nuke_cmds.nuke_branch_cmd)
app.command("whoami")(util_cmds.whoami_cmd)
app.command("root")(util_cmds.root_cmd)
app.command("ignored")(util_cmds.ignored_cmd)
app.command("aliases")(util_cmds.aliases_cmd)
app.command("repo-info")(util_cmds.repo_info_cmd)
app.command("tui")(tui_cmds.tui_cmd)
app.add_typer(util_cmds.config_app, name="config")


def main() -> None:
    try:
        app()
    except GitCommandError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {esc(exc.stderr.strip() or str(exc))}")
        sys.exit(exc.returncode or 1)
