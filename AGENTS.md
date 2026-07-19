# AI Gateway agent guide

Read `START_HERE.txt`, `.ai/CONTEXT.md`, `.ai/MEMORY.md`, `README.md`, the relevant modules under `src/ai_gateway/`, and related tests before editing.

- Keep evaluation, route selection, handler registration, and execution separated.
- Preserve deterministic offline behavior as the default. Provider calls belong behind adapters and must not be required by core tests.
- Treat route, model, tool, confidence, and reasons as observable output; do not silently change routing semantics.
- Validate tool arguments and keep high-risk requests from being routed to unrestricted execution.
- Avoid adding a model call where explicit rules or a small deterministic classifier are sufficient.
- Never commit provider keys, prompt contents containing private data, or unredacted production traces.

Validate Python changes with `pytest` and `ruff check .`; run focused tests before the full suite.

Project specialist roles live under `.agents/skills/`. For coordinated or multi-role work, read
`.ai/TEAM.md`, use `.ai/HANDOFF.md` as the single active-task contract, and validate role changes
with `python scripts/validate_agent_team.py`. Keep one accountable owner per artifact; Reviewer, QA,
and AI Safety & Evaluation cannot certify their own implementation.

Use `.ai/HANDOFF.md` only for active-task continuity. Add durable memory only for explicit approved routing or interface decisions.

## Startup team

Read `.ai/TEAM.md` before multi-role or idea-to-release work. Use its explicit
gears and keep the task contract in `.ai/HANDOFF.md`; this guide's routing,
safety, and validation rules remain authoritative.
