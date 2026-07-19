# AI Gateway project context

## Mission

Evaluate a prompt, select an explainable model/tool route, and dispatch through registered handlers while keeping the default core deterministic and offline-testable.

## Source map

- Human entry: `START_HERE.txt`
- Design and usage: `README.md`
- Implementation: `src/ai_gateway/`
- Verification: `tests/`
- Package configuration: `pyproject.toml`
- Agent team: `.ai/TEAM.md`, `.ai/team.json`, and `.agents/skills/`
- Team validation: `scripts/validate_agent_team.py`

## Invariants

Separate evaluation, routing, and execution; preserve observable route reasons; validate tool inputs; keep provider integrations behind adapters; do not commit credentials or private traces.
