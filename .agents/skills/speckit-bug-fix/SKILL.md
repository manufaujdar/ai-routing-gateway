---
name: speckit-bug-fix
description: Apply the remediation from a bug assessment and record what was changed
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: spec-kit-core
  source: bug:commands/speckit.bug.fix.md
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


# Fix Bug

Apply the remediation that was proposed by `$speckit-bug-assess` and record the changes in a fix report at `.specify/bugs/<slug>/fix.md`. This command is **only** valid after an assessment exists for the given slug.

## User Input

```text
$ARGUMENTS
```

The user input should identify the bug to fix. Accept any of:

- `slug=<bug-slug>` or `--slug <bug-slug>` or just a bare slug-like token.
- A path that contains the slug (e.g. `.specify/bugs/login-timeout/`).
- **Nothing** — fall back to context (see below).

## Slug Resolution

Resolve `BUG_SLUG` in this order, stopping at the first match:

1. **Explicit user input** — a slug passed in `$ARGUMENTS` (any of the forms above).
2. **Conversation context** — if the current session has just run `$speckit-bug-assess`, the slug it reported is the working slug. Reuse it without re-prompting. Confirm it by checking that `.specify/bugs/<slug>/assessment.md` exists; if it does not, fall through.
3. **Single candidate on disk** — list `.specify/bugs/*/assessment.md`. If exactly one matching `assessment.md` is found, use the slug from its parent directory.
4. **Disambiguate**:
   - **Interactive mode**: ask the user which bug to fix and list the candidates.
   - **Automated mode**: stop with an error listing the candidates. Do not guess.

Once resolved, set `BUG_SLUG` and `BUG_DIR = .specify/bugs/<BUG_SLUG>`, and briefly state in your reply which resolution path was used (explicit / from context / single candidate / asked).

## Prerequisites

- `BUG_DIR/assessment.md` MUST exist. If it does not, stop and instruct the user to run `$speckit-bug-assess` first.
- If `BUG_DIR/fix.md` already exists, ask the user whether to overwrite it before continuing (interactive mode) or refuse (automated mode).
- Read `BUG_DIR/assessment.md` in full. Treat its **Proposed Remediation**, **Files likely to change**, **Tests to add or update**, and **Risks & Considerations** sections as the contract for this command.

## Execution

1. **Confirm the plan**
   - Restate, in 3–6 bullets, what you are about to change and where, based on the assessment.
   - If the assessment's verdict is `invalid`, stop — there is nothing to fix. Tell the user and exit.
   - If the verdict is `likely valid, needs reproduction` and there are unresolved `[NEEDS CLARIFICATION]` items, flag them and ask the user whether to proceed in interactive mode, or stop in automated mode.

2. **Apply the remediation**
   - Make the code changes described by the preferred remediation. Stay within the files listed by the assessment unless newly discovered evidence requires expanding scope (in which case, log the expansion explicitly in the report).
   - Add or update the tests called out in the assessment so the bug cannot regress silently.
   - Keep the change minimal — do not refactor unrelated code, do not introduce dependencies that the assessment did not call for.
   - If you discover the assessment was wrong (the proposed fix does not work, the root cause is elsewhere), STOP modifying code, document the new finding in the fix report under **Deviations from Assessment**, and recommend re-running `$speckit-bug-assess`.

3. **Run local checks**
   - If the project has obvious test commands (e.g., `pytest`, `npm test`, `cargo test`), run the tests that exercise the changed paths. Capture pass/fail and key output.
   - Do not run destructive or network-dependent suites without the user's consent.

4. **Write the fix report**

   Write to `BUG_DIR/fix.md` using this structure:

   ```markdown
   # Bug Fix: <short title>

   - **Slug**: <BUG_SLUG>
   - **Fixed**: <ISO 8601 date>
   - **Assessment**: ./assessment.md
   - **Status**: applied | partial | not-applied

   ## Summary

   <One or two sentences describing what was changed and why.>

   ## Changes

   | File | Change | Notes |
   |------|--------|-------|
   | `path/to/file.py` | <added / modified / removed> | <short note> |
   | `path/to/test_file.py` | added test | <short note> |

   ## Diff Highlights (optional)

   <Short, illustrative snippets of the most important hunks — not a full diff dump.>

   ## Tests Added or Updated

   - `path/to/test_file.py::test_name` — <what it pins down>

   ## Local Verification

   - Commands run: `<command>` → <result, brief>
   - Manual checks: <what was verified by hand, if anything>

   ## Deviations from Assessment

   <Empty if none. Otherwise, list any places where the actual fix departed from the proposed remediation and why.>

   ## Follow-ups

   - <suggested cleanup, monitoring, doc update, etc.>
   ```

5. **Report back** with:
   - The slug and `BUG_DIR/fix.md` path.
   - The status (`applied`, `partial`, `not-applied`).
   - The next suggested step: `$speckit-bug-test slug=<BUG_SLUG>`.

## Guardrails

- Never modify files outside the project workspace.
- Never edit `assessment.md` — it is the contract you are working against. Record disagreements in `fix.md` under **Deviations from Assessment**.
- Never delete files unless the assessment explicitly required it.
- Never overwrite an existing `fix.md` without confirmation.