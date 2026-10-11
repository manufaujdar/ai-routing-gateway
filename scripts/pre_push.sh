#!/usr/bin/env bash
# Existing quality checks followed by bounded synthetic/tooling gates.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest
ruff check .
python scripts/validate_agent_team.py
python tools/readiness_agent.py audit --json
python -m build
python -m twine check dist/*
python -m unittest discover -s tools -p 'test_*.py'
python -m pip check
python -m pip_audit --local
python scripts/browser_regressions.py
python scripts/engineering_checks.py "$@"
