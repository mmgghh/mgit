from mgit import config


def test_load_config_defaults(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    conf = config.load_config(tmp_git_repo)
    assert conf["log"]["limit"] == 30


def test_repo_config_overrides_global(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    with open(f"{tmp_git_repo}/.mgit.toml", "w") as f:
        f.write('[log]\nlimit = 50\n')
    conf = config.load_config(tmp_git_repo)
    assert conf["log"]["limit"] == 50


def test_get_dotted_key(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert config.get("log.limit", tmp_git_repo) == 30
    assert config.get("no.such.key", tmp_git_repo) is None


def test_diff_side_by_side_defaults_true(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert config.get_bool("diff.side_by_side", tmp_git_repo) is True


def test_get_bool_parses_strings_written_by_config_set(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for raw, expected in [("false", False), ("No", False), ("0", False), ("off", False), ("true", True), ("yes", True)]:
        config.set_value("diff.side_by_side", raw, cwd=tmp_git_repo)
        assert config.get_bool("diff.side_by_side", tmp_git_repo) is expected, raw
