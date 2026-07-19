from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("example", ["basic_routing.py", "team_workflow.py"])
def test_example_runs(example: str) -> None:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    source_path = str(ROOT / "src")
    environment["PYTHONPATH"] = (
        source_path
        if not existing_pythonpath
        else source_path + os.pathsep + existing_pythonpath
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / example)],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
