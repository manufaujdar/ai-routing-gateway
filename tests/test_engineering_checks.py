"""Regression coverage for the offline documentation boundary."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "engineering_checks", Path(__file__).resolve().parents[1] / "scripts/engineering_checks.py"
)
assert SPEC is not None and SPEC.loader is not None
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


def test_offline_links_reject_missing_file_and_accept_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    document = tmp_path / "README.md"
    (tmp_path / "existing.md").write_text("# Present\n")
    document.write_text(
        "[present](existing.md#heading)\n[broken](missing.md)\n[public](https://example.com/)\n"
    )
    assert checks.document_errors(document) == ["README.md: missing relative link missing.md"]


def test_code_examples_and_external_workspace_links_are_not_followed(tmp_path, monkeypatch):
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    document = tmp_path / "README.md"
    document.write_text(
        "```md\n[example](not-a-real-file.md)\n```\n[workspace](../private-workspace.md)\n"
    )
    assert checks.document_errors(document) == []


def test_dirty_tree_is_not_certified_as_outgoing_commit(monkeypatch):
    monkeypatch.setattr(checks, "resolve", lambda ref: "a" * 40)
    monkeypatch.setattr(checks, "git", lambda *args: " M README.md")
    with pytest.raises(ValueError, match="working tree must be clean"):
        checks.run("a" * 40)


def test_resolved_ref_must_be_immutable_sha(monkeypatch):
    monkeypatch.setattr(checks, "git", lambda *args: "invalid-ref; command")
    with pytest.raises(ValueError, match="immutable commit SHA"):
        checks.resolve("main")
