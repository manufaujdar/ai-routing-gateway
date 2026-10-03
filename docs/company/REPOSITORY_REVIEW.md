# Repository review and adoption decisions

Read-only public snapshots checked on 3 October 2026. All six GitHub metadata
responses reported `archived=false`. This does not prove active maintenance or
security. No upstream code, models or datasets were installed, copied into the
product, or executed. Hashes identify references, not recommended releases.

## Upstream snapshots

| Repository and pinned revision | Material inspected | Decision and limit |
| --- | --- | --- |
| [lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM/tree/0b64fdafe049e596a3f5657c219329f24af24198), `0b64fdafe049e596a3f5657c219329f24af24198` | Tree and `routellm/routers/routers.py` lines 1–105: strong/weak threshold interface and causal router initialization | Optional learned baseline behind an adapter. Heavy ML dependencies and model artifacts must remain outside the dependency-free core. Root license metadata Apache-2.0. Latest default-branch commit returned was 2024-08-10; verify the desired maintained fork/release before adoption. |
| [eth-sri/cascade-routing](https://github.com/eth-sri/cascade-routing/tree/1788b904a42aa586d555784be240b344868480d2), `1788b904a42aa586d555784be240b344868480d2` | Tree and `src/selection/cascade_router.py` lines 1–105: quality/cost inputs, depth and ordering controls, prediction entry point | Research comparison for expected-cost planning. Do not confuse expected-cost optimization with enforceable spend reservation or deadline control. Root metadata Apache-2.0; returned commit 2025-02-14. |
| [RouteWorks/RouterArena](https://github.com/RouteWorks/RouterArena/tree/04c99fdbe4a3ec1f44475694f46dd25065c8fd8a), `04c99fdbe4a3ec1f44475694f46dd25065c8fd8a` | Tree and `router_evaluation/compute_scores.py` lines 1–105, including source SPDX header | Benchmark adapter/reference; report component metrics alongside aggregate score. Excerpt ignores nonpositive/missing costs in cost collection: our receipts must distinguish free, missing and pending costs and report coverage. Root metadata and inspected header Apache-2.0. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm/tree/e340e546e24c17c302475279e885a302b19f5b94), `e340e546e24c17c302475279e885a302b19f5b94` | Repository tree, root LICENSE, current official routing/adaptive/auto-routing documentation | Candidate execution integration and direct competitor. Root LICENSE makes non-enterprise content MIT and refers enterprise content to a separate license; GitHub reports NOASSERTION. Do not treat the entire repository as uniformly MIT. Runtime implementation/tests were not audited. |
| [vllm-project/semantic-router](https://github.com/vllm-project/semantic-router/tree/49395c6755bc7422e3d4b3c13c49aa43f8acc355), `49395c6755bc7422e3d4b3c13c49aa43f8acc355` | Tree, `website/docs/overview/semantic-router-overview.md` lines 1–105, official architecture article | Strong integration alternative; explicitly separates policy, signals, algorithms, gateway and backends. Root metadata Apache-2.0 with additional nested license files present. This was an architecture review, not validation of Go/runtime behavior. |
| [Portkey-AI/gateway](https://github.com/Portkey-AI/gateway/tree/669825cbe89ee51569918b8f78a9db486fd69dd4), `669825cbe89ee51569918b8f78a9db486fd69dd4` | Tree and `src/services/conditionalRouter.ts` lines 1–105: conditions, first matching target, explicit default/no-match behavior | Optional transport comparison and conditional-policy inspiration. Keep policy selection and execution separate. Root metadata MIT; commercial cloud behavior can exceed this source. |

License observations above are limited to metadata and the specifically inspected
files. Before code adoption, read selected files, tests and path-specific licenses,
pin a compatible release, and update `THIRD_PARTY_NOTICES.md` for any copied
material. This research task adopts ideas, not third-party code.

## Existing project: reuse and concrete gaps

Local base: `55edcef5506b6e5fae55b376c5924a7b38aea1eb`. Source inspected includes
`selector.py`, `optimization.py`, `telemetry.py`, verifier/cascade sections of
`execution.py`, strategy references and existing team tests.

| Current implementation | Reuse | Gap to address before a company pilot |
| --- | --- | --- |
| `ModelSelector` in `src/ai_gateway/selector.py` | Filtering and observable model candidates | Fixed weights and candidate-relative normalization are not calibrated task success; filtering uses estimated point latency/cost. Add opt-in cohort estimates and constrained plan selection. |
| `ModelCatalog` | Immutable profiles and task lookup | Unique model identifiers are required by dispatch even when multiple deployments might serve the same model. Version a deployment-aware call contract before supporting that product promise. |
| `HeuristicResponseVerifier` in `execution.py` | Injectable verifier protocol | Nonempty/length/code/reasoning-language checks assess form, explicitly not factual correctness. Never market this score as accuracy. Add task-specific checks and labeled validation. |
| Cascade and self-consistency planning | Bounded strategies and observability | Plan estimates are not an atomic ledger or real deadline guarantee. Require reservations and whole-path accounting before strict-budget execution. |
| `AdaptiveRoutingAgent` in `optimization.py` | Optional adjustment and proposal boundary | Small sample minimum and heuristic aggregates do not establish calibration or unbiased counterfactual gains. Scores can use technical success as a proxy; require outcome definitions and replay. |
| `InMemoryTelemetryStore` in `telemetry.py` | Prompt-free call observations | Process-local storage and no tenant isolation. Aggregation treats absent cost as zero via `cost_usd or 0.0`; add explicit unknown-cost coverage before savings claims. These are design findings, not fixes made here. |
| 12-role team and validator | Existing ownership, gates, local skill discovery | Company-specific responsibilities are supplied through references, without a competing agent registry or always-running swarm. |

## Recommended implementation ownership

Builder owns future production changes; Engineer supplies contracts; QA and
Safety own independent verification. Preserve `src/ai_gateway/selector.py` as the
legacy behavior while adding an opt-in policy implementation. Extend the existing
telemetry interfaces rather than adding a disconnected event system. Keep the
reservation store behind a protocol with an offline deterministic test double
and an explicitly selected durable transactional backend for deployment.

The MVP should not fork any complete competitor. First benchmark whether an
existing routing engine plus our evaluation/reporting layer solves the problem.
Only then implement missing behavior at the seams above.
