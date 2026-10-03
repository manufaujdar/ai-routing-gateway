# Research and competitive evidence

Review date: 3 October 2026. Targeted technical review, not a systematic review or
exhaustive market census. Public primary papers, official documentation, and
selected repository files were inspected. No paid models, vendor trials, private
datasets, or live comparative benchmarks were run. Findings below distinguish
published results, documented features, and our proposed response.

## Scientific evidence and design consequences

| Primary source; inspection depth | What it supports | Limits and proposed use |
| --- | --- | --- |
| Chen, Zaharia, Zou, [FrugalGPT](https://arxiv.org/abs/2305.05176), 2023; abstract | Learned cascades can reduce cost while preserving benchmark quality; the paper reports up to 98% savings in its experiments. | Historical models and task-dependent best cases. Never reuse that number as our forecast. Evaluate cheap-first only with a useful verifier and enough deadline slack. |
| Ong et al., [RouteLLM v4](https://arxiv.org/html/2406.18665v4), revised 2025; full-text page and router source excerpt | Preference-trained strong/weak selection and threshold calibration provide a practical learned-routing baseline. | Preference wins do not establish factual accuracy; transfer must be rechecked for customer tasks and new models. Use as an optional baseline, not core dependency. |
| Hu et al., [RouterBench v2](https://arxiv.org/abs/2403.12031v2), 2024; abstract | A shared outcome matrix enables repeatable cost–performance comparisons; over 405,000 recorded outcomes are described. | Historical model pool and recorded responses do not simulate current queueing, failures, or repeated stochastic generation. Useful for methodology, insufficient for launch evidence. |
| Dekoninck, Baader, Vechev, [Unified Routing and Cascading v3](https://arxiv.org/html/2410.10347v3), 2025 revision; introduction, formulation and estimator discussion | Initial selection and post-response escalation can be optimized together; quality estimators are critical. | Optimality depends on the formal objective and estimation assumptions. It is not a production deadline or factuality guarantee. Keep pre-call quality prediction and post-call verification separate. |
| [RouterArena v3](https://arxiv.org/html/2510.00202v3), 2025/2026; evaluation discussion and scoring source excerpt | Compare accuracy, cost, optimality, robustness, and routing latency. The evaluated systems exhibit different trade-offs. | Router pools differ; leaderboard positions are not equal-pool causal comparisons. Use both controlled-pool and vendor-default tracks; do not advertise a universal rank. |
| Li et al., [LLMRouterBench v1](https://arxiv.org/html/2601.07206v1), 2026; overview, conclusion and limitations | Unified evaluation across 33 models and 21 datasets finds several advanced methods fail to reliably beat simple baselines; careful pool selection matters. | Domain-specific, very long-context and multimodal tasks are excluded; latency is estimated from tokens and provider throughput. Measure real end-to-end latency separately. |
| Moslem and Kelleher, [Dynamic Model Routing and Cascading survey v3](https://arxiv.org/abs/2603.04445v3), 2026; abstract and publication metadata | Organizes routing by decision timing, input information and computation; covers preferences, uncertainty, reinforcement learning and modalities. | A taxonomy does not establish which combination wins for our traffic. Use it to structure backup policies and ablations. |
| [Difficulty-Aware Agentic Orchestration](https://arxiv.org/abs/2509.11079), 2025 onward; abstract | Adapts workflow depth, operators, and model assignments to query difficulty. | Experimental approach, not evidence our customers need multi-agent control. Evaluate only after a single-step baseline works. Title reflects the current abstract page. |
| [ProgRouter](https://arxiv.org/abs/2608.25992), August 2026; abstract only | Proposes progress-aware model choice across workflow steps under time/cost budgets. | Recent preprint; implementation and results not independently reproduced. Future research candidate for remaining-budget planning, not a launch dependency. |

Research confidence is strongest for the need for measured trade-offs and honest
baselines; weaker for selecting any specific learned method without local data.
Abstract-only sources are discovery-level evidence. No claim is made to have
verified every proof, appendix, or latest implementation.

## Current competitors: capabilities before gaps

Each gap below is a **customer-validation hypothesis**, not proof a competitor
lacks the feature. Documentation silence is not evidence of absence. Vendor
capabilities can change after this snapshot.

| Company/project | Documented overlap | Where to investigate a customer problem |
| --- | --- | --- |
| [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) | Price/performance selection, model/provider routing and fallbacks; rolling percentile preferences. | Customer-outcome evidence and strict application deadlines. The documented performance preferences deprioritize endpoints rather than exclude them, so they must not be treated as our hard admission control. |
| [LiteLLM adaptive router](https://docs.litellm.ai/docs/adaptive_router) and [auto routing](https://docs.litellm.ai/docs/proxy/auto_routing) | Adaptive task-level quality/cost signals, auto routing, cache-aware savings and classifier costs; operational routing too. | Whether weak satisfaction signals predict true task completion; coverage-correct, whole-workflow savings against an agreed baseline. This is a direct competitor, not merely a transport adapter. |
| [Not Diamond concepts](https://docs.notdiamond.ai/docs/key-concepts) | Learned selection, custom-router identifiers, quality/cost/latency tradeoffs, continuous quality/cost blending. | Buyer demand for private evidence, calibrated uncertainty, workflow-wide constraints and interoperable policy export. These are diligence questions, not established product omissions. |
| [Martian SDK](https://withmartian.github.io/martian-sdk-python/api/routers_client.html) | Router training and configurable model sets/quality-latency preferences in the inspected SDK documentation. | Compare custom-router calibration and evaluation portability. SDK documentation is dated; current service availability, commercial terms and production capabilities remain unverified. |
| [Portkey AI Gateway](https://portkey.ai/docs/product/ai-gateway) | Gateway operations and routing; inspected open source contains conditional routing. | Quantified task outcomes across customer workflows and migration effort. Do not assume conditional routing is the full commercial feature set. |
| [Vercel AI Gateway](https://vercel.com/docs/ai-gateway) | Managed model access, routing and observability. | Evidence portability across heterogeneous/self-hosted deployments; whether customers need a separate decision product at all. Integrate if it reduces adoption cost. |
| [Amazon Bedrock intelligent prompt routing](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html) | Predicts response quality for model selection; documents default and configured routers. | Cross-provider/edge execution and workflow governance outside Bedrock. Configuration/model-family limits should be rechecked at integration time. |
| [vLLM Semantic Router](https://vllm-project.github.io/2026/07/21/vllm-sr-new-chapter-mom.html) | Explicit decision layers, session-aware routing, replay, explanation, and multi-model collaboration are already described. | Customer-specific outcome guarantees, evidence usability and operating burden. Strong build-versus-integrate competitor; do not claim explainable decision planes or topology routing as novel. |

## Decisions from experienced engineering teams

| Primary engineering source | Observed guidance | Our design decision |
| --- | --- | --- |
| Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Start with simple solutions; distinguish predictable workflows from open-ended agents. | No model call for ordinary filtering, budgets, receipts or policy enforcement. Add learned routing only after replay beats deterministic baselines. |
| Anthropic, [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | Parallel research helps suitable tasks but introduces substantial token and coordination costs; the article reports about 15 times chat token use in its setting. | Bound fan-out and judge costs under one workflow budget. Never apply that multiplier universally or put the company team on every request. |
| Google SRE, [Handling overload](https://sre.google/sre-book/handling-overload/) | Admission control, load shedding and restrained retries are essential under overload. | Single retry owner, workflow-wide attempt cap, jitter, circuit breakers, and explicit overload response. |
| vLLM, [Mixture-of-Models architecture](https://vllm-project.github.io/2026/07/21/vllm-sr-new-chapter-mom.html) | Separates signals, policies, algorithms and model backends. | Preserve our evaluator/selector/executor boundaries and assess integration before building infrastructure. |

## Gaps worth testing, in order

1. **Outcome evidence:** do operators know whether cheaper routing increased human
   rework or silent error? Interview and measure; schema validity is not truth.
2. **Full cost attribution:** can finance reconcile initial calls, classifiers,
   retries, judges, tool charges and integration costs? Compare to actual invoices.
3. **Uncertainty during change:** can a new model version or new task enter service
   without treating stale quality estimates as facts? Test cold-start and drift.
4. **Session-level trade-offs:** are savings lost to cache misses, state conversion,
   inconsistent tool behavior or repeated user prompts? Replay full sessions.
5. **Portable control:** do customers need one evidence/policy layer across hosted
   gateways and private deployments? Verify willingness to pay before building it.

These problems overlap with competitors' roadmaps and products. Sustainable
differentiation requires better customer evidence and execution, not stronger
marketing language.
