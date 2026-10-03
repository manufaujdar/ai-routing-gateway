# Spec Kit integration: AI gateway

Installed 2026-10-03. GitHub Spec Kit v1.1.0, MIT, commit `f1d3a4f8337ebbd3ae22760a9c12e3352b93a175`.
Source: https://github.com/github/spec-kit/tree/f1d3a4f8337ebbd3ae22760a9c12e3352b93a175
CLI is an isolated uv tool, not an application dependency. Codex skills are in
`.agents/skills/speckit-*/SKILL.md`; shared scripts/templates are in `.specify/`.
Core, bug v1.0.0 and assess v1.0.1 are installed; git/github/agent-context are absent.
MIT attribution is retained in `UPSTREAM_LICENSE.txt`. Local modifications: command
guardrail preamble, linked constitution, this guide, hooks auto-execution disabled,
and feature-directory containment checks in common.sh/create-new-feature.sh.

## Project authority

- `AGENTS.md`
- `START_HERE.txt`
- `README.md`
- `.ai/CONTEXT.md`
- `.ai/MEMORY.md`
- `.ai/TEAM.md`

Use the existing project rules and role gears. This is internal development tooling; it does not change runtime behavior, data access, scientific conclusions or release authority.

Tracker: `.ai/HANDOFF.md`. Link every new feature/bug/assessment to its existing
task or decision. Do not turn `specs/*/tasks.md` into a parallel project backlog.
Keep evidence in the owning project's existing records. Read the nearest AGENTS.md
before changing any subdirectory. Run commands from this project directory; use
`SPECIFY_INIT_DIR` only with an explicitly selected local project root.
Clear inherited SPECIFY_INIT_DIR/SPECIFY_FEATURE_DIRECTORY overrides before changing
projects. Feature directories must resolve beneath this project's specs/ with no
symlink traversal. Local guards reject external, traversal and symlink feature paths
before plan/task writes and before persisting an explicit feature override.

## Use in Codex chat

For a bounded feature: `$speckit-specify <outcome and tracker reference>`, then
`$speckit-clarify` if needed, `$speckit-plan`, `$speckit-checklist`, `$speckit-tasks`,
`$speckit-analyze`, `$speckit-implement`, `$speckit-converge`. The constitution is
already linked to existing rules; `$speckit-constitution` may maintain those links
without inventing principles or changing approved requirements.

For a repair: `$speckit-bug-assess <synthetic symptom> slug=<name>`,
`$speckit-bug-fix slug=<name>`, `$speckit-bug-test slug=<name>`.

For an idea: `$speckit-assess-intake <idea> slug=<name>`, then
`$speckit-assess-research`, `$speckit-assess-define`, `$speckit-assess-shape`,
`$speckit-assess-decide`, each with the same slug. Research follows local evidence
rules. A go verdict is advisory and does not authorize implementation or release.

`$speckit-taskstoissues` creates external GitHub records and is held until explicit
repository/disclosure authorization. These `$speckit-*` invocations are agent skills,
not shell commands. Skill presence does not prove execution or model correctness.

## Terminal checks and maintenance

Run `specify version`, `specify integration status`, `specify extension list`,
`specify artifact list --json`, and `specify workflow list` to inspect the installation.
Validation for this tooling change: registry parsing, all 18 command definitions,
local-root resolution, script syntax, feature/plan/task smoke in a disposable fixture,
and the owning project's instruction validator where present.
Application verification for later changes: Run the relevant commands already required by AGENTS.md. For this tooling-only change, validate linked files and installed scripts/registries; application tests are required if application behavior later changes.

An in-place upstream upgrade can replace local guardrails. Do not run a forced
upgrade over these files; stage the selected new release, review it, and compare
against `.specify/adoption.json` before explicitly merging changes. The additive
installer fails on conflicting paths. Rollback removes only unchanged files listed
in adoption.json, after checking hashes; retain any new specs and user edits.
This installation has not executed a paid/provider workflow or deployed anything.
