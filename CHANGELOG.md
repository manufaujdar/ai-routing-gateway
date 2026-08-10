# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) and the structure of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Added a dependency-free decision-only browser console to the optional FastAPI
  transport and documented the loopback-only Ollama adapter path.
- Added an authenticated `/v1/capabilities` endpoint with non-secret routes and model metadata.

### Changed

- `GatewayRequest` and `ProjectTask` now reject non-boolean control flags instead of accepting
  truthy strings, integers, or `None`.

### Security

- Release handlers now require external-action authorization to be exactly `True` at dispatch.
- OpenAI-compatible adapter URLs now require HTTPS by default, reject malformed URLs and userinfo,
  and permit insecure HTTP only through an explicit loopback-development option.

### Planned

- Provider telemetry, runtime usage metering, and production policy adapters.

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
