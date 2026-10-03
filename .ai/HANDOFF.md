# Current handoff

## Runtime controls — implemented locally 3 October 2026

Active role: Documentation handoff after Builder implementation and self-review.
Completed the pending local runtime controls in the existing repository:
durable SQLite charge reservations/reconciliation; shared execution deadlines,
call/prompt/output caps; process-local circuit breaker; optional bearer-to-container
tenant access with isolated telemetry/feedback and provider override prevention.
Added runnable offline example and reconciled entry/deployment documentation.
See [configuration and limitations](../docs/RUNTIME_CONTROLS.md).

Validation: 226 tests on Python 3.11.16 and 3.14.7; Ruff, diff whitespace,
12-role validator and deterministic readiness audit pass. Source/wheel build,
Twine metadata and isolated installed-wheel core smoke pass. Focused cases cover
parallel reservation, restart, unknown charges, overbilling, late responses,
half-open circuits, tenant isolation and bypass rejection. File review ledger
records builder self-review and exclusions; no independent certification claimed.

Remaining: representative authorized evaluation data and live provider contracts;
hard cancellation, distributed quotas, audited billing recovery and hosted identity
lifecycle before commercial guarantees. Unknown provider charges remain reserved
until explicit reconciliation, including successful calls from the bundled SDK
adapter because it reports tokens but no confirmed dollar charge. Controls depend
on operator-verified exposure bounds and provider support; no hard SLO is claimed.

Next owner: maintainer / independent Reviewer, QA and Safety/Evaluation, then pilot
evaluation owner for dataset and provider validation. No approval is needed to
inspect these local artifacts. Future GitHub publication, paid evaluation and
deployment require their existing explicit authorization. No provider calls,
publication, deployment or background service occurred; other user changes remain.


## Routing redesign — implemented locally 3 October 2026

Owner / active gear: Builder validation and Documentation handoff.
Implemented in the existing GitHub checkout; no new repository was needed.
[Implementation, research and migration guide](../docs/ROUTER_REDESIGN.md).

Completed: versioned fixed-cohort quality gate with abstention, capability/p95
filters, paired offline replay, shared council/direct usage accounting, bounded
failure fallback, request/deployment identity fixes, accurate cost provenance,
explicit quality labels, final-stage feedback and finite input validation.
SDK retries disabled; adaptive ranking requires explicit operator opt-in.
No provider calls, public release or hosted changes were performed. Existing
company and concurrent Spec Kit edits were preserved.

Validation results are recorded in the implementation guide. The later runtime
completion above supersedes this pass's pending reservation/deadline/tenant-access
work. Real evaluation data and commercial deployment controls remain separate.
This session performed builder self-review, not independent certification.

Next owner: maintainer / independent Reviewer, QA and Safety/Evaluation for release
review, then the pilot evaluation owner for representative workload data. Human
authorization is needed before any later GitHub push, paid evaluation or deployment.
There is no ongoing implementation task or background service from this handoff.

## Model-routing company design — completed 3 October 2026

Local research, architecture and all 12 company role contracts are complete.
Deliverable: [EquiRoute company design](../docs/company/README.md).
Validation: [record and limitations](../docs/company/VALIDATION.md); 165 tests
passed, Ruff and both skill validators passed, and 39 local links resolved.
Active role: Documentation / local release preparation. No production routing
changes, provider calls, deployment or independent certification are claimed.
Next owner: Manu for market/pilot constraints, then Planner and Engineer for an
explicit implementation task. Spending, data access and external release retain
their existing approval boundaries. There is no ongoing task or background run.

The prior release handoff below is preserved for the maintainer.

## Open-source tool readiness — 10 August 2026

TASK: Make the remaining public repository a reliable, discoverable, and reusable
open-source tool.

OUTCOME: `manufaujdar/ai-routing-gateway` should install cleanly, expose a clear
CLI/library/API entry point, pass CI, and give new users a verified first-run path.

USER OR BENEFICIARY: Open-source users integrating deterministic AI routing and
safe specialist-team planning.

IN SCOPE: Fix the failing CI dependency contract; add small user-facing CLI
discoverability improvements; add PEP 561 typing metadata; reconcile README and
changelog; run independent QA and release preflight.

OUT OF SCOPE: Provider calls becoming mandatory, production deployment, PyPI
publishing, GitHub release creation, secrets, or changes to core routing policy.

OWNER / ACTIVE ROLE: Release after builder and independent QA.

INPUTS AND SOURCES: Existing README, source, tests, GitHub Actions logs, and the
project's deterministic/offline invariants in `AGENTS.md` and `.ai/TEAM.md`.

ACCEPTANCE CRITERIA:

- CI installs every optional dependency required by the tests and passes on the
  declared Python matrix.
- `ai-gateway --version` and `ai-gateway-team --version` work after installation.
- The installed package advertises its typing marker and remains dependency-free
  for core routing.
- A clean temporary environment can install and run the documented quickstart.
- Existing routing, safety, API, team, and scaffold behavior remains compatible.
- `pytest`, `ruff check .`, package build, Twine metadata checks, and team
  validation pass.

RISKS / APPROVAL GATES: No external provider calls or public release actions.
GitHub push/release/PyPI publication remain separate human-authorized release
actions.

VALIDATION: Focused CLI and packaging tests, full pytest, Ruff, team validation,
clean-install smoke tests, wheel-content inspection, and GitHub Actions re-run
after publication if authorized.

DELIVERABLE LOCATION: Repository root, `src/ai_gateway/`, `tests/`, `.github/`,
`README.md`, and `CHANGELOG.md`.

STATUS: READY FOR AUTHORIZED RELEASE — local implementation, QA, and packaging gates passed.

Previous verified baseline: 132 tests pass in a clean temporary environment with
the `dev`, `api`, and `openai` extras. The checked-in `.venv` is stale and points
to an old absolute path; it is ignored generated state and is not being edited.

## Gate result

The local change adds the missing API extra to CI and release verification, adds
CLI version flags, adds PEP 561 typing metadata, updates the quickstart, and adds
regression coverage. Independent verification passed: 135 tests, Ruff, 12-skill
validation, wheel build, Twine metadata, wheel marker inspection, and a fresh
non-editable install with CLI and decision-only smoke tests.

Release completed on branch `agent/open-source-tool-readiness` at commit
`179a2f4`, with draft PR #8 opened at
https://github.com/manufaujdar/ai-routing-gateway/pull/8. Remote CI run
31374280062 passed for the distribution build and Python 3.11, 3.12, 3.13, and
3.14. The PR remains intentionally draft and has not been merged.

NEXT OWNER: Manu / maintainer.
NEXT ACTION: Review and merge draft PR #8 when satisfied with the public release
scope; no further implementation or CI repair is currently required.


## Completed local tooling — Spec Kit (2026-10-03)

Pinned v1.1.0 core + bug/assess Codex skills installed. Read .specify/INTEGRATION.md;
existing tracker/role/privacy/human gates retain authority. Hashes, 18 commands,
links, JSON, Bash and local-root checks pass; disposable feature/plan/tasks and
external/traversal/symlink negative checks pass. No application/runtime or hosted
change. Active role: local tooling release/handoff. Next owner: selected project
product/engineering owner for an authorized task. Existing approval gates apply.
