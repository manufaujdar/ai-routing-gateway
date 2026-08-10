# Contributing

Thank you for helping improve AI Routing Gateway. Small, focused changes with deterministic tests
are easiest to review.

## Development setup

```bash
git clone <your-fork-url>
cd <repository-directory>
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,api,openai]'
```

Provider credentials are optional and must never be committed. The core test suite is offline.

## Before opening a pull request

```bash
pytest
ruff check .
python scripts/validate_agent_team.py
python tools/readiness_agent.py audit
python -m build
python -m twine check dist/*
```

When changing routing, include assertions for the observable route, model, tools, confidence, and
reasons. When changing team workflows, preserve independent Builder, Reviewer, QA, and Safety roles.

## Pull requests

- Explain the user-visible outcome and why the change is needed.
- Keep evaluation, selection, council planning, registration, and execution separate.
- Add focused tests for success, rejection, and failure behavior.
- Update README, examples, and changelog when an interface changes.
- Do not include provider keys, private prompts, production traces, or generated build artifacts.
- Complete the relevant model, provider, or dataset card for new integrations and include exact
  source, version, license/terms, data handling, validation evidence, and rollback behavior.

By contributing, you agree that your contribution is licensed under the repository's MIT License
and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
