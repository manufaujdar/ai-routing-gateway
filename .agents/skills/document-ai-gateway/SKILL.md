---
name: document-ai-gateway
description: Reconcile AI Gateway README, architecture, API/CLI examples, strategy documents, and agent-team contracts with verified implemented behavior. Use after implementation and independent verification, for explicit documentation requests, or when review finds factual documentation drift. Do not invent behavior, silently change interfaces, or publish marketing claims.
---

# Document the AI Gateway

Use code, tests, and verified gate evidence as sources of truth. Preserve human-written positioning and
decision history unless the user explicitly requests narrative changes.

## Contract

- Own factual documentation updates, examples, cross-links, architecture diagrams, and discoverability.
- Change documentation only; return behavior/interface inconsistencies to Planner, Engineer, or Builder.
- Distinguish illustrative estimates from live provider facts.
- Do not store credentials, private prompts, unredacted traces, or stale active-task detail.

## Workflow

1. Read all entry docs, changed interfaces, relevant tests, and verification evidence.
2. Map new, changed, deprecated, and unchanged behavior.
3. Update README usage, architecture boundaries, API/CLI examples, team/skill docs, and strategy docs
   only where evidence requires it.
4. Verify commands and examples locally when safe.
5. Check cross-document terminology, file paths, model/route fields, versions, and discoverability.
6. Keep `.ai/HANDOFF.md` transient and `.ai/MEMORY.md` limited to explicitly approved durable decisions.

## Required output

Report each document changed and the verified behavior it now reflects, commands/examples checked,
remaining documentation gaps, narrative decisions left untouched, and next owner.

## Stop and escalate

Stop for ambiguous product positioning, security-policy narrative, removing historical decisions,
large unsupported rewrites, or contradictions between code and approved interface intent.

## Handoff

Send technically verified docs to `release`. Send launch-facing factual inputs to `marketer`; Marketer
must not redefine canonical technical behavior.
