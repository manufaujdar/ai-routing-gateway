# Documentation index

AI Routing Gateway is an embeddable Python decision plane with a dependency-free
core, optional transports and adapters, and gated specialist-agent workflows.
The default examples and tests remain deterministic and offline.

## Find the right document

| Task | Start here | Continue with |
| --- | --- | --- |
| Install and make a first decision | [README](../README.md) | [Human start page](../START_HERE.txt), [examples](../examples/) |
| Find a component or public interface | [Architecture](architecture.md) | [Technical overview](technical-overview.md) |
| Evaluate routing strategy | [Routing strategy](ROUTING_STRATEGY.md) | [Validation protocol](../VALIDATION_PROTOCOL.md), [council review](LLM_COUNCIL_REVIEW.md) |
| Integrate a specialist team | [Team SDK](TEAM_SDK.md) | [Agent guide](../AGENTS.md), [repository team](../.ai/TEAM.md) |
| Add a provider, model or dataset | [Extension review](OPEN_SOURCE_EXTENSIONS.md) | [Provider card](../PROVIDER_CARD_TEMPLATE.md), [model card](../MODEL_CARD_TEMPLATE.md), [dataset card](../DATASET_CARD_TEMPLATE.md) |
| Assess a hosted integration | [Deployment boundaries](../DEPLOYMENT_BOUNDARIES.md) | [Security reporting](../SECURITY.md), [governance](../GOVERNANCE.md) |
| Contribute, verify or release | [Contributing](../CONTRIBUTING.md) | [Engineering checks](../TOOLING.md), [release procedure](RELEASING.md), [changelog](../CHANGELOG.md) |
| Check licensing or get help | [MIT license](../LICENSE) | [Third-party notices](../THIRD_PARTY_NOTICES.md), [notice](../NOTICE), [citation](../CITATION.cff), [support](../SUPPORT.md) |

Library, CLI, optional API and provider execution have different boundaries.
Use the README and deployment document for the scope of the interface you are
integrating. A passing offline check does not establish live-provider quality,
production tenant controls or release approval.

## Repository organisation

| Location | Owns |
| --- | --- |
| `src/ai_gateway/` | Decision pipeline, team SDK, adapters, CLI and optional HTTP/UI transport |
| `tests/` | Offline unit, integration, packaging and scaffold contracts |
| `examples/` | Runnable routing and specialist-team examples |
| `docs/` | Architecture, public-interface maps, strategy and release instructions |
| `requirements/`, `pyproject.toml` | Package and optional integration requirements |
| `scripts/`, `tools/`, `.github/` | Local validation, release preflight, pinned tooling and CI |
| `.ai/`, `.agents/`, `AGENTS.md` | Current task, approved memory and project-team contracts |
| Root policy and card files | Stable deployment, validation, contribution, provenance and integration entry points |

Put new explanatory design or validation notes in `docs/` and link them here.
Keep runnable demonstrations in `examples/`, implementation in `src/ai_gateway/`,
and verification fixtures in `tests/`. Preserve existing entry-point paths when
organising files; update inbound links when a move is necessary. Keep generated
packages, provider keys, private prompts and production traces out of source docs.

## Reference patterns

LiteLLM and OpenRouter inform transport/provider separation; RouteLLM and Not
Diamond inform routing research; OpenTelemetry informs observability boundaries.
They are comparison references, not required core dependencies.

