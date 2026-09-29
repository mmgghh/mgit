import os
import shutil

import pytest
from rich.text import Text

from mgit.git import delta

SAMPLE = (
    "diff --git a/f.txt b/f.txt\n"
    "index 1111111..2222222 100644\n"
    "--- a/f.txt\n"
    "+++ b/f.txt\n"
    "@@ -1 +1 @@\n"
    "-old line\n"
    "+new line\n"
)
needs_delta = pytest.mark.skipif(shutil.which("delta") is None, reason="delta not installed")


def _fake_delta(tmp_path, monkeypatch, script):
    fake = tmp_path / "bin" / "delta"
    fake.parent.mkdir()
    fake.write_text(f"#!/bin/sh\n{script}\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake.parent}{os.pathsep}{os.environ['PATH']}")
    return fake


def test_render_returns_none_without_delta(monkeypatch):
    monkeypatch.setattr(delta.shutil, "which", lambda name: None)
    assert delta.render(SAMPLE, 80) is None


def test_render_empty_diff_is_empty_string():
    assert delta.render("", 80) == ""


def test_render_returns_none_when_delta_fails(tmp_path, monkeypatch):
    _fake_delta(tmp_path, monkeypatch, "exit 3")
    assert delta.render(SAMPLE, 80) is None


def test_render_passes_layout_flags(tmp_path, monkeypatch):
    _fake_delta(tmp_path, monkeypatch, 'echo "$@"')
    assert delta.render(SAMPLE, 72).split() == ["--paging=never", "--width=72", "--side-by-side"]
    assert delta.render(SAMPLE, 72, side_by_side=False).split() == ["--paging=never", "--width=72", "--no-gitconfig"]


def test_page_returns_false_without_delta(monkeypatch):
    monkeypatch.setattr(delta.shutil, "which", lambda name: None)
    assert delta.page(SAMPLE) is False


@needs_delta
def test_render_produces_ansi(tmp_git_repo):
    out = delta.render(SAMPLE, 100, cwd=tmp_git_repo)
    assert "\x1b[" in out
    assert "new line" in Text.from_ansi(out).plain


@needs_delta
def test_render_side_by_side_fits_width(tmp_git_repo):
    out = delta.render(SAMPLE, 60, cwd=tmp_git_repo)
    assert max(Text.from_ansi(line).cell_len for line in out.splitlines()) <= 60
