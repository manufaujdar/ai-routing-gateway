# Privacy and data boundary

Status: source distribution and offline library use only. This file is a
technical privacy boundary, not a jurisdiction-specific privacy policy for a
hosted service.

## Current distribution

The core library is deterministic, dependency-free, and offline by default. It
does not create user accounts, a hosted service, advertising profiles, or a
remote data store. Optional provider, tool, API, and telemetry adapters may
process prompts, outputs, traces, identifiers, or usage data according to the
integrating application's configuration and the selected provider's terms.

Do not commit or use real credentials, private prompts, personal data, customer
data, production traces, proprietary tool schemas, unlicensed datasets, or
model weights in the repository or its examples.

## Deployment responsibility

An integrator that enables a provider, tool, API, telemetry sink, database, or
hosted UI is responsible for the resulting data flow. Before processing
personal, health, confidential, or regulated information, document controller
and processor roles, lawful basis or authorization, notice and consent where
applicable, provider retention/training terms and regions, access controls,
encryption, retention/deletion, incident response, and required contracts.
The integrator must publish its own privacy notice and terms of service; this
repository does not provide them.

## Legal and compliance boundary

The MIT `LICENSE` governs the source code. It is not a privacy policy, security
certification, HIPAA/DPDP/GDPR compliance statement, or provider endorsement.
See `NOTICE`, `THIRD_PARTY_NOTICES.md`, `SECURITY.md`, and
`DEPLOYMENT_BOUNDARIES.md` for the remaining boundaries.

Reviewed: 2026-08-14.
