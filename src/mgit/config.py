from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .git.repo import is_git_repo, repo_root

DEFAULTS: dict[str, Any] = {
    "log": {"limit": 30},
}


def _global_config_path() -> Path:
    return Path.home() / ".config" / "mgit" / "config.toml"


def _repo_config_path(cwd: str | None = None) -> Path | None:
    if not is_git_repo(cwd):
        return None
    return Path(repo_root(cwd)) / ".mgit.toml"


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(cwd: str | None = None) -> dict:
    merged = _deep_merge(DEFAULTS, _load_toml(_global_config_path()))
    repo_path = _repo_config_path(cwd)
    if repo_path is not None:
        merged = _deep_merge(merged, _load_toml(repo_path))
    return merged


def get(dotted_key: str, cwd: str | None = None) -> Any:
    node: Any = load_config(cwd)
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def set_value(dotted_key: str, value: str, cwd: str | None = None, global_: bool = False) -> None:
    path = _global_config_path() if global_ else (_repo_config_path(cwd) or _global_config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _load_toml(path)
    node = data
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    _write_toml(path, data)


def _toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def _render_table(section: str, data: dict) -> str:
    lines = [f"[{section}]"]
    nested = ""
    for key, value in data.items():
        if isinstance(value, dict):
            nested += "\n\n" + _render_table(f"{section}.{key}", value)
        else:
            lines.append(f"{key} = {_toml_scalar(value)}")
    return "\n".join(lines) + nested


def _write_toml(path: Path, data: dict) -> None:
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    text = "\n".join(f"{k} = {_toml_scalar(v)}" for k, v in scalars.items())
    for key, value in tables.items():
        text += ("\n\n" if text else "") + _render_table(key, value)
    path.write_text(text + "\n")
