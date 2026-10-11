# Current handoff

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

## Audit implementation — 11 October 2026

- Task: Request settings and native result navigation; user authorized implementation and Git push from the portfolio UX/settings audit.
- Scope/files: src/ai_gateway/static/{index.html,app.js,styles.css}.
- Result: Document-owned result scroll with named keyboard-scrollable JSON; contextual strategy fields; page-only future-history checkbox; confirmation/error handling for browser-history clearing. Off-period decisions retain a per-entry exclusion so enabling saves later cannot persist them. Routing, execution switches and provider-key contract unchanged.
- Verification: 21 API/production-boundary tests; actual-source browser contextual fields, native result owner and reduced motion; Off→request→On→request storage exclusion regression; Ruff and diff check pass.
- Source state: separate clean checkout from the verified current GitHub branch; original dirty checkout preserved. No dirty baseline incorporated.
- Active gear: Review/QA to authorized Git publication; one mutating UI owner and independent root review.
- Limits/next owner: app owner for physical-device, screen-reader and other-browser checks. No provider runs, real data, deployment or model/clinical release. Existing governed release gates remain.

## Main integration — 11 October 2026

Task-only UX/settings changes adapted to current main, retaining its backend and existing history. User authorized main publication. Validation and remote receipt are recorded in the portfolio task; no deployment/provider or regulated release is claimed.

## Main-push engineering tooling — 11 October 2026

User authorized suitable tools and main-only publication. Active gear: engineering/build followed by independent Review and QA. Scope: repo-owned quality commands, workflow/docs/secret gates and synthetic browser regressions; no runtime policy, clinical/provider data, model run, deployment or hook replacement. Acceptance: native suites and new gates pass, representative failure paths reject, root review resolves findings, exact main push and hosted CI are verified. Tool pins/source/limitations are in TOOLING.md; transient evidence is in the portfolio tooling receipt. Next owner after publication: maintainer for governed release and physical-device approval.
