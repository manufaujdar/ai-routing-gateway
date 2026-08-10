# Security policy

## Supported versions

Until the first stable release, security fixes are provided for the latest published `0.x` version
only.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability
reporting feature under the repository's **Security** tab. Include affected versions, impact,
reproduction steps, and any suggested mitigation, but do not include real credentials, private
prompts, or production traces.

Maintainers should acknowledge a complete report within seven days, coordinate validation and a
fix privately, and publish an advisory after affected users have a reasonable upgrade path. Exact
timelines depend on severity and reproducibility.

## Security boundaries

The deterministic core performs no provider calls. Provider credentials belong in environment or
secret-management systems. Integrators are responsible for authentication, tenant isolation,
tool sandboxing, rate limits, and production data-retention policy.

Prompt content, attachments, tool results, model outputs, and routing traces may contain personal,
confidential, regulated, or adversarial data. Do not assume that removing obvious identifiers makes
a trace safe to publish. A production deployment must document provider retention and training-use
terms, processing regions, log redaction, access controls, deletion, incident response, and tool
authorization. See [DEPLOYMENT_BOUNDARIES.md](DEPLOYMENT_BOUNDARIES.md).
