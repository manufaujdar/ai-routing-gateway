# Reusable specialist-team SDK

The team subsystem is ordinary dependency-free Python. It selects a right-sized project team,
exposes why each role was selected, and executes the resulting workflow through handlers supplied
by the integrating project. It does not host a website and it does not require an LLM.

## Design boundary

```text
ProjectTask -> TeamPlanner -> TeamPlan -> TeamRoleRegistry -> TeamExecutor -> TeamRun
                                  |              |
                                  |              +-- application-owned agent handlers
                                  +-- roles, stages, gates, council advice, reasons
```

Planning, registration, and execution are separate. The existing prompt/model gateway can be used
inside a role handler, but project-team planning does not change prompt routing or council execution.

## Public objects

- `ProjectTask` describes the objective and explicit feature, risk, documentation, marketing, and
  release flags.
- `TeamPlanner` deterministically selects ordered `TeamStep` objects.
- `TeamPlan` exposes selected roles, parallel stages, required gates, council advice, and reasons.
- `TeamRoleRegistry` maps roles to application-owned implementations.
- `TeamExecutor` preflights handlers, executes stages, and stops after a blocked or failed result.
- `RoleResult` and `TeamRun` provide structured, serializable evidence.
- `scaffold_team()` installs `.ai/TEAM.md`, `.ai/team.json`, and 12 starter role skills.

Every `ProjectTask` control flag is type-strict: callers must pass `True` or `False`, not strings,
integers, or `None`. Release dispatch applies a second boundary check and invokes the Release handler
only when `external_actions_authorized is True`; truthiness is not authorization.

## Role selection

The default feature path is Team Lead, Planner, Engineer, Builder, Reviewer and QA, then
Documentation. R&D is added for requested research, Designer for user-facing work, and AI Safety &
Evaluation for routing or AI-policy changes. Marketer and Release are selected only by explicit
flags. Review, QA, documentation, marketing, and research task kinds use smaller focused teams.

Reviewer, QA, and AI Safety & Evaluation are independent certification roles. If any selected role
returns `blocked` or `failed`, the executor records all results from that already-started parallel
stage and does not call downstream documentation, marketing, or release handlers.

## Council recommendation

The planner recommends a council only when all of these deterministic conditions hold:

- the task is high-stakes;
- the choice is ambiguous;
- the decision is hard to reverse;
- multiple viable approaches have material trade-offs;
- independent views are likely to change the recommendation;
- council cost and latency fit the request policy;
- the work is product-feature planning or research.

The recommendation is advisory and observable in `TeamPlan`; it never triggers a provider call.
The accountable role or application composition root can pass an appropriate question to the
gateway's existing `CouncilPlanner`. Tests, policy, and an accountable owner remain authoritative.

## Integrating an agent runtime

Implement the `TeamRoleHandler` protocol:

```python
class MyAgent:
    def run(self, task, step, context):
        return RoleResult(
            role=TeamRole.ENGINEER,
            status=RoleStatus.PASSED,
            summary="Technical design accepted",
            artifacts=("docs/DESIGN.md",),
            reasons=("Boundaries and failure modes are specified",),
        )
```

The handler may call an agent framework, an internal service, a shell-isolated worker, or plain
Python. Keep credentials in the host application's secret management. Do not return private prompt
contents or raw provider traces in summaries and reasons.

Register every role present in `plan.roles` before calling `execute()`. Missing handlers fail during
preflight, before the first handler can cause a side effect. Sequential execution is the default;
set `parallel=True` to run roles marked parallel by the plan with a bounded thread pool.

## Scaffolding safety

`ai-gateway-team init PATH` uses only fixed destinations inside the resolved project directory. It
preflights every generated file and refuses all writes if any destination already exists. Symlink
destinations escaping the target are rejected. `--force` replaces only the known generated files;
unrelated project files are not touched.

Generated skills are intentionally generic. Extend their project-specific instructions after
installation, retain one accountable owner per artifact, and keep independent certification roles
separate from implementation.

## Intentionally deferred

- Framework-specific OpenAI, Anthropic, Codex, or LangGraph role adapters.
- Persistent/resumable workflow state and distributed queues.
- Per-role token/cost/latency metering and automatic model selection within a handler.
- Timeouts, process isolation, sandbox policy, and automatic repair loops.

Those are application or later SDK layers. The first release keeps the core portable, predictable,
offline-testable, and safe to embed.
