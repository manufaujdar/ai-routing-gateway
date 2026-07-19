# AI Gateway and Agent Routing Strategy

Research date: 2026-07-19

## Executive recommendation

Do not begin by recreating the provider-aggregation layer already offered by Vercel AI
Gateway, OpenRouter, LiteLLM, and Portkey. Use one or more of them as replaceable execution
adapters. Build the differentiated layer above them: an explainable decision plane that decides:

1. whether the request is safe and permitted;
2. whether it needs a tool, one model call, a deterministic workflow, or multiple agents;
3. which models are feasible given capability, residency, budget, latency, and quality limits;
4. which feasible model has the best expected utility for this request;
5. what fallback or escalation should run if the first attempt fails a technical or quality check.

The product should optimize outcomes, not merely tokens. Its durable advantage will come from
customer-specific evaluation and feedback data: model quality by task, tenant, tool set, and
workflow. Provider catalogs and generic benchmarks are necessary bootstrap data, but they do not
tell a customer which model succeeds on that customer's support tickets, codebase, documents, or
agent tools.

## What existing systems do

| System | Strongest layer | Current approach | Gap this project can address |
| --- | --- | --- | --- |
| Vercel AI Gateway | Managed transport gateway | Unified API, provider failover, budgets, and observability. Its cost-aware guide leaves task difficulty classification in application code. | Cross-provider, application-specific quality prediction and agent-topology selection. |
| OpenRouter | Model/provider marketplace and routing | Large catalog; provider filters; routing by price, throughput, or latency; rolling percentile performance signals; automatic provider fallback. | Customer-specific task success and workflow-aware routing above provider health. |
| LiteLLM | Self-hostable compatibility and operations | OpenAI-compatible translation, retries/fallbacks, load balancing, spend tracking, budgets, and callbacks. | A rigorous request-to-model quality policy and learning loop. |
| Portkey | Enterprise gateway operations | Composable fallback, load balancing, conditional routing, caching, guardrails, budgets, and observability. | Predictive selection based on expected task quality rather than only configured conditions. |
| Not Diamond | Learned model router | Predicts a model using quality, cost, and latency trade-offs; supports general and custom routers. | A transparent, self-hostable policy layer that also selects tools, workflows, and agent topology. |
| RouteLLM | Routing research/framework | Learns when a stronger model is worth its cost from preference data and provides routing evaluation. | Production policy, capability filtering, provider reliability, agents, and tenant controls. |

Primary references:

- [Vercel AI Gateway overview](https://vercel.com/docs/ai-gateway) and
  [cost-aware model routing guide](https://vercel.com/kb/guide/cost-aware-model-routing-with-ai-gateway)
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [LiteLLM documentation](https://docs.litellm.ai/)
- [Portkey AI Gateway](https://portkey.ai/docs/product/ai-gateway) and
  [fallback composition](https://portkey.ai/docs/product/ai-gateway/fallbacks)
- [Not Diamond routing concepts](https://docs.notdiamond.ai/docs/key-concepts)
- [RouteLLM paper](https://arxiv.org/abs/2406.18665) and
  [evaluation framework](https://github.com/lm-sys/RouteLLM)

## Proposed architecture

```text
Request + tenant policy + objective
                |
                v
      Safety and policy gate                 hard constraints
                |
                v
       Task/capability evaluator              deterministic first
                |
                v
    Execution-topology selector  ----->  direct | tool | workflow | multi-agent
                |
                v
          Model feasibility filter            capabilities, budget, SLA, privacy
                |
                v
          Utility-based model ranker           quality, cost, latency, reliability
                |
                v
       Execution adapter / gateway             Vercel, OpenRouter, LiteLLM, direct
                |
                v
     Verifier, fallback, or escalation         only when expected value is positive
                |
                v
      Outcome telemetry and evaluation  -----> profiles and policies
```

These components must remain separate. In particular, a provider health router answers “where can
this exact model run?” while a model router answers “which model should do this task?” and an agent
router answers “what execution topology should solve it?” Combining those decisions into one opaque
model call makes failures expensive to debug and policies hard to enforce.

## Selection algorithm

Start deterministic and graduate to learned prediction only when outcome labels exist.

### 1. Evaluate the request

Produce task type, complexity, required capabilities, risk, expected input/output size, and routing
confidence. Explicit metadata supplied by the application should override weak prompt inference.
High-risk actions must be blocked or constrained before any tool-capable agent is considered.

### 2. Filter hard constraints

Reject candidates lacking required modalities, tools, context length, structured output, region,
data-retention policy, tenant allowlisting, availability, maximum estimated cost, minimum quality,
or maximum latency. A weighted score must never compensate for a violated security or compliance
constraint.

### 3. Rank the feasible set

For the initial version, normalize quality, estimated request cost, and latency within the feasible
set and calculate a request-objective score:

```text
utility = w_quality * quality
        + w_cost    * inverse_cost
        + w_latency * inverse_latency
```

Keep every component, estimate, weight, and rejection reason observable. Later, add reliability and
cache-hit probability, and replace generic quality with `P(success | task, model, tenant, context)`.
The top candidate is primary; the remaining compatible candidates are an ordered fallback plan.

### 4. Verify and escalate selectively

Do not routinely call two models and judge both; that destroys the savings. Use a cheap, task-specific
verifier only where failure is detectable: schema validation, unit tests, citation checks, policy
checks, retrieval grounding, or a calibrated confidence threshold. Escalate to a stronger candidate
when the expected value of improved quality exceeds its incremental cost and delay.

## How agents fit

“More agents” is not automatically more capable. Multi-agent execution increases token use,
coordination failures, latency, and the tool attack surface. Prefer this decision order:

1. deterministic code for fixed, verifiable transformations;
2. a single tool-using agent for one coherent objective;
3. a coded workflow when steps and state transitions are known;
4. manager plus specialist agents when the work is open-ended, decomposable, parallelizable, and
   valuable enough to justify the overhead;
5. handoff to a specialist when it should own the conversation rather than report to a manager.

OpenAI's Agents SDK documents manager/agents-as-tools and handoff patterns, while Anthropic's
research system uses an orchestrator-worker pattern for parallel open-ended research. Those are
execution patterns, not substitutes for the model decision plane.

References: [OpenAI agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)
and [Anthropic's multi-agent research architecture](https://www.anthropic.com/engineering/multi-agent-research-system).

Each agent invocation should call the same model selector with its own task type and constraints.
The planner may deserve a high-quality reasoning model; narrow retrieval workers may use cheap fast
models; a code verifier may use deterministic tests. Enforce a workflow-wide budget, depth limit,
parallelism limit, tool allowlist, and approval boundary in addition to per-call limits.

## Defensible learning loop

Record a privacy-safe event for every decision and attempt:

- decision ID, tenant/application, task taxonomy, complexity, and policy version;
- candidate set, eliminated candidates and reasons, score components, selected model and fallback;
- provider/model version, tokens, cache status, time to first token, total latency, retries, and cost;
- technical validity, task-specific verifier results, user feedback, and downstream business outcome;
- agent topology, tool calls, approvals, step cost, and final status.

Use explicit consent and redaction; do not store raw private prompts by default. Build offline replay
and shadow evaluation before online learning. Compare policies at equal quality, cost, and latency
budgets, not only average benchmark accuracy. Use contextual bandits only after guardrails, delayed
outcome handling, exploration budgets, and rollback are in place.

## Delivery roadmap

### Phase 1: explainable deterministic router (implemented)

- model catalog with task support, quality estimate, price estimate, and latency estimate;
- hard filters for model allowlists, budget, latency, and minimum quality;
- request objectives for balanced, cost, quality, and latency;
- ranked candidate/fallback list and an observable selection reason;
- offline behavior and injectable catalog for telemetry-backed production data.

### Phase 2: provider execution and reliability

- adapters for one managed gateway and one self-hosted option;
- capability translation, timeouts, retries, circuit breakers, compatible fallbacks, and streaming;
- real usage/cost capture and model catalog refresh with versioned snapshots;
- tenant auth, budget accounting, privacy/residency policies, and audit events.

### Phase 3: evaluation and escalation

- golden task sets per application and task-specific verifiers;
- replay harness, quality/cost/latency Pareto reports, shadow selection, and canary rollout;
- calibrated escalation from cheap to strong models;
- confidence and abstention when the router lacks evidence.

### Phase 4: workflow and agent routing

- execution-plan model (`direct`, `tool`, `workflow`, `manager-workers`, `handoff`);
- typed tool schemas, sandbox boundaries, human approvals, and workflow budgets;
- specialized per-step model selection and parallel worker scheduling;
- trace-level evaluation of final outcomes rather than grading isolated model messages.

### Phase 5: customer-specific learned routing

- per-task success prediction trained on preference, verifier, and outcome data;
- drift detection for quality, price, and latency;
- safe contextual exploration, automatic rollback, and policy simulation;
- recommendations showing expected quality retained, money saved, and latency impact.

## Success metrics

Use a constrained scorecard rather than one blended vanity metric:

- primary: task success rate at a defined spend and latency budget;
- efficiency: cost per successful task and agent steps per successful task;
- experience: p50/p95 time to first token and end-to-end completion latency;
- reliability: successful completion rate, fallback rate, and budget-exhaustion rate;
- routing: regret versus the best known feasible model, escalation precision/recall, and abstention;
- safety: policy violations, unrestricted high-risk tool executions, and approval bypasses.

The initial target should be a measurable reduction in cost per successful task while holding task
success and p95 latency within agreed guardrails. Claims such as “best model” are not meaningful
without that task- and customer-specific definition.
