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
