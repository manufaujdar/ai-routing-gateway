from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".agents" / "skills"
REGISTRY = ROOT / ".ai" / "team.json"
REQUIRED_ROLES = {
    "team-lead",
    "planner",
    "research",
    "designer",
    "engineer",
    "builder",
    "reviewer",
    "qa",
    "safety-evaluation",
    "documentation",
    "marketer",
    "release",
}
REQUIRED_HEADINGS = {
    "## Contract",
    "## Workflow",
    "## Required output",
    "## Stop and escalate",
    "## Handoff",
}
UNSAFE_PATTERNS = ("rm -rf", "git reset --hard", "git checkout --", "OPENROUTER_API_KEY=")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise ValueError("missing anchored YAML frontmatter")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, match.group(2)


def validate_openai_yaml(skill_dir: Path, skill_name: str) -> list[str]:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.is_file():
        return ["agents/openai.yaml is missing"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for field in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{field}:\s*\"[^\"]+\"\s*$", text, re.M):
            errors.append(f"agents/openai.yaml lacks quoted {field}")
    short = re.search(r'^\s*short_description:\s*"([^"]+)"', text, re.M)
    if short and not 25 <= len(short.group(1)) <= 64:
        errors.append("short_description must contain 25-64 characters")
    prompt = re.search(r'^\s*default_prompt:\s*"([^"]+)"', text, re.M)
    if prompt and f"${skill_name}" not in prompt.group(1):
        errors.append("default_prompt must explicitly invoke the skill")
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f".ai/team.json: {error}"]

    roles = registry.get("roles", [])
    role_ids = [role.get("id") for role in roles]
    skills = [role.get("skill") for role in roles]
    if set(role_ids) != REQUIRED_ROLES:
        errors.append(".ai/team.json roles do not match the required team roster")
    if len(role_ids) != len(set(role_ids)):
        errors.append(".ai/team.json contains duplicate role ids")
    if len(skills) != len(set(skills)):
        errors.append(".ai/team.json contains duplicate skill assignments")
    known_roles = set(role_ids)
    for role in roles:
        for target in role.get("next", []):
            if target not in known_roles:
                errors.append(f"role {role.get('id')} has unknown handoff target {target}")

    discovered = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    if discovered != set(skills):
        errors.append("skill folders and .ai/team.json entries are not one-to-one")

    for skill_name in sorted(discovered):
        skill_dir = SKILLS_DIR / skill_name
        path = skill_dir / "SKILL.md"
        if not path.is_file():
            errors.append(f"{skill_name}: SKILL.md is missing")
            continue
        try:
            metadata, body = parse_frontmatter(path)
        except ValueError as error:
            errors.append(f"{skill_name}: {error}")
            continue
        if set(metadata) != {"name", "description"}:
            errors.append(f"{skill_name}: frontmatter must contain only name and description")
        if metadata.get("name") != skill_name:
            errors.append(f"{skill_name}: folder and frontmatter names differ")
        if not re.fullmatch(r"[a-z0-9-]{1,64}", skill_name):
            errors.append(f"{skill_name}: name must be lowercase hyphen-case and <=64 chars")
        description = metadata.get("description", "")
        if not description or len(description) > 1024 or "<" in description or ">" in description:
            errors.append(f"{skill_name}: description is empty or invalid")
        if "TODO" in body or "[TODO" in body:
            errors.append(f"{skill_name}: unresolved template placeholder")
        if len(body.splitlines()) > 500:
            errors.append(f"{skill_name}: SKILL.md exceeds 500 body lines")
        missing = sorted(REQUIRED_HEADINGS - set(re.findall(r"^## .+$", body, re.M)))
        if missing:
            errors.append(f"{skill_name}: missing headings {', '.join(missing)}")
        for pattern in UNSAFE_PATTERNS:
            if pattern in body:
                errors.append(f"{skill_name}: forbidden unsafe pattern {pattern!r}")
        errors.extend(f"{skill_name}: {error}" for error in validate_openai_yaml(skill_dir, skill_name))
    return sorted(errors)


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated {len(REQUIRED_ROLES)} AI Gateway team skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
