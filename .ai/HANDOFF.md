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
