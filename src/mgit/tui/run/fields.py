from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Union

import typer.core

from .gitrefs import REF_HINTS, RefField

# See discovery.py: this typer version has no external `click` package to
# import — typer.core.TyperArgument/TyperOption are the stable public
# equivalents to click.Argument/click.Option.
TyperParam = Union[typer.core.TyperArgument, typer.core.TyperOption]


@dataclass
class TextField:
    label: str
    opt: str | None
    default: str = ""
    required: bool = False


@dataclass
class FlagField:
    label: str
    opt: str
    default: bool = False


@dataclass
class IntField:
    label: str
    opt: str | None
    default: str = ""


FieldSpec = Union[TextField, FlagField, IntField, RefField]


def build_field(path: list[str], param: TyperParam) -> FieldSpec | None:
    if not getattr(param, "expose_value", True):
        return None

    label = _label(param)
    opt = None if isinstance(param, typer.core.TyperArgument) else _preferred_opt(param.opts)

    hint = REF_HINTS.get((*path, param.name))
    if hint is not None:
        return RefField(label=label, opt=opt, loader=hint, required=param.required)

    if getattr(param, "is_flag", False):
        return FlagField(label=label, opt=opt, default=bool(param.default))

    if param.type.name == "int":
        default = "" if param.default is None else str(param.default)
        return IntField(label=label, opt=opt, default=default)

    default = "" if param.default in (None, ()) else str(param.default)
    return TextField(label=label, opt=opt, default=default, required=param.required)


def _label(param: TyperParam) -> str:
    if getattr(param, "help", None):
        return param.help.strip().splitlines()[0]
    return param.human_readable_name


def _preferred_opt(opts: Sequence[str]) -> str:
    long_opts = [o for o in opts if o.startswith("--")]
    return long_opts[0] if long_opts else opts[0]


def render_tokens(spec: FieldSpec, value) -> list[str]:
    if isinstance(spec, (TextField, RefField)):
        default = getattr(spec, "default", None)
        if not value or value == default:
            return []
        return [value] if spec.opt is None else [spec.opt, value]

    if isinstance(spec, FlagField):
        if value == spec.default:
            return []
        return [spec.opt] if value else []

    if isinstance(spec, IntField):
        if not value or value == spec.default:
            return []
        return [value] if spec.opt is None else [spec.opt, value]

    raise TypeError(f"Unknown field spec: {spec!r}")  # pragma: no cover
