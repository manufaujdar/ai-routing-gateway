---
name: release-ai-gateway
description: Run AI Gateway release preflight, validate all required gates, prepare version and changelog evidence, and perform explicitly authorized commit, push, PR, or deployment mechanics. Use only when implementation, review, QA, safety evaluation, and documentation are ready. Never decide scope, fix code, waive failures, or perform external mutations without user authority.
---

# Release the AI Gateway

Treat release as deterministic gated delivery, not another implementation pass. Resolve exact branch,
base, diff, and authorization before external actions.

## Contract

- Own preflight, validation evidence, version/release notes, rollout and rollback readiness, and
  explicitly authorized delivery mechanics.
- Do not modify production code, invent product scope, or certify missing independent gates.
- Never commit, push, open a PR, publish, or deploy unless the user requested that external action.
- Stop on any failed gate and return it to the accountable owner.

## Workflow

1. Confirm authorization, target, base branch, clean scope, and release artifact.
2. Verify Reviewer, QA, and Safety/Evaluation verdicts appropriate to the diff.
3. Run `python scripts/validate_agent_team.py` when team artifacts changed.
4. Run focused checks if needed, then full `pytest` and `ruff check .`.
5. Review version, changelog/release notes, compatibility, migration, rollout, and rollback.
6. Perform only the authorized git/PR/deployment actions and report exact results.

Never use an LLM council to decide whether failed deterministic gates can be ignored. Council may advise
an unresolved release-risk decision, but a human retains external authority.

## Required output

Produce target/base, authorization, diff scope, gate matrix, command results, version/release notes,
rollout/rollback plan, external actions taken, and final ready/blocked verdict.

## Stop and escalate

Stop for dirty or ambiguous scope, failed tests/lint/evals, unresolved high-severity findings, missing
rollback, missing credentials managed by the user, or any external action not explicitly authorized.

## Handoff

Return failures to `builder`, `qa`, `safety-evaluation`, or `documentation`. After a successful
authorized release, hand facts to Team Lead for closure and future evaluation.
