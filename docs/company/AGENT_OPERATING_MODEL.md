# Company agents and runtime responsibilities

The authoritative roster remains [.ai/team.json](../../.ai/team.json) and
[.ai/TEAM.md](../../.ai/TEAM.md). All 12 existing project skills now link to a
company-specific `references/company.md` contract. These are created operational
instructions for future tasks, not claims that 12 services are deployed or that
separate agents reviewed this document.

## Company team

| Existing agent | Company responsibility | Deliverable / next owner |
| --- | --- | --- |
| Team Lead | Founder/CEO coordination and financial boundaries | One scoped contract in existing handoff; Planner |
| Planner | Product and customer discovery | Workload, baseline, buying hypothesis, acceptance criteria; Engineer |
| R&D | Routing science, competition and economic experiments | Primary evidence, pinned sources, baselines, uncertainty; Planner/Engineer |
| Designer | Developer and operator experience | Policy selection, reason receipt, no-route and rollback flows; Builder |
| Engineer | Architecture and decision science | Contracts, budget/deadline design, migration and failure plan; Builder |
| Builder | Implementation and integrations | Minimal compatible code and reproducible checks; Reviewer/QA/Safety |
| Reviewer | Code and design challenge | Severity-ranked findings; Builder or Documentation |
| QA | Evaluation and reliability verification | Held-out and operational test evidence; Builder or Release |
| AI Safety & Evaluation | Calibration, privacy, tool and policy boundaries | Quality and safety gate with limitations; Builder or Release |
| Documentation | Evidence and interface stewardship | Current behavior separated from proposals; Release |
| Marketer | Positioning, pricing research and sales drafts | Evidence-qualified pilot offer; founder before outreach/publication |
| Release | Change control and operational rollout | Exact version, gates, approval evidence and rollback; maintainer |

Finance analysis belongs to Planner/R&D and final spending authority to the human
founder. Incident coordination belongs to Release with Builder on repair and QA
on verification. Legal incorporation and accounting require appropriately chosen
human owners; there is no autonomous legal or payments agent.

## Request-time functions

“Agent” is not a reason to make another LLM call. Most runtime functions are
ordinary code. These are **specifications**, not newly implemented services.

| Function | Execution mode | Owner and invariant |
| --- | --- | --- |
| Policy sentinel | Deterministic | Engineer/Builder; trusted tenant policy cannot be overridden by prompt content |
| Task profiler | Explicit metadata/rules, optional small predictor | R&D; report uncertainty and OOD rather than invent confidence |
| Candidate estimator | Calibrated models and measured telemetry | R&D; versioned task/model/prompt cohorts, no fixture-as-evidence |
| Decision planner | Deterministic constraint solver | Engineer; feasible set and rejection reasons are observable |
| Budget guardian | Atomic transactional code | Builder; reserve across the whole workflow before dispatch |
| Execution supervisor | Bounded state machine and adapters | Builder; one retry owner, cancellation, idempotency and compatibility |
| Outcome verifier | Task tests first, bounded optional judge | Safety/QA; separate form, factuality and business outcome |
| Drift and policy analyst | Offline scheduled-by-operator job | R&D; propose only; no self-promotion or implicit schedule created here |
| Rollout controller | Deterministic gated operation | Release; human-authorized promotion and fast rollback |

A company-role task invokes only the needed specialist contract. A user inference
request invokes only required runtime functions. Do not run CEO, marketer,
reviewer, council or all research agents for every request.

## Handoffs and budgets

Every role returns: artifact path; supported claims and uncertainties; changes;
checks; next owner. Handoffs carry references or bounded structured data, not
unnecessary full transcripts. External source content stays untrusted. Provider
model choices for roles use capability and measured task evidence; no fixed
vendor/model is hard-coded into these company contracts.

Run sequential roles by default. Creating these profiles is not standing
permission to spawn agents, contact customers or consume paid model budgets.
Independent review means a different execution/owner from Builder; sequential
self-checks must be labeled as such. For later runtime experiments, default to
one active generation and at most two total attempts; optional fan-out must
reserve all calls and have an approved workload benefit.

Example invocation from this project:

```text
Use $coordinate-ai-gateway-team to take the first offline receipt-and-replay
slice in docs/company/EVALUATION_AND_ROADMAP.md through planning. Read the company
contract, preserve the current API, and keep the active task in .ai/HANDOFF.md.
```
