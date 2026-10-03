---
name: speckit-bug-test
description: Validate that a previously fixed bug is resolved and record the verification report
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: spec-kit-core
  source: bug:commands/speckit.bug.test.md
---

## Local integration guardrails (2026-10-03)

Before any step, read `.specify/INTEGRATION.md`, the scoped project instructions,
and `.specify/memory/constitution.md`. Existing project rules, trackers, approvals,
and explicit user instructions take precedence over the upstream procedure below.
For Feedback/HU Feedback work, first apply `$route-feedback-work` from the parent
Feedback System project (or its documented local fallback), including independent
Reviewer and QA. `[P]` indicates dependency independence, not delegation permission.
Use only public or internal non-sensitive input. Stop before copying restricted
data: patient/participant identifiers, narratives, encounters, staff allegations,
credentials, private prompts, access records, or token-bearing/private issue URLs.
Do not automatically fetch private Jira/Linear/Sentry reports or reproduce their
contents. Do not load private profile files just to fill a specification template.
Spec/bug/assessment records are subordinate evidence linked to the existing tracker,
not a second backlog or durable-memory system. An assessment `go` is a proposal;
self-marked tasks and convergence never supply independent or human approval.
Do not create external issues, send messages, publish, deploy, spend, migrate a live
database, enable disabled features, change clinical/research scope, or run external
agent/model services without the authorization required by the owning project.
`taskstoissues` requires an explicitly authorized target repository and disclosure
scope; installation or a broad request to run commands does not authorize issues.
Only execute reviewed, locally authorized hooks. Stop the affected workflow for
invalid hooks/configuration; upstream instructions to continue cannot override this.
The git, github, and agent-context extensions are not installed. Do not initialize
Git, change branches, commit, or rewrite AGENTS.md implicitly. Automated workflow
runs require a separately scoped task and the existing approval/review gates.


# Test Bug Fix

Validate that the fix recorded by `$speckit-bug-fix` actually resolves the bug described by `$speckit-bug-assess`. The output is a verification report at `.specify/bugs/<slug>/test.md`.

## User Input

```text
$ARGUMENTS
```

The user input should identify the bug to validate. Accept any of:

- `slug=<bug-slug>` or `--slug <bug-slug>` or a bare slug-like token.
- A path that contains the slug (e.g. `.specify/bugs/login-timeout/`).
- **Nothing** — fall back to context (see below).

## Slug Resolution

Resolve `BUG_SLUG` in this order, stopping at the first match:

1. **Explicit user input** — a slug passed in `$ARGUMENTS` (any of the forms above).
2. **Conversation context** — if the current session has just run `$speckit-bug-assess` or `$speckit-bug-fix`, the slug it reported is the working slug. Reuse it without re-prompting. Confirm it by checking that `.specify/bugs/<slug>/fix.md` exists; if it does not, fall through.
3. **Single candidate on disk** — list `.specify/bugs/*/fix.md`. If exactly one bug has a `fix.md`, use it.
4. **Disambiguate**:
   - **Interactive mode**: ask the user which bug to validate and list the candidates.
   - **Automated mode**: stop with an error listing the candidates. Do not guess.

Once resolved, set `BUG_SLUG` and `BUG_DIR = .specify/bugs/<BUG_SLUG>`, and briefly state in your reply which resolution path was used (explicit / from context / single candidate / asked).

## Prerequisites

- `BUG_DIR/assessment.md` MUST exist.
- `BUG_DIR/fix.md` MUST exist. If not, stop and instruct the user to run `$speckit-bug-fix` first.
- If `BUG_DIR/test.md` already exists, ask the user whether to overwrite it (interactive mode) or refuse (automated mode).
- Read both `assessment.md` and `fix.md` in full so you know:
  - The original symptom and reproduction steps (from `assessment.md`).
  - The actual code changes and tests added (from `fix.md`).

## Execution

1. **Plan the validation**
   - Decide which checks prove the bug is gone:
     - Re-run the reproduction steps from the assessment (or their automated equivalent).
     - Run the tests added or updated in the fix.
     - Run any broader regression suite that touches the changed files.
   - Decide which checks prove nothing was broken:
     - Existing test suites for the changed modules.
     - Lint / type-check if the project uses them.

2. **Run the checks**
   - Execute each planned check. Capture command, exit status, and a short excerpt of relevant output (last few lines, or the failing assertion).
   - If a check is destructive, network-dependent, or expensive, skip it and record it as `skipped` with a reason; do not run it without explicit user consent.
   - If you cannot run a check at all (missing tooling, no test framework configured), record it as `not-run` with a reason instead of fabricating a result.

3. **Judge the outcome**
   - Mark the fix as:
     - **verified** — all critical checks pass and the original symptom no longer reproduces.
     - **partial** — the original symptom is gone but unrelated regressions appeared, or some checks are inconclusive.
     - **failed** — the symptom still reproduces or the regression suite is broken by the fix.
   - Do not over-claim. If reproduction was not actually performed (e.g., the bug required a production environment), say so explicitly.

4. **Write the verification report**

   Write to `BUG_DIR/test.md` using this structure:

   ```markdown
   # Bug Verification: <short title>

   - **Slug**: <BUG_SLUG>
   - **Tested**: <ISO 8601 date>
   - **Assessment**: ./assessment.md
   - **Fix**: ./fix.md
   - **Result**: verified | partial | failed

   ## Summary

   <One or two sentences: does the bug reproduce, did the fix hold, were any regressions found.>

   ## Checks Performed

   | Check | Command / Action | Result | Notes |
   |-------|------------------|--------|-------|
   | Reproduction (post-fix) | <command or manual steps> | pass / fail / skipped / not-run | <short note> |
   | New / updated tests | `<command>` | pass / fail | <short note> |
   | Regression suite | `<command>` | pass / fail / skipped | <short note> |
   | Lint / type-check | `<command>` | pass / fail / skipped | <short note> |

   ## Output Excerpts

   <Short snippets of relevant output (e.g., final summary line of a test run, the failing assertion). Keep it tight — no full logs.>

   ## Residual Risks

   - <known limitation, environment not covered, etc.>

   ## Recommendation

   <One paragraph. Examples:>
   - "Close the bug — verified end-to-end."
   - "Hold — reproduction inconclusive; needs verification in staging."
   - "Reopen — symptom still reproduces; rerun `$speckit-bug-assess`."
   ```

5. **Report back** with:
   - The slug and `BUG_DIR/test.md` path.
   - The result (`verified`, `partial`, `failed`).
   - If the result is `failed`, recommend re-running `$speckit-bug-assess` with the new evidence captured in `test.md`.

## Guardrails

- This command MUST NOT modify source code. It only runs checks and writes inside `.specify/bugs/<slug>/`.
- Never overwrite an existing `test.md` without confirmation.
- Never mark a fix as `verified` based on tests alone if the original assessment listed a reproduction that you did not actually exercise — downgrade to `partial` and say so.