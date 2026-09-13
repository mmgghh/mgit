import typer
import typer.main

from mgit.cli.main import app as mgit_app
from mgit.tui.run.fields import FlagField, IntField, RefField, TextField, build_field, render_tokens


def _params(path: list[str]) -> dict:
    root = typer.main.get_command(mgit_app)
    ctx = typer.Context(root, info_name="mgit")
    command = root
    for name in path:
        command = command.get_command(ctx, name)
        ctx = typer.Context(command, info_name=name, parent=ctx)
    return {p.name: p for p in command.params}


def test_build_field_classifies_string_argument_as_text():
    params = _params(["branch", "new"])
    spec = build_field(["branch", "new"], params["name"])
    assert isinstance(spec, TextField)
    assert spec.opt is None
    assert spec.required is True


def test_build_field_classifies_bool_option_as_flag():
    params = _params(["branch", "delete"])
    spec = build_field(["branch", "delete"], params["force"])
    assert isinstance(spec, FlagField)
    assert spec.opt == "--force"
    assert spec.default is False


def test_build_field_classifies_int_option_as_int_field():
    params = _params(["log"])
    spec = build_field(["log"], params["limit"])
    assert isinstance(spec, IntField)
    assert spec.opt == "--limit"


def test_build_field_uses_ref_hint_over_generic_classification():
    params = _params(["branch", "delete"])
    spec = build_field(["branch", "delete"], params["name"])
    assert isinstance(spec, RefField)
    assert spec.opt is None
    assert spec.required is True


def test_render_tokens_text_field_skips_default():
    spec = TextField(label="name", opt=None, default="", required=False)
    assert render_tokens(spec, "") == []
    assert render_tokens(spec, "feature") == ["feature"]


def test_render_tokens_flag_field_only_emits_when_true():
    spec = FlagField(label="force", opt="--force", default=False)
    assert render_tokens(spec, False) == []
    assert render_tokens(spec, True) == ["--force"]


def test_render_tokens_ref_field_emits_opt_and_value():
    spec = RefField(label="remote", opt="--remote", loader=lambda cwd: [])
    assert render_tokens(spec, None) == []
    assert render_tokens(spec, "origin") == ["--remote", "origin"]
