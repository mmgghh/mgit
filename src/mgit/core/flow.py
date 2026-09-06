from __future__ import annotations

from ..git.runner import run


def _get(key: str, default: str, cwd: str | None = None) -> str:
    return run(["config", "--get", key], cwd=cwd, check=False) or default


def init_flow(main_branch: str = "main", develop_branch: str = "develop", cwd: str | None = None) -> None:
    existing = run(["branch", "--format=%(refname:short)"], cwd=cwd).splitlines()
    if develop_branch not in existing:
        run(["branch", develop_branch, main_branch], cwd=cwd)
    run(["config", "gitflow.branch.main", main_branch], cwd=cwd)
    run(["config", "gitflow.branch.develop", develop_branch], cwd=cwd)
    run(["config", "gitflow.prefix.feature", "feature/"], cwd=cwd)
    run(["config", "gitflow.prefix.release", "release/"], cwd=cwd)
    run(["config", "gitflow.prefix.hotfix", "hotfix/"], cwd=cwd)


def feature_start(name: str, cwd: str | None = None) -> str:
    develop = _get("gitflow.branch.develop", "develop", cwd)
    prefix = _get("gitflow.prefix.feature", "feature/", cwd)
    return run(["checkout", "-b", f"{prefix}{name}", develop], cwd=cwd)


def feature_finish(name: str, cwd: str | None = None) -> str:
    develop = _get("gitflow.branch.develop", "develop", cwd)
    prefix = _get("gitflow.prefix.feature", "feature/", cwd)
    branch = f"{prefix}{name}"
    run(["checkout", develop], cwd=cwd)
    out = run(["merge", "--no-ff", branch], cwd=cwd)
    run(["branch", "-d", branch], cwd=cwd)
    return out


def feature_list(cwd: str | None = None) -> list[str]:
    prefix = _get("gitflow.prefix.feature", "feature/", cwd)
    out = run(["branch", "--format=%(refname:short)"], cwd=cwd)
    return [b for b in out.splitlines() if b.startswith(prefix)]


def release_start(version: str, cwd: str | None = None) -> str:
    develop = _get("gitflow.branch.develop", "develop", cwd)
    prefix = _get("gitflow.prefix.release", "release/", cwd)
    return run(["checkout", "-b", f"{prefix}{version}", develop], cwd=cwd)


def release_finish(version: str, cwd: str | None = None) -> str:
    main_branch = _get("gitflow.branch.main", "main", cwd)
    develop = _get("gitflow.branch.develop", "develop", cwd)
    prefix = _get("gitflow.prefix.release", "release/", cwd)
    branch = f"{prefix}{version}"
    run(["checkout", main_branch], cwd=cwd)
    run(["merge", "--no-ff", branch], cwd=cwd)
    run(["tag", "-a", version, "-m", version], cwd=cwd)
    run(["checkout", develop], cwd=cwd)
    out = run(["merge", "--no-ff", branch], cwd=cwd)
    run(["branch", "-d", branch], cwd=cwd)
    return out


def release_list(cwd: str | None = None) -> list[str]:
    prefix = _get("gitflow.prefix.release", "release/", cwd)
    out = run(["branch", "--format=%(refname:short)"], cwd=cwd)
    return [b for b in out.splitlines() if b.startswith(prefix)]


def hotfix_start(version: str, cwd: str | None = None) -> str:
    main_branch = _get("gitflow.branch.main", "main", cwd)
    prefix = _get("gitflow.prefix.hotfix", "hotfix/", cwd)
    return run(["checkout", "-b", f"{prefix}{version}", main_branch], cwd=cwd)


def hotfix_finish(version: str, cwd: str | None = None) -> str:
    main_branch = _get("gitflow.branch.main", "main", cwd)
    develop = _get("gitflow.branch.develop", "develop", cwd)
    prefix = _get("gitflow.prefix.hotfix", "hotfix/", cwd)
    branch = f"{prefix}{version}"
    run(["checkout", main_branch], cwd=cwd)
    run(["merge", "--no-ff", branch], cwd=cwd)
    run(["tag", "-a", version, "-m", version], cwd=cwd)
    run(["checkout", develop], cwd=cwd)
    out = run(["merge", "--no-ff", branch], cwd=cwd)
    run(["branch", "-d", branch], cwd=cwd)
    return out


def hotfix_list(cwd: str | None = None) -> list[str]:
    prefix = _get("gitflow.prefix.hotfix", "hotfix/", cwd)
    out = run(["branch", "--format=%(refname:short)"], cwd=cwd)
    return [b for b in out.splitlines() if b.startswith(prefix)]
