from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_gateway import ROLE_DEFINITIONS, scaffold_team, validate_scaffold


def test_scaffold_creates_complete_portable_team(tmp_path: Path) -> None:
    project = tmp_path / "project with spaces"
    paths = scaffold_team(project)

    assert len(paths) == len(ROLE_DEFINITIONS) * 2 + 2
    registry = json.loads((project / ".ai" / "team.json").read_text(encoding="utf-8"))
    assert registry["schema_version"] == 1
    assert len(registry["roles"]) == 12
    assert len({item["id"] for item in registry["roles"]}) == 12
    for definition in ROLE_DEFINITIONS:
        skill = project / ".agents" / "skills" / definition.skill_name / "SKILL.md"
        assert skill.read_text(encoding="utf-8").startswith("---\nname:")
        yaml = (skill.parent / "agents" / "openai.yaml").read_text(encoding="utf-8")
        short = next(line for line in yaml.splitlines() if "short_description:" in line)
        assert 25 <= len(short.split('"')[1]) <= 64
    assert validate_scaffold(project) == ()


def test_scaffold_collision_causes_no_partial_writes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    conflict = project / ".ai" / "TEAM.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        scaffold_team(project)

    assert conflict.read_text(encoding="utf-8") == "keep me"
    assert not (project / ".ai" / "team.json").exists()
    assert not (project / ".agents").exists()


def test_scaffold_force_only_replaces_known_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    scaffold_team(project)
    unrelated = project / "notes.txt"
    unrelated.write_text("untouched", encoding="utf-8")

    scaffold_team(project, force=True)

    assert unrelated.read_text(encoding="utf-8") == "untouched"


def test_scaffold_rejects_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / ".ai").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="inside the target"):
        scaffold_team(project)
    assert list(outside.iterdir()) == []


def test_scaffold_preflights_blocking_parent_before_any_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".agents").write_text("blocking file", encoding="utf-8")

    with pytest.raises(ValueError, match="parent is not a directory"):
        scaffold_team(project)

    assert not (project / ".ai").exists()
    assert (project / ".agents").read_text(encoding="utf-8") == "blocking file"


def test_scaffold_force_rejects_directory_leaf_before_overwriting(tmp_path: Path) -> None:
    project = tmp_path / "project"
    scaffold_team(project)
    team_readme = project / ".ai" / "TEAM.md"
    team_readme.write_text("sentinel", encoding="utf-8")
    skill = project / ".agents" / "skills" / ROLE_DEFINITIONS[0].skill_name / "SKILL.md"
    skill.unlink()
    skill.mkdir()

    with pytest.raises(ValueError, match="must be regular files"):
        scaffold_team(project, force=True)

    assert team_readme.read_text(encoding="utf-8") == "sentinel"


@pytest.mark.parametrize("tamper", ["registry", "frontmatter", "unsafe"])
def test_validator_rejects_tampered_contracts(tmp_path: Path, tamper: str) -> None:
    project = tmp_path / tamper
    scaffold_team(project)
    skill = project / ".agents" / "skills" / ROLE_DEFINITIONS[0].skill_name / "SKILL.md"
    if tamper == "registry":
        registry_path = project / ".ai" / "team.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["roles"][0]["skill"] = "missing-skill"
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
    elif tamper == "frontmatter":
        skill.write_text(skill.read_text(encoding="utf-8").replace("\n---\n", "\n", 1), encoding="utf-8")
    else:
        skill.write_text(skill.read_text(encoding="utf-8") + "\nrm -rf /\n", encoding="utf-8")

    assert validate_scaffold(project)


def test_validator_rejects_non_object_registry(tmp_path: Path) -> None:
    project = tmp_path / "project"
    scaffold_team(project)
    (project / ".ai" / "team.json").write_text("[]", encoding="utf-8")

    assert validate_scaffold(project) == (".ai/team.json: root must be a JSON object",)
