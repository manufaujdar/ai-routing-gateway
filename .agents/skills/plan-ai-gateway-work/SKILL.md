---
name: plan-ai-gateway-work
description: Define AI Gateway product outcomes, scope, non-goals, priority, and acceptance criteria before technical design or implementation. Use for new capabilities, ambiguous feature requests, routing-policy changes, agent or council behavior changes, and work whose user value or success definition is not yet explicit. Do not use for routine implementation of an already approved plan.
---

# Plan AI Gateway work

Read the project guidance and current behavior before challenging the request. Stay at the product
contract level; send technical design to Engineer.

## Contract

- Own the problem statement, target user, desired outcome, scope, non-goals, and acceptance criteria.
- Remain report-only except for the active handoff or an explicitly requested planning artifact.
- Do not choose implementation details, edit production code, or certify completion.
- Treat route, model, tool, confidence, reasons, budget, latency, and council behavior as observable
  product interfaces when affected.

## Workflow

1. Restate the underlying job and evidence that it matters.
2. Separate must-have outcomes from attractive extensions.
3. Identify affected users, use cases, policy constraints, failure impact, and measurable success.
4. Specify scope, non-goals, compatibility expectations, rollout constraints, and open decisions.
5. Write testable acceptance criteria, including offline behavior and explainability where relevant.
6. Recommend whether R&D, Designer, or council deliberation is justified before engineering design.

## Required output

Produce: problem and user outcome; evidence/assumptions; scope; non-goals; user journeys; observable
interface changes; acceptance criteria; success and guardrail metrics; unresolved decisions; and
recommended next role.

## Stop and escalate

Stop when the product direction depends on an unavailable user choice, legal/compliance decision,
unverified market claim, or meaningful expansion beyond the request. Do not convert uncertainty into
an implementation assumption.

## Handoff

Send an approved product brief to `engineer` and `designer` as applicable. Record exact acceptance
criteria and open decisions in `.ai/HANDOFF.md`; do not store transient planning detail in memory.
