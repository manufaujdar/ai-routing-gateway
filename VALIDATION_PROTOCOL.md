# Routing and integration validation protocol

This document is a validation scaffold, not evidence that a deployment is safe
or production-ready. Use synthetic or explicitly approved, sanitized prompts in
the public test suite.

## Routing policy

1. Freeze the evaluator version, policy configuration, route registry, model
   catalog, and tool allow-list for an evaluation run.
2. Build a labeled prompt set covering every supported task type plus ambiguous,
   multilingual, adversarial, empty, malformed, and high-risk inputs.
3. Report route accuracy, unsafe false negatives, unnecessary blocks, fallback
   rate, and confidence calibration. Review results by language, prompt length,
   task type, and risk category.
4. Test that disallowed routes and models fail closed and that decision-only
   mode never invokes a handler.

## Model selection and budgets

1. Record catalog source, retrieval time, model identifier, pricing unit,
   context limits, region, capabilities, and availability assumptions.
2. Compare estimated tokens, cost, and latency with provider invoices and
   measured telemetry. Do not treat fixture metadata as a live guarantee.
3. Test exact-boundary, zero-budget, unavailable-model, timeout, rate-limit, and
   partial-response cases. Hard constraints must not silently become preferences.
4. Revalidate after any provider, tokenizer, pricing, or selection-weight change.
5. Validate each execution strategy independently: cascade escalation precision, verifier false
   acceptance/rejection, self-consistency agreement, total call count, and end-to-end budgets.
6. Replay every adaptive policy proposal on a frozen evaluation set. Require statistically useful
   sample sizes, explicit approval, canary limits, and automatic rollback thresholds before use.

## Tools, adapters, and councils

1. Validate tool inputs and outputs against explicit schemas and test injection,
   path traversal, SSRF, oversized payload, secret exposure, and destructive
   action cases relevant to each tool.
2. Confirm provider TLS, timeout, redaction, retention, and error-normalization
   behavior with a staging account containing no production data.
3. Verify that council eligibility, cost ceilings, member independence, failure
   handling, and synthesis provenance match the documented policy.
4. Require human review for consequential actions; peer agreement is not proof.

## Release evidence

Archive the code revision, configuration hashes, sanitized evaluation-set
version, metric report, known failures, reviewer, approval, and rollback plan.
Run `pytest`, `ruff check .`, `python scripts/validate_agent_team.py`,
`python tools/readiness_agent.py audit`, and the package checks in
[docs/RELEASING.md](docs/RELEASING.md).
