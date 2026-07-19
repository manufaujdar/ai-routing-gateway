# AI Gateway agent team

This repository uses explicit specialist gears, inspired by gstack's separation of planning,
review, QA, release, and documentation. Roles are project-local Codex skills under
`.agents/skills/`; they are task contracts, not permanently running services.

## Operating model

```text
Team Lead
   |
   +-- Discover: R&D + Planner + Designer (as needed)
   +-- Design:   Planner -> Engineer
   +-- Build:    Builder
   +-- Certify:  Reviewer || QA || AI Safety & Evaluation
   +-- Repair:   Builder -> independent re-verification
   +-- Explain:  Documentation + Marketer (only for a launch)
   +-- Deliver:  Release
```

Parallelize independent read-heavy work. Keep one accountable owner for every artifact. Builder is
the only default owner of production-code changes. Reviewer, QA, and AI Safety & Evaluation are
report-only and cannot approve their own implementation. Release never fixes code or waives a gate.

## Team directory

| Gear | Skill | Authority | Required result |
| --- | --- | --- | --- |
| Team Lead | `$coordinate-ai-gateway-team` | Coordinate and consolidate | Current handoff, selected gears, gate state |
| Planner | `$plan-ai-gateway-work` | Product scope only | Outcome, scope/non-goals, acceptance criteria |
| R&D | `$research-ai-routing` | Research and disposable experiments | Evidence, options, uncertainty, recommendation |
| Designer | `$design-ai-gateway-experience` | Report/specification only | API/CLI/user journey and accessibility contract |
| Engineer | `$engineer-ai-gateway-systems` | Technical design only | Boundaries, data flow, failures, test matrix |
| Builder | `$build-ai-gateway-feature` | Production implementation | Scoped code, focused tests, deviation log |
| Reviewer | `$review-ai-gateway-changes` | Independent report only | Severity-ranked diff findings with evidence |
| QA | `$test-ai-gateway-quality` | Independent behavioral report only | Reproduction evidence and acceptance verdict |
| AI Safety & Evaluation | `$evaluate-ai-gateway-safety` | Independent policy/eval report only | Routing, council, safety, privacy, cost verdict |
| Documentation | `$document-ai-gateway` | Documentation changes | Docs reconciled to verified behavior |
| Marketer | `$market-ai-gateway` | Draft artifacts only | Evidence-grounded positioning; no publishing |
| Release | `$release-ai-gateway` | Authorized delivery mechanics | Validation evidence, rollout/rollback readiness |

The machine-readable registry is `.ai/team.json`. Run `python scripts/validate_agent_team.py` after
editing any team skill or registry entry.

## Handoff contract

Use `.ai/HANDOFF.md` only while work is active. Record:

1. objective and accountable owner;
2. base revision and current status;
3. in-scope work and explicit non-goals;
4. affected routes, models, tools, interfaces, and policies;
5. decisions, assumptions, and plan deviations;
6. outputs and files changed;
7. checks run and evidence;
8. unresolved risks or blockers;
9. gate result and exact next owner/action.

Clear stale task detail after completion. Put durable approved routing/interface decisions in
`.ai/MEMORY.md`, not in handoff history.

## When to create subagents

The Team Lead may create specialist subagents when the user requests team/parallel work or an
applicable skill is explicitly invoked. Give each subagent one bounded deliverable and minimal
necessary context. Prefer parallel R&D, exploration, review, QA, and evaluation. Avoid concurrent
production edits; assign them to one Builder unless file ownership is disjoint and explicit.

Every subagent returns a concise artifact summary, evidence, risks, and recommended next owner. The
Team Lead consolidates duplicate findings and remains accountable for the final response.

## Council policy

Use deterministic rules and a single accountable role by default. Never call an LLM council for
routine implementation, formatting, tests, documentation reconciliation, or release mechanics.

Council deliberation is eligible only when all are true:

- the decision is consequential, ambiguous, or hard to reverse;
- multiple feasible approaches have materially different trade-offs;
- independent perspectives are likely to change the outcome;
- total cost and latency fit the request policy;
- the result will advise, not replace, the accountable role.

Good candidates are product scope, architecture choices, R&D conclusions, design direction, and
unresolved high-risk review disputes. Peer agreement is not proof; deterministic tests, evidence,
and safety policy remain authoritative.

## Universal gates

- Read `START_HERE.txt`, `AGENTS.md`, `.ai/CONTEXT.md`, `.ai/MEMORY.md`, `README.md`, relevant source,
  and tests before acting.
- Keep evaluation, route selection, council planning, handler registration, and execution separate.
- Preserve deterministic offline behavior and observable route/model/tool/confidence/reasons.
- Keep provider calls behind adapters and secrets/private prompts out of files and traces.
- Validate focused behavior first, then run `pytest` and `ruff check .` before release readiness.
- Stop when a required gate fails; return the work to its accountable owner instead of waiving it.
