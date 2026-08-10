# Governance

AI Routing Gateway is an early-stage open-source project maintained by Manu
Faujdar.

## Decision authority

The maintainer reviews contributions, releases, routing-policy changes,
dependency and provenance changes, and security boundaries. A change may be
rejected when it weakens explainability, offline behavior, privacy, tool safety,
licensing certainty, or independent review gates.

Project roles under `.agents/skills/` help structure work; they are not voting
members, autonomous maintainers, or substitutes for accountable human review.
Generated output and council agreement are evidence to inspect, not authority.

## Contributions

Contributions should be focused, tested, documented, and attributable. Changes
to evaluation, selection, council policy, or execution must state the affected
route, model, tool, confidence, reasons, cost boundary, and failure behavior.
See [CONTRIBUTING.md](CONTRIBUTING.md).

Do not submit credentials, private prompts, personal data, customer data,
production traces, proprietary tool schemas, unlicensed datasets, or model
weights. Third-party assets require an explicit source, version, license, and
redistribution review.

## Releases

Releases require passing CI, a clean package build, validated metadata, an
updated changelog, and review of unresolved safety and compatibility risks.
Publishing to GitHub or PyPI remains an explicitly authorized maintainer action.
A version tag does not establish production readiness, provider accuracy, or
security compliance.
