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

## Diffs and conflicts

If [delta](https://github.com/dandavison/delta) is installed, `mgit diff`
(on a terminal) and every diff in the TUI are shown through it in
side-by-side layout; otherwise you get plain `git diff` output. Set
`mgit config set diff.side_by_side false` for delta's unified layout (with
delta's default styling, since this bypasses your gitconfig `[delta]`
settings).

During a merge, rebase, cherry-pick, revert or `git am`, `mgit conflicts show <path>`
says which side is which — during a rebase git's "ours" is the upstream you
are rebasing onto and "theirs" is your own commit — then diffs the two sides
(`--mode base-ours` / `--mode base-theirs` show what each side changed).

## TUI

An interactive Textual-based TUI is available as an optional extra:

    pip install mgit[tui]
    mgit tui

It has five tabs: Run (browse, fill in, and execute any mgit command,
including stash, git-flow, merge/rebase, and other mutating operations),
Status (`r` to refresh), Conflicts (each conflicted file's two sides, named
by what they are, plus their diff; `1`/`2` take a side, `e` edits, `a` marks
resolved, `m` cycles the diff, `C`/`A` continue/abort — the TUI opens here
when a conflict is in progress), Branches (list/switch, `Enter` to switch),
and Log (a commit browser with author/since/until/grep filters, `d` on a
commit to view its diff). Press `F1` for all keys.
