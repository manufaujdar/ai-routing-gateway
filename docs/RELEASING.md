# Release guide

This repository is configured to build and test every pull request and to publish a Python package
only after a GitHub Release is published.

## One-time GitHub setup

1. Create the GitHub repository and push the reviewed `main` branch.
2. Enable private vulnerability reporting under **Settings > Security**.
3. Enable branch protection for `main`, require pull requests, and require the CI test and package
   jobs to pass.
4. Create a protected GitHub Environment named `pypi` and require manual approval.
5. On PyPI, create a pending trusted publisher for package `ai-routing-gateway`, the exact GitHub
   owner/repository, workflow `.github/workflows/publish.yml`, and environment `pypi`.
6. Confirm that the distribution name is available on PyPI. If it changes, update `pyproject.toml`,
   the publish workflow environment URL, README installation commands, and release checks.
7. Configure a private maintainer channel for conduct reports and replace the temporary guidance in
   `CODE_OF_CONDUCT.md` with that exact channel before inviting outside contributors.

Trusted publishing uses short-lived OpenID Connect credentials; do not add a long-lived PyPI token
to repository secrets.

The publish workflow verifies that the release commit is contained in `origin/main` and constructs
the publishable artifact with `requirements/release.txt`, exact hashes, and build isolation disabled.
Update the lock intentionally when release tooling changes:

```bash
python -m pip install pip-tools==7.6.0
pip-compile --generate-hashes --resolver=backtracking \
  --output-file=requirements/release.txt requirements/release.in
```

## Release procedure

1. Move completed entries from `Unreleased` into a dated version in `CHANGELOG.md`.
2. Update `__version__` in `src/ai_gateway/_version.py` and examples/tests that assert the version.
3. Run:

   ```bash
   pytest
   ruff check .
   python scripts/validate_agent_team.py
   python scripts/check_release.py --tag vX.Y.Z \
     --commit "$(git rev-parse vX.Y.Z)" --main-ref main
   python -m build
   python -m twine check dist/*
   ```

4. Merge the reviewed release change to `main`.
5. Create and publish a GitHub Release using tag `vX.Y.Z` on that commit.
6. Approve the protected `pypi` environment deployment after the build job succeeds.
7. Install the published wheel in a clean environment and run both CLI smoke tests.

## Rollback

PyPI releases cannot be replaced. If a release is defective, yank the affected version, document the
reason, fix forward with a new patch version, and link the GitHub advisory or issue when appropriate.
Never reuse or move a published version tag.
