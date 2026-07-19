# Review of `karpathy/llm-council`

Review date: 2026-07-19. Source reviewed at commit `92e1fcc`.

## What the repository demonstrates well

The reference project implements a clear three-stage deliberation protocol:

1. several models answer the original question independently and in parallel;
2. the same models review identity-blind candidate answers and provide rankings;
3. a chairman model receives the answers and reviews and synthesizes a final response.

Its most valuable design choices are independence before collaboration, anonymous review to reduce
brand favoritism, parallel calls within each stage, retention of raw intermediate outputs, and
graceful continuation when one model call fails. The UI also exposes both raw review text and parsed
rankings, which is important because model-generated rankings are not perfectly structured.

Reference: [karpathy/llm-council](https://github.com/karpathy/llm-council), especially its
[council orchestration](https://github.com/karpathy/llm-council/blob/master/backend/council.py) and
[OpenRouter adapter](https://github.com/karpathy/llm-council/blob/master/backend/openrouter.py).

## What should change for a gateway

The repository describes itself as a small experimental application. Several choices are therefore
reasonable for a demo but unsuitable as gateway defaults:

- Every user message runs a full council. Easy questions pay the same multi-call overhead as hard,
  consequential decisions.
- Membership and chairman are hard-coded rather than selected for task capability, policy, price,
  observed quality, provider diversity, or current health.
- There is no request-wide cost or latency check. With `N` members, the flow makes `N` answer calls,
  `N` review calls containing all candidate answers, and one synthesis call.
- Average peer rank is not proof of correctness. Correlated models may confidently agree on the same
  error, and writing style can reveal identity despite label anonymization.
- Partial ranking parsing can give malformed ballots disproportionate influence.
- Candidate answers are embedded in later prompts, creating an indirect prompt-injection boundary.
- Errors are broadly swallowed, usage is not reconciled against estimates, and conversation JSON is
  local demo storage rather than an auditable production event model.

## Implementation in this gateway

The gateway retains the useful protocol while making council execution conditional and policy-aware.

### Council activation

`CouncilPlanner` runs after task evaluation and model feasibility/ranking. It supports:

- `auto`: enable only for open-ended reasoning when the activation score crosses a threshold;
- `always`: require council or fail explicitly when council eligibility, membership, or latency
  requirements cannot be satisfied;
- `never`: force a single-model route.

Auto mode uses deterministic signals: task type, prompt complexity, route confidence, application
metadata (`stakes=high`, `requires_consensus=true`), deliberation language, and whether the request
optimizes quality, cost, or latency. Cost- and latency-first objectives discourage automatic council
use. Only direct `llm.*` routes without tools are council-compatible. Tool, search, vision, and
blocked routes remain on their registered handlers; `always` rejects them instead of bypassing the
handler contract.

### Feasible, diverse membership

Members are drawn from the ranked candidates already approved by capability, tenant allowlist,
quality floor, per-model cost, latency, and availability. The planner prefers distinct providers and
uses the strongest-quality member as chairman. It does not introduce a model that the selector
rejected.

### Total request constraints

The planner estimates all three stages and checks the result against the end-to-end latency limit.
Catalog costs are planning estimates, not runtime accounting: they cannot capture exact review and
synthesis tokens, retries, cache use, or provider billing. Until atomic usage metering can stop the
workflow before overspend, `auto` disables council whenever `max_cost_usd` is set and records that
reason in `CouncilPlan`; `always` rejects that combination with `CouncilRequirementError`. A selected
single-model route may still use its existing catalog estimate for preflight filtering, but the
gateway does not describe that estimate as a hard runtime spend guarantee.

### Execution and degradation

`CouncilHandler` performs parallel independent answers and parallel anonymous review, accepts only
complete ballots containing every candidate exactly once, aggregates valid votes, and asks the
chairman to synthesize. It exposes all stages, label mapping, aggregate rankings, plan estimates, and
fallback state in response metadata.

If all members fail, execution fails explicitly. If only one succeeds, its answer is returned as a
degraded council result. If chairman synthesis fails, the highest-ranked successful independent
answer is returned. Candidate content is delimited and described as untrusted, and the council
adapter only exposes text completion—never unrestricted tools.

### Provider boundary

Core tests use a deterministic `MockModelCaller`. `OpenAICompatibleModelCaller` is an optional
adapter for OpenRouter, Vercel AI Gateway, LiteLLM, or another compatible endpoint. Provider access
is never required for evaluation, selection, planning, or core tests.

## Recommended next production work

1. Capture exact usage and latency for every stage and enforce an atomic workflow budget.
2. Add cancellation, per-call timeouts, retry classification, circuit breaking, and streaming stage
   events.
3. Version council prompts and use strict structured output where supported.
4. Add task-specific evidence and verifiers; peer agreement alone must not authorize high-risk
   actions.
5. Evaluate council versus the best single model using paired task sets. Measure quality lift, cost
   per successful task, latency, disagreement, and escalation precision.
6. Learn activation from observed incremental benefit only after enough labeled outcomes exist:
   `expected council quality gain - cost penalty - latency penalty`.
7. Use a separate, approval-gated agent workflow for tool execution. A council should advise; it
   should not multiply privileged actions across models.

The key product metric is not how often the council runs. It is whether council activation improves
task success enough to justify its incremental cost and latency compared with the selected single
model.
