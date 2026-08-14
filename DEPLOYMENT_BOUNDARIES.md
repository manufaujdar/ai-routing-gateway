# Deployment and data boundaries

AI Routing Gateway is an integration framework, not a managed gateway service.
The default core evaluates requests locally and uses mock handlers. Installing
the package does not create authentication, isolation, billing enforcement,
network egress controls, or safe tool execution.

## Implemented boundaries

- Deterministic evaluation and model selection can run without network access.
- Provider calls are optional and isolated behind adapters.
- Decision-only mode avoids handler execution.
- Routes, selected models, tools, confidence, candidates, council plans, execution strategies, and
  reasons remain observable.
- Direct adaptive model execution records bounded in-memory deployment outcomes without prompt or
  response content; policy recommendations are never promoted automatically.
- High-risk keyword matches route to a blocked handler in the baseline policy.
- External release actions in team workflows require an exact boolean approval.
- Non-HTTPS provider endpoints are rejected except for explicitly enabled
  literal loopback development endpoints.

These are framework controls, not a comprehensive security or safety system.
Keyword rules are bypassable, catalog prices are estimates, and mock handlers
do not prove that a production tool is safe.

## Required before production use

1. Define tenants, users, data classes, allowed routes, allowed tools, retention,
   deletion, audit, incident response, and regional processing requirements.
2. Authenticate every request and enforce tenant isolation, least privilege,
   quotas, rate limits, and runtime cost ceilings outside model-generated text.
3. Validate every tool argument against a strict schema; sandbox execution and
   require explicit approval for destructive or externally visible actions.
4. Treat prompts, attachments, tool results, and traces as potentially sensitive.
   Redact logs, encrypt transport and storage, and document each provider's data
   use and retention terms.
5. Replace fixture catalog values with versioned provider metadata and measured
   telemetry. Fail closed when price, capability, context limit, or availability
   cannot be established for a hard constraint.
6. Persist telemetry in a tenant-isolated store only after defining retention and deletion; audit
   feedback integrity and require replay, approval, canary, rollback, and drift gates for changes.
7. Add timeouts, bounded retries, circuit breakers, idempotency, concurrency
   limits, abuse monitoring, and tested rollback behavior.
8. Evaluate prompt injection, data exfiltration, unsafe tool use, cross-tenant
   leakage, model fallback, and partial provider failure before launch.

Regulatory and contractual compliance depends on the deploying organization,
jurisdiction, data, providers, and intended use. This repository does not claim
SOC 2, ISO 27001, HIPAA, GDPR, or other compliance certification.
