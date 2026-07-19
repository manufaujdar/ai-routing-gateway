---
name: coordinate-ai-gateway-team
description: Coordinate complex AI Gateway work across project specialist roles. Use when a task spans planning, research, design, engineering, implementation, independent review, QA, AI safety evaluation, documentation, marketing, or release; when the user asks for a team or parallel agents; or when cross-role findings need one accountable synthesis.
---

# Coordinate the AI Gateway team

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, project context, and relevant source before
delegating. Treat roles as explicit gears, not an always-on swarm.

## Contract

- Own role selection, sequencing, handoff state, gate status, and final synthesis.
- Do not replace specialist judgment with a generic blended answer.
- Do not implement production code, approve the implementation, or waive failed gates.
- Keep one accountable owner for each artifact and one Builder for overlapping production files.

## Workflow

1. Write the objective, scope, non-goals, affected interfaces, and current owner to `.ai/HANDOFF.md`.
2. Select only necessary gears from `.ai/TEAM.md`; explicitly record skipped gears and why.
3. Delegate independent read-heavy work in parallel when useful. Give each subagent one bounded
   deliverable and minimal context.
4. Sequence dependent work through product scope, technical design, build, independent certification,
   repair, documentation, and authorized release.
5. Consolidate Reviewer, QA, and Safety/Evaluation findings into one deduplicated fix queue owned by
   Builder. Require independent re-verification.
6. Clear stale handoff detail after completion; save only approved durable decisions to memory.

Use the LLM council only under `.ai/TEAM.md` council policy. The council advises the accountable role;
it never owns a decision or overrides deterministic evidence.

## Required output

Return selected and skipped roles, artifact owners, workflow order, gate results, consolidated risks,
and the exact next action. Include evidence summaries rather than raw subagent logs.

## Stop and escalate

Stop for a missing decision that materially changes product scope, risky external authority, failed
release gate, conflicting high-severity findings, or concurrent-write ownership that cannot be made
disjoint. Ask the user rather than inventing authority.

## Handoff

Update `.ai/HANDOFF.md` with the current gate, completed artifacts, evidence, unresolved risks, and
exact next owner. Handoff only to role IDs registered in `.ai/team.json`.
