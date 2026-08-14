# Open-source integration plan

Reviewed 2026-08-10. These are optional integration categories, not bundled
runtime dependencies. Exact releases and notices must be reviewed before use.

| Integration | Proposed use | Current boundary |
|---|---|---|
| OpenAI Python SDK | Optional client for OpenAI-compatible endpoints | Lazy optional dependency behind `OpenAICompatibleModelCaller`; provider terms and data handling remain deployment responsibilities. |
| Ollama | Loopback-only local generation example | Not started or installed by this project; insecure HTTP is permitted only with explicit loopback opt-in. |
| OpenRouter or compatible gateways | Multi-provider model access | Configure externally and document model IDs, prices, retention, regions, fallbacks, and provider-specific terms. |
| LangGraph, OpenHands, or other agent runtimes | Host application execution of team roles | Not core dependencies; require sandbox, authorization, state, and external-action review. |
| Search, browser, code, and filesystem tools | Implement `tool.*` routes | Mock-only in the default container; production handlers need schemas, allow-lists, isolation, and audit. |
| OpenTelemetry-compatible instrumentation | Operational latency, failure, and cost signals | Future adapter; prompts and tool payloads must be redacted or excluded by default. |

Recommended order:

1. Validate deterministic route and model-selection behavior on a versioned,
   sanitized evaluation set.
2. Add one provider adapter with documented data handling, strict timeouts, and
   measured cost/latency reconciliation.
3. Add one read-only tool with schema validation and injection tests.
4. Add authenticated multi-tenant controls before any shared deployment.
5. Enable consequential or write-capable tools only after sandboxing, explicit
   approval, audit, and rollback are independently tested.
