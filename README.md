# mgit

A git wrapper CLI with rich log search filters (author, date range, message,
path, branch, merges), a full git-flow branch model, and safety-railed
merge/rebase/cherry-pick/stash helpers. Shells out to your system `git` —
no bundled git implementation.

## Install

    pip install -e .

Requires Python 3.11+.

### Termux

    pkg install git python
    pip install mgit

`mgit` has no compiled dependencies (`typer` + `rich`, both pure Python), so
it installs the same way on Termux as on desktop Linux/macOS.

## Usage

    mgit branch list
    mgit log --author=alice --since=2026-01-01 --until=2026-02-01
    mgit flow init
    mgit flow feature start login
    mgit stash save "WIP"
    mgit rebase continue

Run `mgit --help` for the full command tree, or `mgit <group> --help` for
any subcommand group's options.

## Configuration

Global config: `~/.config/mgit/config.toml`. Per-repo override: `.mgit.toml`
at the repo root. Read a value with `mgit config get <key>`, write one with
`mgit config set <key> <value>` (add `--global` to write to the global file).

## TUI

An interactive Textual-based TUI is available as an optional extra:

    pip install mgit[tui]
    mgit tui

It currently covers repo status (`r` to refresh), branch list/switch
(`Enter` to switch), and a commit log browser with author/since/until/grep
filters (`d` on a commit to view its diff). Stash, git-flow, merge/rebase,
and other mutating operations stay CLI-only for now.
