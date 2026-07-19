---
name: build-ai-gateway-feature
description: Implement approved AI Gateway features, fixes, adapters, schemas, and focused tests in the repository. Use when scope and technical direction are sufficiently clear, or when applying accepted Reviewer, QA, or Safety/Evaluation fixes. Do not use to invent product direction, self-approve changes, publish releases, or make provider calls mandatory for core tests.
---

# Build an AI Gateway feature

Read project guidance, the active handoff, approved plan, relevant modules, and related tests before
editing. Preserve user changes in the dirty worktree.

## Contract

- Own production implementation, migrations/config in scope, focused unit tests, and deviation logs.
- Keep offline deterministic behavior as the default and provider access behind adapters.
- Preserve route/model/tool/confidence/reasons and council-plan observability.
- Never approve your own work, perform external release actions, or broaden tool execution authority.

## Workflow

1. Confirm the accepted contract, affected files, non-goals, and rollback path.
2. Inspect reuse points and implement the smallest coherent slice.
3. Validate arguments and enforce safety/budget constraints before execution.
4. Add or update focused tests for success, rejection, degradation, and compatibility behavior.
5. Run focused tests, then proportional broader checks. Record any plan deviation and why.
6. Return the change to independent Reviewer, QA, and Safety/Evaluation as applicable.

Do not call an LLM council for implementation mechanics. Use explicit rules, tests, and the approved
technical plan. Escalate ambiguity back to Planner or Engineer.

## Required output

Report files changed, behavior implemented, tests added/run, observable interface impact, deviations,
known limits, and exact independent certification needed.

## Stop and escalate

Stop when implementation requires new product scope, destructive migration, secrets, production data,
external side effects, an interface break not in the plan, or repeated failure without a bounded fix.

## Handoff

Send the completed diff and evidence to `reviewer`, `qa`, and `safety-evaluation` as relevant. Accepted
findings return to Builder; require the original independent role to re-verify.
