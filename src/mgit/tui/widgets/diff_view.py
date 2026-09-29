from __future__ import annotations

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from ... import config
from ...git import delta


def _plain(text: str) -> Text:
    return Text(text) if text else Text("(no differences)", style="dim")


class DiffView(VerticalScroll):
    """A scrollable diff, rendered through delta at the widget's width when available."""

    DEFAULT_CSS = "DiffView { height: 1fr; }"

    def __init__(self, text: str = "", cwd: str | None = None, id: str | None = None) -> None:
        super().__init__(id=id)
        self.cwd = cwd
        self._text = text
        self._rendered_width: int | None = None
        self._generation = 0

    @property
    def text(self) -> str:
        return self._text

    def compose(self) -> ComposeResult:
        yield Static(_plain(self._text), classes="diff-body")

    def set_diff(self, text: str) -> None:
        self._text = text
        self._rendered_width = None
        self.query_one(".diff-body", Static).update(_plain(text))
        self.scroll_home(animate=False)
        self._render_at_current_width()

    def on_resize(self) -> None:
        self._render_at_current_width()

    def _render_at_current_width(self) -> None:
        # Always reserve the scrollbar's width so the render width doesn't
        # change when the scrollbar appears, which would re-render in a loop.
        width = self.size.width - self.styles.scrollbar_size_vertical
        if width <= 0 or width == self._rendered_width:
            return
        self._rendered_width = width
        self._generation += 1
        self._render_diff(self._text, width, self._generation)

    @work(thread=True, group="diff-render")
    def _render_diff(self, text: str, width: int, generation: int) -> None:
        side_by_side = config.get_bool("diff.side_by_side", self.cwd)
        rendered = delta.render(text, width, side_by_side=side_by_side, cwd=self.cwd)
        self.app.call_from_thread(self._apply, rendered, generation)

    def _apply(self, rendered: str | None, generation: int) -> None:
        # A newer render (new text or width) supersedes this one.
        if generation != self._generation or not rendered:
            return
        body = Text.from_ansi(rendered, no_wrap=True, overflow="crop")
        self.query_one(".diff-body", Static).update(body)
