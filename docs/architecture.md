# System architecture

AI Routing Gateway separates deterministic decision-making from optional
execution adapters. The core remains offline-testable and does not require a
provider, web tool, database, or hosted service.

## Component flow

Request -> evaluator -> model selector -> council planner -> router -> registered
handler or council handler -> response.

The evaluator classifies task and capability needs. The selector filters and
ranks the model catalog. The council planner decides whether independent
specialist perspectives are eligible. The router dispatches only to a
host-registered handler.

## Major boundaries

- models.py: typed request, decision, response, team, and policy contracts.
- evaluator.py and selector.py: deterministic classification and ranking.
- router.py: route selection and handler dispatch.
- adapters.py: optional provider caller boundary and transport validation.
- api.py and cli.py: optional HTTP and CLI surfaces.
- team.py and council.py: specialist-agent planning and execution.
- registry.py and container.py: composition and capability registration.

The core must not import application-specific providers, tools, credentials,
or external actions. The host application owns those integrations and supplies
handlers.

## Runtime topology and evolution

The default runtime is a Python library or CLI in the caller's process. The
optional FastAPI app is a local transport. A production host must add
authentication, tenant isolation, rate limits, retries, telemetry, tool
schemas, sandboxing, retention, and provider reliability policy.

Keep provider transport, model choice, and agent topology as separate
decisions. Record material changes in the strategy/release documents and keep
the deterministic offline path working.

