# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) and the structure of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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
- Added an authenticated `/v1/capabilities` endpoint with non-secret routes and model metadata.
- Added `--version` to both command-line tools and a PEP 561 `py.typed` marker for type-aware
  consumers.
- Added bounded single-model, verified-cascade, self-consistency, and council execution planning.
- Added prompt-free deployment telemetry, user feedback capture, observed-performance model-ranking
  adjustments, and versioned policy proposals that require explicit evaluation and promotion.
- Added execution-strategy controls, execution-plan inspection, and a telemetry panel to the local
  routing workspace.

### Changed

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
