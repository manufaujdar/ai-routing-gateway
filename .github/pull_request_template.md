## Outcome

Describe the user-visible or maintainer-visible result.

## Changes

-

## Verification

- [ ] Focused tests added or updated
- [ ] `pytest`
- [ ] `ruff check .`
- [ ] `python scripts/validate_agent_team.py` when team files changed
- [ ] `python tools/readiness_agent.py audit`
- [ ] Documentation and changelog updated when behavior changed

## Safety and compatibility

- [ ] No credentials, private prompts, or production traces are included
- [ ] New providers, tools, models, and evaluation data have provenance and terms documented
- [ ] Routing/model/tool/confidence/reasons remain observable where affected
- [ ] External actions remain explicitly authorized
- [ ] Production-boundary, privacy, and rollback impacts are documented
- [ ] Breaking changes and migration steps are documented
