# Evaluation, economics and delivery plan

All targets here are **proposed acceptance criteria**, not observed performance.
This is the build sequence for the company design, not a second active backlog.
Activate one slice at a time in `.ai/HANDOFF.md`.

## What we must prove

The router must outperform the customer's real policy after charging for routing,
verification, retry, cache changes, tools and operations. Measure three primary
dimensions separately: task success, total cost, and end-to-end latency. Report
the Pareto frontier rather than hiding trade-offs in one score.

Primary economic measure:

```text
cost per successful task = all attributable costs / successful tasks
cost per timely successful task = all attributable costs / tasks correct within deadline
customer net value = baseline total cost - routed total cost - fees - integration amortization
```

Define success independently of the router/verifier. Count failures, timeouts and
abstentions in the offered-task denominator; show conditional accuracy on answered
tasks as a separate metric. Zero successes makes cost-per-success undefined or
infinite, never zero. Cost per success is an aggregate accounting ratio, not the
expected cost of retrying until success under an independence assumption.

## Experimental design

1. **Fix scope:** one workload, success rubric, critical error classes, permissible
   quality loss, time horizon, budget and customer baseline. Freeze the model,
   deployment, prompt, tool and policy versions where possible.
2. **Build evidence:** use customer-authorized cases, stratified by task,
   language, input length, difficulty and relevant failure categories. Split by
   customer/session/document lineage and time to avoid near-duplicate leakage.
   Maintain separate train, calibration and untouched test sets.
3. **Compare baselines:** current production policy; fixed strong; cheapest
   eligible; simple task rules; random feasible routing; RouteLLM-style threshold;
   learned predictor; verified cascade. Add LiteLLM/vLLM or commercial routers
   when authorized and integration permits. Report equal model-pool experiments
   separately from vendor-default product experiments.
4. **Measure actual operation:** randomize/interleave time blocks and account for
   rate limits and load. Repeat stochastic tasks where variation matters. Record
   warm/cold cache separately, concurrency, region, input/output tokens, TTFT,
   completion, verifier time, retries, cost coverage and errors. Public recorded
   matrices cannot establish production latency.
5. **Estimate uncertainty:** paired comparisons on shared cases; session-clustered
   bootstrap intervals where dependencies exist; a prespecified one-sided
   noninferiority test for quality. Use blinded human adjudication on sampled
   disagreements and critical errors. Calibrate judges against those labels;
   test order and model-family bias. A judge agreement score is not truth.
6. **Challenge generalization:** hold out a model, new task, later time period,
   long input, language and provider incident. Evaluate OOD detection, calibration
   curves/Brier score, risk–coverage, and verifier false accepts/rejects by slice.
7. **Only then canary:** decision-only shadow incurs no second inference; outcome
   shadow does incur paid calls and needs budget/data authorization. Randomize
   eligible low-risk traffic, retain a control, reconcile delayed labels and roll
   back with a versioned static policy.

Start discovery with 200–500 labeled cases to expose gross failures and estimate
variance. This is not enough by definition for a one-percentage-point quality
claim. Determine confirmatory sample size from the desired margin, discordant
paired outcomes, error prevalence, clustering and power. Prespecify primary slices
and multiplicity treatment; treat underpowered exploratory slices as uncertain.
For intuition only, zero independent failures in 300 trials gives a one-sided
95% binomial upper bound near 1%; it does not establish safety across every cohort.

Offline evaluation on chosen-action logs cannot infer the unobserved model's
answer. For counterfactual policy estimates, require randomized coverage, logged
propensities and overlap; use appropriate IPS/doubly robust methods and effective
sample-size checks. Without overlap, gather approved paired labels. An oracle
using known answers is an upper bound, never a deployable competitor.

## Proposed pilot gates

| Gate | Acceptance contract |
| --- | --- |
| Quality | One-sided 95% lower confidence bound on routed-minus-baseline success >= -1 percentage point; margin must be accepted for this workflow. Stricter tasks may require zero tolerated degradation. |
| Cost | At least 20% lower total cost per successful task against the agreed baseline, with uncertainty and coverage disclosed; this is a commercial hypothesis. |
| Latency | Customer deadline-miss rate within its contract, plus p50/p95/p99 TTFT and completion reported. No material p95 regression beyond the agreed bound. |
| Accounting | Every billed or pending attempt linked to a reservation; reconcile invoice deltas. Missing prices/costs prevent a complete-savings claim. |
| Policy | No observed cross-tenant, forbidden-region, tool-permission or budget-admission violation in specified tests; production guarantees need additional evidence. |
| Operations | Rollback exercised, predictor/control-plane outage handled, global retry cap verified and sustained-load profile documented. |

For early canaries, propose 1% -> 5% -> 25% -> eligible full rollout. These are
traffic fractions, not automatic timers. Advance only after prespecified sample
and observation windows include delayed outcomes. Abort immediately on policy
violations; use a prespecified sequential statistical rule for noisy quality/cost
signals rather than repeated uncorrected peeking. Maintain holdout traffic where
appropriate to detect model or workload drift.

## Failure-oriented test matrix

| Scenario | Expected behavior |
| --- | --- |
| No feasible route, stale price, unknown capabilities | Explicit abstention/reason; no unauthorized dispatch |
| Simultaneous workers and budget exhaustion | Atomic reservation admits only affordable exposure |
| Lost response, crash, cancellation | Pending charge retained; idempotent reconciliation; no duplicate side effect |
| Nested gateway/provider retries | Single global cap and complete attempt accounting |
| Router outage, OOD input, drift | Approved eligible static route or abstention; no unknown “quality guarantee” |
| Cheap convincing falsehood / valid JSON with wrong fields | Semantic failure recorded; form checks cannot certify correctness |
| Prompt tells router to override region/budget | Trusted policy unchanged; prompt treated as data |
| Stream emitted then provider fails | No invisible model splice; documented partial-result status |
| Correlated provider outages or verifier/model errors | Joint scenarios tested; independence assumptions not used blindly |
| Price/model/prompt/tool change | Version-specific qualification; invalidate relevant stale estimates |
| Feedback spoofing / missing labels | Authenticated deduplicated feedback; no automatic policy promotion |

## Roadmap with accountable roles

Indicative 12-week sequence for a small available team, not a staffing or delivery
commitment. Evidence gates override dates. Agent roles do not replace human
engineering capacity or independent certification.

| Window | Slice, owner and output | Exit / stopping condition |
| --- | --- | --- |
| Weeks 1–2 | Planner + R&D: 8–12 proposed interviews, select 2–3 design partners, choose one task and baseline | Customer authorization and usable labels. Stop broad platform building if the problem or willingness to pay is absent. Contact is not authorized by this plan. |
| Weeks 2–4 | Engineer + Builder: immutable policy/receipts, full attempt costs, deterministic replay and no-route states | Offline invariants pass; costs marked known/estimated/pending; no provider spend required. |
| Weeks 4–6 | Builder: optional constrained selector, durable atomic ledger, one gateway adapter and direct/mock path | Tests cover concurrency, failure, compatibility and rollback; existing API behavior preserved. |
| Weeks 6–8 | R&D + QA + Safety: approved benchmark with small pool, calibrated predictor and verifier | Beat simple baselines under all agreed primary gates; otherwise keep static rules. |
| Weeks 8–10 | Release: shadow and bounded canary in customer-controlled environment | Authorized budget, separate review evidence, rollback exercised, delayed labels mature. |
| Weeks 10–12 | Planner + Marketer: repeatability and paid-pilot decision | Positive customer net value, operating cost understood, evidence report usable without founder assistance. |

Defer bandits, autonomous topology search, multimodal routing, speculative
execution and a provider marketplace. Introduce one alternative only when a
specific observed problem and ablation justify it.

## Build, integrate, or stop

Build our evaluation contracts, receipts, outcome definitions and policy gates.
Use existing transports and qualification data where licensed and compatible.
Evaluate vLLM Semantic Router for customers who already operate that stack and
LiteLLM for Python/gateway integration; do not make either a mandatory dependency
without a maintenance and deployment assessment.

Stop or narrow the company if three qualified pilots cannot demonstrate useful
net value, if labels cost more than savings, or if an existing product meets the
same requirements at lower ownership cost. Expand toward workflow decisions only
after per-request value is reproducible. No background monitor is scheduled by
this roadmap.
