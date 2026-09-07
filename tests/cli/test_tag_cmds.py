import subprocess

from typer.testing import CliRunner

from mgit.cli.main import app

runner = CliRunner()


def test_delete_tag_prompts_and_aborts_on_decline(tmp_git_remote, monkeypatch):
    monkeypatch.chdir(tmp_git_remote)
    subprocess.run(["git", "tag", "-a", "v1.0.0", "-m", "v1.0.0"], cwd=tmp_git_remote, check=True)
    subprocess.run(["git", "push", "origin", "v1.0.0"], cwd=tmp_git_remote, check=True, capture_output=True)
    result = runner.invoke(app, ["tag", "delete", "v1.0.0"], input="n\n")
    assert result.exit_code != 0
    tags_after = subprocess.run(
        ["git", "tag"], cwd=tmp_git_remote, capture_output=True, text=True, check=True
    ).stdout
    assert "v1.0.0" in tags_after


def test_delete_tag_yes_skips_prompt(tmp_git_remote, monkeypatch):
    monkeypatch.chdir(tmp_git_remote)
    subprocess.run(["git", "tag", "-a", "v1.0.0", "-m", "v1.0.0"], cwd=tmp_git_remote, check=True)
    subprocess.run(["git", "push", "origin", "v1.0.0"], cwd=tmp_git_remote, check=True, capture_output=True)
    result = runner.invoke(app, ["tag", "delete", "v1.0.0", "--yes"])
    assert result.exit_code == 0
    tags_after = subprocess.run(
        ["git", "tag"], cwd=tmp_git_remote, capture_output=True, text=True, check=True
    ).stdout
    assert "v1.0.0" not in tags_after
