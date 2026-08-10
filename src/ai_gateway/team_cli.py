from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from ._version import __version__
from .team import ROLE_DEFINITIONS, ProjectTask, ProjectTaskKind, TeamPlanner
from .team_scaffold import scaffold_team, validate_scaffold


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan and scaffold a reusable specialist AI team")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    roles = commands.add_parser("roles", help="List built-in specialist roles")
    roles.add_argument("--json", action="store_true")

    plan = commands.add_parser("plan", help="Create a deterministic team plan")
    plan.add_argument("objective")
    plan.add_argument("--kind", choices=[kind.value for kind in ProjectTaskKind], default="feature")
    plan.add_argument("--research", action="store_true")
    plan.add_argument("--user-facing", action="store_true")
    plan.add_argument("--ai-policy", action="store_true")
    plan.add_argument("--high-stakes", action="store_true")
    plan.add_argument("--ambiguous", action="store_true")
    plan.add_argument("--hard-to-reverse", action="store_true")
    plan.add_argument("--competing-approaches", action="store_true")
    plan.add_argument("--independent-views-useful", action="store_true")
    plan.add_argument("--council-resources-fit", action="store_true")
    plan.add_argument("--no-docs", action="store_true")
    plan.add_argument("--marketing", action="store_true")
    plan.add_argument("--release", action="store_true")
    plan.add_argument("--authorize-external-actions", action="store_true")

    init = commands.add_parser("init", help="Install role contracts into another project")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true", help="Overwrite generated team files")
    validate = commands.add_parser("validate", help="Validate installed role contracts")
    validate.add_argument("path", nargs="?", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "roles":
        payload = [
            {
                "role": item.role.value,
                "name": item.display_name,
                "skill": item.skill_name,
                "purpose": item.purpose,
                "authority": item.mutation_authority,
            }
            for item in ROLE_DEFINITIONS
        ]
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for item in payload:
                print(f"{item['role']}: {item['purpose']}")
        return 0

    if args.command == "plan":
        try:
            task = ProjectTask(
                objective=args.objective,
                kind=ProjectTaskKind(args.kind),
                requires_research=args.research,
                user_facing=args.user_facing,
                affects_ai_policy=args.ai_policy,
                high_stakes=args.high_stakes,
                ambiguous=args.ambiguous,
                hard_to_reverse=args.hard_to_reverse,
                multiple_viable_approaches=args.competing_approaches,
                independent_views_useful=args.independent_views_useful,
                council_resources_fit=args.council_resources_fit,
                documentation_requested=not args.no_docs,
                marketing_requested=args.marketing,
                release_requested=args.release,
                external_actions_authorized=args.authorize_external_actions,
            )
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
        print(json.dumps(TeamPlanner().plan(task).to_dict(), indent=2))
        return 0

    if args.command == "validate":
        errors = validate_scaffold(Path(args.path))
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    try:
        paths = scaffold_team(Path(args.path), force=args.force)
    except (FileExistsError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({"created": [str(path) for path in paths]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
