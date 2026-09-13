from mgit.cli.main import app as mgit_app
from mgit.tui.run.discovery import discover_commands


def test_discover_commands_includes_flat_and_nested_leaves():
    entries = discover_commands(mgit_app)
    paths = {tuple(e.path) for e in entries}
    assert ("push",) in paths
    assert ("branch", "delete") in paths
    assert ("config", "set") in paths


def test_discover_commands_excludes_groups_and_carries_help():
    entries = discover_commands(mgit_app)
    by_path = {tuple(e.path): e for e in entries}
    assert ("branch",) not in by_path
    assert "Delete a local branch" in by_path[("branch", "delete")].help


def test_discover_commands_sorted_by_path():
    entries = discover_commands(mgit_app)
    paths = [e.path for e in entries]
    assert paths == sorted(paths)
