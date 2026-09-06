from mgit import config


def test_set_value_writes_and_reads_back(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config.set_value("log.limit", "100", cwd=tmp_git_repo)
    assert config.get("log.limit", tmp_git_repo) == "100"


def test_set_value_global(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config.set_value("flow.main_branch", "trunk", global_=True)
    assert config.get("flow.main_branch") == "trunk"
