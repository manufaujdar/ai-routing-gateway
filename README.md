# AI Routing Gateway

[![CI](https://github.com/manufaujdar/ai-routing-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/manufaujdar/ai-routing-gateway/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An offline-first Python tool for explainable AI model and tool routing.

AI Routing Gateway is an embeddable Python library for explainable model/tool routing and gated
specialist-agent workflows. It is designed to integrate into another application; no website or
hosted service is required.

The core is dependency-free, deterministic, and offline-testable. Provider calls, web tools, APIs,
and agent frameworks are optional adapters owned by the integrating project.

> **Project status: alpha.** The included catalog values and handlers are stable test fixtures, not
> live provider guarantees. Runtime usage accounting, tenant controls, provider reliability policy,
> and unrestricted tool execution are not included. Public interfaces may evolve before 1.0.

## What it provides

- Explainable prompt classification and routing to LLM or tool capabilities.
- Model ranking across cost, quality, and latency constraints.
- Bounded `single`, verified `cascade`, parallel `self_consistency`, and multi-model `council`
  execution strategies, with an `auto` policy that chooses among them.
- Prompt-free deployment telemetry and a deterministic adaptive routing advisor that proposes
  versioned policy changes without applying them automatically.
- Conservative LLM council activation with `auto`, `always`, and `never` modes.
- A reusable 12-role project team: Lead, Planner, R&D, Designer, Engineer, Builder, Reviewer, QA,
  Safety, Documentation, Marketer, and Release.
- Deterministic team planning, application-owned handlers, independent gates, and explicit external
  action authorization.
- Python APIs plus `ai-gateway` and `ai-gateway-team` command-line tools.

## Quickstart

Create a clean environment, install the package, and make a decision without a
provider key or network call:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -e .
ai-gateway --version
ai-gateway --decision-only "Summarize the trade-offs between two deployment plans"
```

The command prints JSON containing the selected route, model, confidence,
candidate models, and the reasons behind the decision. The default core package
is dependency-free; optional transports and provider adapters are installed only
when you need them.

## Installation

Python 3.11 or newer is required.

Install from a cloned GitHub repository today:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

For development:

```bash
python -m pip install -e '.[dev]'
```

After a PyPI release, the base package will be installable with:

```bash
python -m pip install ai-routing-gateway
```

Optional integrations are installed explicitly:

```bash
python -m pip install '.[openai]'  # OpenAI-compatible model caller
python -m pip install '.[api]'     # Optional FastAPI transport
```

## 1. Route prompts and choose models

```python
from ai_gateway import GatewayRequest, build_container

gateway = build_container().router
response = gateway.route(
    GatewayRequest(
        prompt="Compare two deployment strategies",
        execute=False,
        max_cost_usd=0.01,
        max_latency_ms=1500,
    )
)

print(response.decision.route)
print(response.decision.model)
print(response.decision.reasons)
```

`execute=False` returns the decision without dispatching a handler. The default composition root
uses mock handlers so examples and tests remain offline.

Control flags are strict booleans. For example, `execute` accepts only Python `True`/`False` (and the
API accepts only JSON `true`/`false`); strings, integers, and `None` are rejected before handler
dispatch.

The routing pipeline is:

```text
GatewayRequest
  -> Evaluator
  -> ModelSelector
  -> CouncilPlanner
  -> ExecutionPlanner
  -> Router
  -> registered Handler, AdaptiveLLMHandler, or CouncilHandler
  -> GatewayResponse
```

Included capability routes are `llm.fast`, `llm.reasoning`, `llm.code`, `tool.web_search`,
`tool.vision`, and `blocked`. Route, model, tools, confidence, candidates, council plan, execution
plan, and reasons remain observable in the response.

### Adaptive execution and routing advisor

Set `execution_strategy` to `auto`, `single`, `cascade`, `self_consistency`, or `council`.
Cascade starts with the lowest-cost feasible model and escalates when the configured verifier
rejects the response. Self-consistency runs bounded independent samples and uses majority agreement
or one aggregation call. Estimates are planning controls, not atomic provider spend guarantees.

Configured direct-model calls record prompt-free outcome data such as deployment, task, strategy,
success, latency, token counts, estimated or provider-reported cost, and verifier score. Prompts and
responses are not stored in this telemetry. `AdaptiveRoutingAgent` waits for a minimum sample count
before influencing ranking and only emits policy proposals; promotion still requires replay,
explicit approval, and a canary rollout.

### Council behavior

Councils are eligible only on direct `llm.*` routes without tools. `always` raises
`CouncilRequirementError` when the requirement cannot be satisfied safely. Because catalog
estimates are not atomic runtime accounting, a request with `max_cost_usd` disables councils in
`auto` and is rejected in `always` mode.

## 2. Plan and execute a specialist-agent team

Planning is deterministic and never calls a model. The host application supplies each role handler,
which can use Codex, OpenAI, Anthropic, LangGraph, local models, internal services, or plain Python.

```python
from ai_gateway import (
    ProjectTask,
    RoleResult,
    RoleStatus,
    TeamExecutor,
    TeamPlanner,
    TeamRoleRegistry,
)


class LocalRoleHandler:
    def __init__(self, role):
        self.role = role

    def run(self, task, step, context):
        return RoleResult(
            role=self.role,
            status=RoleStatus.PASSED,
            summary=f"Completed {step.name} for {task.objective}",
        )


task = ProjectTask("Prepare an integration plan")
plan = TeamPlanner().plan(task)

registry = TeamRoleRegistry()
for role in plan.roles:
    registry.register(role, LocalRoleHandler(role))

run = TeamExecutor(registry, parallel=True).execute(plan)
print(run.succeeded)
```

Execution preflights all required handlers. Failed or blocked roles stop downstream work.
Certification roles may run concurrently while results retain stable plan order. The same handler
object cannot implement Builder and independently certify that work. Release handlers are never
invoked unless `external_actions_authorized` is exactly `True`. All `ProjectTask` control flags,
including `release_requested` and `external_actions_authorized`, reject truthy strings, integers,
and `None` rather than coercing them.

Team council advice is conservative: every eligibility condition must be established—product or
research scope, high stakes, ambiguity, hard-to-reverse impact, materially competing approaches,
useful independent perspectives, and sufficient cost/latency budget. The advice is observable and
does not itself make a provider call.

## Command-line tools

```bash
ai-gateway --decision-only "Compare these options and recommend one"
ai-gateway --decision-only --optimize cost --max-cost-usd 0.01 \
  "Compare these options and recommend one"

ai-gateway-team roles --json
ai-gateway-team plan "Add tenant-aware routing" --kind feature --ai-policy
ai-gateway-team init /path/to/project
ai-gateway-team validate /path/to/project
```

`ai-gateway-team init` generates structurally validated, Codex-compatible project-local skill
contracts when the client supports repository skills. It preflights fixed destinations, refuses
overwrites by default, and rejects symlink escapes and known invalid/tampered contracts. Structural
validation is not a sandbox or a comprehensive malicious-skill scanner; review generated and edited
instructions before enabling an agent runtime.

## Provider integration

The OpenAI-compatible adapter can target an OpenAI-compatible gateway such as OpenRouter or another
compatible endpoint:

```python
import os

from ai_gateway import build_container
from ai_gateway.adapters import OpenAICompatibleModelCaller

caller = OpenAICompatibleModelCaller(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
container = build_container(model_caller=caller)
```

Adapter base URLs must be well-formed HTTPS URLs without userinfo, query strings, or fragments.
Plain HTTP is rejected by default. Local development may opt into HTTP only for a literal loopback
host (`localhost`, `127.0.0.0/8`, or `::1`):

```python
caller = OpenAICompatibleModelCaller(
    api_key="local-development-key",
    base_url="http://127.0.0.1:8000/v1",
    allow_insecure_loopback=True,
)
```

Configure the model catalog for the selected endpoint. Keep provider credentials in environment or
secret-management systems; never commit them or include private prompts in traces.

## Optional HTTP transport

The FastAPI application is an optional transport, not the primary product:

```bash
python -m pip install '.[api]'
uvicorn ai_gateway.api:app --reload
```

Open `http://127.0.0.1:8000/` for a small local routing console. It sends
decision-only requests by default and needs no model key. The console exposes routing budgets,
model allow-lists, optimization, execution strategy, verifier controls, council policy, optional
execution, ranked candidates, execution plans, prompt-free telemetry, route reasons, local decision
history, copy, and JSON download. Browser history never stores provider keys.

### Run with a real OpenAI-compatible provider

The preferred path keeps credentials in the server environment:

```bash
python -m pip install -e '.[api,openai]'
cp .env.example .env
# Edit .env and set AI_GATEWAY_API_KEY, endpoint, and model identifiers.
set -a && source .env && set +a
uvicorn ai_gateway.api:app --host 127.0.0.1 --port 8000
```

The server accepts `AI_GATEWAY_API_KEY` (or `OPENAI_API_KEY` as a fallback),
`AI_GATEWAY_BASE_URL`, `DEFAULT_LLM_MODEL`, `REASONING_LLM_MODEL`, `CODE_LLM_MODEL`, and
`AI_GATEWAY_TIMEOUT_SECONDS`. The key is never returned by `/v1/config` or
`/v1/capabilities`.

For a trusted single-user local session, set `AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS=true` to expose
the frontend's ephemeral provider form. That form sends a key for one request, keeps it only in page
memory, and excludes it from local history. Never enable this mode on a shared or public server.

Direct `llm.*` routes execute through the configured provider. Specialized `tool.web_search` and
`tool.vision` routes deliberately fail closed until the host application registers reviewed tool
handlers. Inject them with `build_container(route_handlers={...})`, then pass the container to
`create_app(container)`.

### Container run

The included Compose configuration binds only to local loopback:

```bash
cp .env.example .env
# Add a provider key to .env only if real execution is required.
docker compose up --build
```

Do not use the example container as an internet-facing production deployment without the controls
listed in `DEPLOYMENT_BOUNDARIES.md`.

For optional no-key local generation, Ollama exposes an OpenAI-compatible API on
loopback. Install `.[openai]`, pull a model with Ollama, and construct
`OpenAICompatibleModelCaller` with `base_url="http://127.0.0.1:11434/v1"`, a
non-secret placeholder key such as `"ollama"`, and
`allow_insecure_loopback=True`. Keep the deterministic mock caller as the default;
never expose an unauthenticated local model server beyond loopback.

With Ollama already running, the included smoke test needs no secret:

```bash
python -m pip install -e '.[openai]'
python examples/ollama_local.py
```

Set `OLLAMA_MODEL` only when choosing a different locally downloaded model.

Send `POST /v1/route` with the same prompt, execution, strategy, optimization, budget, latency,
quality, verifier, and council fields represented by `GatewayRequest`. Operational endpoints are
`GET /health`, `GET /ready`, `GET /v1/config`, `GET /v1/capabilities`, `GET /v1/telemetry`,
`GET /v1/policy/proposal`, and `POST /v1/feedback`; interactive OpenAPI documentation is available
at `/docs`.

Client discovery is available at `GET /v1/capabilities`. It returns configured
routes and non-secret model metadata, including task types, quality estimates,
latency estimates, and capabilities.

## Repository map

- `src/ai_gateway/`: routing, model selection, adaptive execution, telemetry, council, team SDK,
  CLI, and optional adapters.
- `tests/`: offline unit, integration, packaging, scaffold, and example verification.
- `examples/`: runnable routing and specialist-team examples.
- `docs/ROUTING_STRATEGY.md`: gateway comparison, product strategy, and roadmap.
- `docs/LLM_COUNCIL_REVIEW.md`: council source review and activation policy.
- `docs/TEAM_SDK.md`: complete portable-team integration contract.
- `docs/RELEASING.md`: GitHub and PyPI release procedure.
- `.ai/TEAM.md` and `.agents/skills/`: repository-local project team contracts.
- `VALIDATION_PROTOCOL.md`: evaluation plan for routing, budgets, providers, tools, and councils.
- `DEPLOYMENT_BOUNDARIES.md`: controls present today and responsibilities before production use.
- `MODEL_CARD_TEMPLATE.md`, `PROVIDER_CARD_TEMPLATE.md`, and `DATASET_CARD_TEMPLATE.md`: provenance
  records for future integrations and evaluation assets.
- `tools/readiness_agent.py`: deterministic, local-only public-readiness audit.

## Development

```bash
pytest
ruff check .
python scripts/validate_agent_team.py
python tools/readiness_agent.py audit
python scripts/check_release.py --tag v0.1.0
python -m build
python -m twine check dist/*
```

Read `CONTRIBUTING.md` before submitting changes. Report sensitive vulnerabilities according to
`SECURITY.md`, not through a public issue. Community expectations are in `CODE_OF_CONDUCT.md`, and
release history is in `CHANGELOG.md`.

## Production responsibilities

Before production use, integrators should add authentication, tenant isolation, rate limits,
runtime budgets, retries, circuit breakers, telemetry, prompt-injection defenses, strict tool
schemas, execution sandboxing, and a defined data-retention policy.

## License and provenance

Released under the MIT License. See `LICENSE`, `NOTICE`, `CITATION.cff`, and
`THIRD_PARTY_NOTICES.md`. Project decision authority and contribution boundaries are documented in
`GOVERNANCE.md`; optional integration categories are reviewed in
`docs/OPEN_SOURCE_EXTENSIONS.md`.
