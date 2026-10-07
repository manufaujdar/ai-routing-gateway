# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) and the structure of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Added optional per-container provider concurrency admission and a reproducible decision-only
  overhead measurement script; expanded adversarial and multi-process budget tests.
- Added an agent-integration and production-boundary assessment with route and failure matrices.
- Added optional durable SQLite charge admission/reconciliation, shared execution deadlines,
  prompt/output caps and a process-local provider circuit breaker. Unknown charges remain held.
- Added optional bearer-to-container tenant API access with isolated telemetry/feedback and
  server-owned provider configuration; trusted-local defaults are unchanged.
- Added an offline runtime-control example and included examples in source distributions.
- Added opt-in versioned evidence routing with conservative fixed-cohort quality bounds,
  capability/p95 gates, candidate receipts and explicit abstention.
- Added paired offline selection replay with calibration/test ID separation and coverage metrics.
- Added call-count preflight and shared usage accounting for configured council calls.

- Added `PRIVACY_AND_DATA_BOUNDARY.md` and included it in source distributions to distinguish the MIT source license from deployment-specific privacy and service terms.
- Added a responsive local routing workspace with execution controls, provider setup, ranked
  candidates, route explanations, local history, copy, and JSON export.
- Added environment-managed and explicitly gated ephemeral OpenAI-compatible provider execution,
  request IDs and timing, health/readiness/config endpoints, injectable custom tool handlers, and
  local-only container deployment files.
- Added citation, notice, governance, deployment-boundary, validation, and model/provider/dataset
  provenance templates for safer public reuse.
- Added a deterministic local readiness auditor and CI coverage for documentation, privacy,
  accessibility, supply-chain, and decision-only execution signals.
- Added a dependency-free decision-only browser console to the optional FastAPI
  transport and documented the loopback-only Ollama adapter path.
- Added `/v1/capabilities` with non-secret routes and model metadata; authentication applies
  when optional tenant mode is configured.
- Added `--version` to both command-line tools and a PEP 561 `py.typed` marker for type-aware
  consumers.
- Added bounded single-model, verified-cascade, self-consistency, and council execution planning.
- Added prompt-free deployment telemetry, user feedback capture, observed-performance model-ranking
  adjustments, and versioned policy proposals that require explicit evaluation and promotion.
- Added execution-strategy controls, execution-plan inspection, and a telemetry panel to the local
  routing workspace.

### Changed

- HTTP input models reject unknown fields and invalid selection modes before provider setup.
  Oversized token estimates, non-finite computed prices and non-boolean availability are rejected.
- The local console tolerates malformed/full history storage, hides stale failed results and
  displays verification/usage. Local history's prompt/output persistence is explicit.
- Static readiness output now explicitly distinguishes artifact checks from production readiness.
- Unknown cost and token totals now serialize as `null`; known subtotals and unpriced call counts
  remain visible. `hard_budget_respected` is now false: catalog budgets are planning estimates.
- Adaptive ranking is opt-in. Form scores and transport success no longer count as quality labels.
- Cascades recover provider failures; sample majorities include failed samples in the denominator.
  Request identity, final-feedback attribution, endpoint namespaces and wall-time accounting are fixed.
- The bundled OpenAI-compatible adapter disables SDK retries; API numeric validation is stricter
  and validation errors omit submitted values.

- `GatewayRequest` and `ProjectTask` now reject non-boolean control flags instead of accepting
  truthy strings, integers, or `None`.
- CI and release verification now install the optional API extra because the API contract tests
  exercise the optional FastAPI transport.

### Security

- Release handlers now require external-action authorization to be exactly `True` at dispatch.
- OpenAI-compatible adapter URLs now require HTTPS by default, reject malformed URLs and userinfo,
  and permit insecure HTTP only through an explicit loopback-development option.

### Planned

- Durable tenant-aware telemetry storage, atomic runtime budget enforcement, streaming TTFT
  measurement, and production policy promotion adapters.

## [0.1.0] - 2026-07-19

### Added

- Deterministic prompt evaluation and explainable route decisions.
- Cost, quality, and latency-aware model selection over an injectable catalog.
- Policy-gated LLM council planning and provider-neutral council execution.
- Reusable specialist-team SDK with deterministic planning, independent gates, and safe release
  authorization.
- `ai-gateway` and `ai-gateway-team` command-line tools.
- Safe project-team scaffolding and validation for 12 project roles.
- Optional FastAPI and OpenAI-compatible integrations behind extras.
- Offline tests, project-agent validation, packaging checks, and GitHub release automation.
