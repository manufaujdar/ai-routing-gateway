from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

from ai_gateway import __version__

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_release.py"
SPEC = importlib.util.spec_from_file_location("check_release", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECK_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_RELEASE)


def test_current_release_metadata_is_consistent() -> None:
    assert CHECK_RELEASE.validate_release("v0.1.0") == []
    assert __version__ == "0.1.0"


def test_release_tag_must_match_package_version() -> None:
    errors = CHECK_RELEASE.validate_release("v9.9.9")
    assert errors == ["release tag must be v0.1.0, received v9.9.9"]


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_release_commit_must_be_contained_in_main(tmp_path: Path) -> None:
    _git(tmp_path, "init", "--initial-branch=main")
    _git(tmp_path, "config", "user.name", "Release Test")
    _git(tmp_path, "config", "user.email", "release-test@example.invalid")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("main\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "main")
    main_commit = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "switch", "-c", "unreviewed")
    tracked.write_text("unreviewed\n", encoding="utf-8")
    _git(tmp_path, "commit", "-am", "unreviewed")
    unreviewed_commit = _git(tmp_path, "rev-parse", "HEAD")

    assert CHECK_RELEASE.validate_main_ancestry(main_commit, "main", tmp_path) == []
    assert CHECK_RELEASE.validate_main_ancestry(unreviewed_commit, "main", tmp_path) == [
        f"release commit {unreviewed_commit} is not contained in main"
    ]
