from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, OptionList, RichLog, Select, Static, Switch
from textual.widgets.option_list import Option

from ...cli.main import app as mgit_cli_app
from ..run.discovery import CommandEntry, discover_commands
from ..run.fields import FlagField, IntField, RefField, TextField, build_field, render_tokens


CONFIRM_COMMANDS: dict[tuple[str, ...], str] = {
    ("nuke",): "--yes",
    ("nuke-branch",): "--yes",
    ("reset-hard",): "--yes",
    ("tag", "delete"): "--yes",
}


class RunView(Widget):
    DEFAULT_CSS = "RunView { height: 1fr; }"
    can_focus = True

    class CommandChosen(Message):
        bubble = True

        def __init__(self, entry: CommandEntry) -> None:
            self.entry = entry
            super().__init__()

    def __init__(self, cwd: str | None = None) -> None:
        super().__init__()
        self.cwd = cwd
        self._entries = discover_commands(mgit_cli_app)
        self._filtered = self._entries

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search mgit commands...", id="run-search")
        yield OptionList(*self._options(self._entries), id="run-commands")

    def _options(self, entries: list[CommandEntry]):
        for i, entry in enumerate(entries):
            yield Option(f"{' '.join(entry.path)}  {entry.help}", id=str(i))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "run-search":
            return
        query = event.value.strip().lower()
        self._filtered = [
            e for e in self._entries if query in " ".join(e.path).lower() or query in e.help.lower()
        ]
        option_list = self.query_one("#run-commands", OptionList)
        option_list.clear_options()
        option_list.add_options(self._options(self._filtered))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "run-commands":
            return
        index = int(event.option.id)
        entry = self._filtered[index]
        self.post_message(self.CommandChosen(entry))
        self.app.push_screen(CommandFormScreen(entry, self.cwd))


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(self.message, id="confirm-message")
            with Horizontal():
                yield Button("Yes", id="confirm-yes", variant="error")
                yield Button("No", id="confirm-no", variant="primary")

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#confirm-yes")
    def _yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#confirm-no")
    def _no(self) -> None:
        self.dismiss(False)


class CommandFormScreen(ModalScreen[None]):
    BINDINGS = [
        ("escape", "dismiss_screen", "Back"),
        ("ctrl+r", "run", "Run"),
    ]

    def __init__(self, entry: CommandEntry, cwd: str | None) -> None:
        super().__init__()
        self.entry = entry
        self.cwd = cwd
        self.entries: list[tuple[object, Widget]] = []

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="run-fields", can_focus=False):
            yield Static(" ".join(["mgit", *self.entry.path]), id="run-form-title")
            confirm_gated = tuple(self.entry.path) in CONFIRM_COMMANDS
            for param in self.entry.command.params:
                if confirm_gated and param.name == "yes":
                    continue
                spec = build_field(self.entry.path, param)
                if spec is None:
                    continue
                widget = _widget_for(spec, self.cwd)
                self.entries.append((spec, widget))
                required = getattr(spec, "required", False)
                label_text = spec.label + (" (required)" if required else "")
                yield Vertical(Label(label_text), widget, classes="field")
        yield Static(id="run-preview")
        yield Button("Run", id="run-button", variant="primary")
        yield RichLog(id="run-output", highlight=False, markup=False)

    def on_mount(self) -> None:
        self._refresh_preview()

    def action_dismiss_screen(self) -> None:
        self.dismiss()

    def _current_argv(self) -> list[str]:
        tokens: list[str] = []
        for spec, widget in self.entries:
            tokens += render_tokens(spec, _value_of(spec, widget))
        return [*self.entry.path, *tokens]

    def _refresh_preview(self) -> None:
        preview_text = "$ mgit " + shlex.join(self._current_argv())
        self.query_one("#run-preview", Static).update(preview_text)

    @on(Input.Changed)
    @on(Select.Changed)
    @on(Switch.Changed)
    def _on_change(self) -> None:
        self._refresh_preview()

    @on(Button.Pressed, "#run-button")
    def _on_run_pressed(self) -> None:
        self.action_run()

    def _validation_error(self) -> str | None:
        seen_blank_positional = False
        for spec, widget in self.entries:
            if getattr(spec, "opt", None) is not None:
                continue  # only positionals (opt is None) can suffer the shifting bug
            value = _value_of(spec, widget)
            if not value:
                if getattr(spec, "required", False):
                    return f"{spec.label} is required"
                seen_blank_positional = True
            elif seen_blank_positional:
                return f"Cannot set {spec.label} without the earlier positional argument(s)"
        return None

    def action_run(self) -> None:
        error = self._validation_error()
        if error is not None:
            self.app.notify(error, severity="error")
            return
        argv = self._current_argv()
        confirm_flag = CONFIRM_COMMANDS.get(tuple(self.entry.path))
        if confirm_flag is not None:
            self.app.push_screen(
                ConfirmScreen(f"Run mgit {' '.join(argv)}?"),
                lambda confirmed: self._on_confirmed(confirmed, [*argv, confirm_flag]),
            )
            return
        self._start(argv)

    def _on_confirmed(self, confirmed: bool | None, argv: list[str]) -> None:
        if confirmed:
            self._start(argv)

    def _start(self, argv: list[str]) -> None:
        self.query_one("#run-button", Button).disabled = True
        self.query_one("#run-output", RichLog).clear()
        self._run_process(argv)

    @work(thread=True, exclusive=True)
    def _run_process(self, argv: list[str]) -> None:
        env = {**os.environ, "FORCE_COLOR": "1"}
        # Resolve the `mgit` executable next to the *currently running*
        # interpreter (sys.executable), not a bare "mgit" on PATH. A bare
        # name can resolve to a completely different install (e.g. a
        # system/pyenv-wide `mgit`) than the one actually running this TUI
        # process, silently running the wrong code. Fall back to PATH lookup
        # (or a bare "mgit") for non-venv installs (e.g. `pip install --user`)
        # where the console script doesn't live next to sys.executable.
        candidate = Path(sys.executable).parent / "mgit"
        mgit_executable = str(candidate) if candidate.exists() else (shutil.which("mgit") or "mgit")
        try:
            process = subprocess.Popen(
                [mgit_executable, *argv],
                cwd=self.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            self.app.call_from_thread(self.app.notify, str(exc), severity="error", markup=False)
            self.app.call_from_thread(self._finished, 1, notify=False)
            return
        assert process.stdout is not None
        code = 1
        try:
            for line in process.stdout:
                self.app.call_from_thread(self._append_output, line.rstrip("\n"))
            process.wait()
            code = process.returncode
        finally:
            self.app.call_from_thread(self._finished, code)

    def _append_output(self, line: str) -> None:
        """Append a line to the RichLog widget, rendering any ANSI styling."""
        try:
            widget = self.query_one("#run-output", RichLog)
            widget.write(Text.from_ansi(line))
        except NoMatches:
            # Widget might not be available if the screen was dismissed
            pass

    def _finished(self, code: int, *, notify: bool = True) -> None:
        try:
            self.query_one("#run-button", Button).disabled = False
        except NoMatches:
            pass
        if notify:
            self.app.notify(f"exit {code}", severity="error" if code else "information", title="mgit")
        if code == 0 and hasattr(self.app, 'refresh_other_views'):
            self.app.refresh_other_views()


def _widget_for(spec, cwd: str | None):
    if isinstance(spec, TextField):
        return Input(value=spec.default, placeholder=spec.label)
    if isinstance(spec, IntField):
        return Input(value=spec.default, placeholder=spec.label, restrict=r"[0-9]*")
    if isinstance(spec, FlagField):
        return Switch(value=spec.default)
    if isinstance(spec, RefField):
        options = spec.loader(cwd)
        return Select(options, value=Select.NULL, allow_blank=True)
    raise TypeError(f"No widget for {spec!r}")  # pragma: no cover


def _value_of(spec, widget):
    if isinstance(spec, RefField):
        return None if widget.value is Select.NULL else widget.value
    return widget.value
