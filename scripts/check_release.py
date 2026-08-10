from __future__ import annotations

import argparse
import re
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_release(tag: str, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    version = runpy.run_path(root / "src" / "ai_gateway" / "_version.py")["__version__"]
    expected_tag = f"v{version}"
    if tag != expected_tag:
        errors.append(f"release tag must be {expected_tag}, received {tag}")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.MULTILINE):
        errors.append(f"CHANGELOG.md lacks a dated [{version}] release section")
    return errors


def validate_main_ancestry(commit: str, main_ref: str, root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, main_ref],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return []
    if result.returncode == 1:
        return [f"release commit {commit} is not contained in {main_ref}"]
    detail = result.stderr.strip() or "git merge-base could not verify ancestry"
    return [f"release ancestry verification failed: {detail}"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify version and changelog release metadata")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--main-ref")
    args = parser.parse_args()
    errors = validate_release(args.tag)
    if bool(args.commit) != bool(args.main_ref):
        errors.append("--commit and --main-ref must be provided together")
    elif args.commit and args.main_ref:
        errors.extend(validate_main_ancestry(args.commit, args.main_ref))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Release metadata is valid for {args.tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
