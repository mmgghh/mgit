from typer.testing import CliRunner

from mgit.cli.main import app

runner = CliRunner()


def test_branch_list_smoke(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    result = runner.invoke(app, ["branch", "list"])
    assert result.exit_code == 0
    assert "main" in result.stdout


def test_branch_delete_missing_branch_reports_error(tmp_git_repo, monkeypatch):
    monkeypatch.chdir(tmp_git_repo)
    result = runner.invoke(app, ["branch", "delete", "does-not-exist"])
    assert result.exit_code != 0
