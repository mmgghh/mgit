from pathlib import Path

from mgit import config


def test_set_value_writes_and_reads_back(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config.set_value("log.limit", "100", cwd=tmp_git_repo)
    assert config.get("log.limit", tmp_git_repo) == "100"


def test_set_value_global(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config.set_value("flow.main_branch", "trunk", global_=True)
    assert config.get("flow.main_branch") == "trunk"


def test_set_value_escapes_backslashes(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    path_with_backslash = "C:\\Users\\test\\repo"
    config.set_value("custom.path", path_with_backslash, cwd=tmp_git_repo)
    assert config.get("custom.path", tmp_git_repo) == path_with_backslash


def test_set_value_writes_to_distinct_files(tmp_git_repo, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config.set_value("log.limit", "50", cwd=tmp_git_repo)
    repo_file = Path(tmp_git_repo, ".mgit.toml")
    global_file = tmp_path / "home" / ".config" / "mgit" / "config.toml"
    assert repo_file.exists()
    assert "50" in repo_file.read_text()
    assert not global_file.exists()

    config.set_value("log.limit", "75", global_=True)
    assert "75" in global_file.read_text()
    assert "50" in repo_file.read_text()
    assert "75" not in repo_file.read_text()
