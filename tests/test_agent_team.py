import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_agent_team.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_team", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_project_agent_team_is_valid() -> None:
    assert VALIDATOR.validate() == []


def test_frontmatter_parser_rejects_unanchored_content(tmp_path: Path) -> None:
    path = tmp_path / "SKILL.md"
    path.write_text("prefix\n---\nname: invalid\ndescription: invalid\n---\nbody", encoding="utf-8")

    try:
        VALIDATOR.parse_frontmatter(path)
    except ValueError as error:
        assert "anchored" in str(error)
    else:
        raise AssertionError("unanchored frontmatter was accepted")


def test_frontmatter_parser_reads_required_metadata(tmp_path: Path) -> None:
    path = tmp_path / "SKILL.md"
    path.write_text(
        "---\nname: example-skill\ndescription: Example role.\n---\n\n# Example\n",
        encoding="utf-8",
    )

    metadata, body = VALIDATOR.parse_frontmatter(path)
    assert metadata == {"name": "example-skill", "description": "Example role."}
    assert body.startswith("\n# Example")
