from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "readiness_agent.py"
SPEC = importlib.util.spec_from_file_location("readiness_agent", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
READINESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = READINESS
SPEC.loader.exec_module(READINESS)


def test_repository_passes_deterministic_readiness_audit() -> None:
    result = READINESS.audit(ROOT)
    assert result["external_model_calls"] is False
    assert result["findings"] == []
    assert result["ready"] is True


def test_missing_public_artifacts_fail_closed(tmp_path: Path) -> None:
    result = READINESS.audit(tmp_path)
    assert result["ready"] is False
    assert any(finding["area"] == "governance" for finding in result["findings"])
