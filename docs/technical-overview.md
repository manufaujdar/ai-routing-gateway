# Technical overview

Status: alpha, dependency-free core with optional integrations.

## Runtime and package map

- Python 3.11 or newer; package source is under src/ai_gateway.
- No required runtime dependencies.
- Optional api extra adds FastAPI and Uvicorn.
- Optional openai extra adds the OpenAI SDK for compatible endpoints.
- Development uses pytest, Ruff, build, and Twine checks.
- Entrypoints are ai-gateway and ai-gateway-team.

## Code responsibilities

- router.py: route orchestration and handler dispatch.
- evaluator.py: prompt/task classification.
- selector.py: model feasibility filtering and ranking.
- models.py: typed request, decision, response, catalog, and team models.
- adapters.py: provider caller boundary and transport validation.
- api.py and cli.py: optional HTTP/CLI surfaces.
- council.py and council_handler.py: conservative multi-perspective execution.
- team.py, team_cli.py, and team_scaffold.py: portable-team planning and skill scaffolding.
- container.py and registry.py: composition and capability registration.
- tests/ and examples/: deterministic contract and usage coverage.

## Public interfaces and operations

The Python API centers on GatewayRequest, GatewayResponse, build_container,
TeamPlanner, TeamExecutor, ProjectTask, RoleResult, and handler/registry
contracts. Optional POST /v1/route mirrors GatewayRequest. GET
/v1/capabilities exposes non-secret route and model metadata. The CLI exposes
decision-only routing and team roles/plan/init/validate commands.

Install with pip, use the editable dev extra for checks, and run pytest, Ruff,
the team validator, release check, package build, and Twine check as documented
in README.md. Provider credentials belong in environment or secret management.

## Validation and gaps

Live provider behavior, runtime usage accounting, tenant controls, unrestricted
tool execution, streaming, retry/failover, and learned quality prediction are
not guaranteed by the alpha core. Human approval remains required for release,
deployment, credentials, and external-action authorization.

