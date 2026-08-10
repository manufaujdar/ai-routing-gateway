#!/usr/bin/env python3
"""Deterministic, local-only repository readiness audit.

This tool reads project files and emits findings. It makes no network or model
calls, does not inspect secrets, and does not edit the repository.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    area: str
    title: str
    next_action: str


REQUIRED_PUBLIC_FILES = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "CODE_OF_CONDUCT.md",
    "DEPLOYMENT_BOUNDARIES.md",
    "VALIDATION_PROTOCOL.md",
    "MODEL_CARD_TEMPLATE.md",
    "PROVIDER_CARD_TEMPLATE.md",
    "DATASET_CARD_TEMPLATE.md",
    "THIRD_PARTY_NOTICES.md",
)


def audit(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    findings: list[Finding] = []
    present = {name for name in REQUIRED_PUBLIC_FILES if (root / name).is_file()}
    for name in sorted(set(REQUIRED_PUBLIC_FILES) - present):
        findings.append(
            Finding("high", "governance", f"Missing {name}", f"Add and review {name}.")
        )

    pyproject = _read(root / "pyproject.toml")
    readme = _read(root / "README.md")
    security = _read(root / "SECURITY.md")
    normalized_security = " ".join(security.lower().split())
    workflow = _read(root / ".github/workflows/ci.yml")
    web_html = _read(root / "src/ai_gateway/static/index.html")
    web_javascript = _read(root / "src/ai_gateway/static/app.js")

    _require(
        findings,
        'license = "MIT"' in pyproject and "MIT License" in _read(root / "LICENSE"),
        "high",
        "licensing",
        "Package and repository license are inconsistent",
        "Align pyproject metadata with the repository license.",
    )
    _require(
        findings,
        "offline" in readme.lower() and "mock" in readme.lower(),
        "high",
        "truthfulness",
        "Default execution boundary is unclear",
        "State that the default is offline and handlers are mocks.",
    )
    _require(
        findings,
        "private prompt" in normalized_security and "credential" in normalized_security,
        "high",
        "privacy",
        "Security policy omits sensitive routing data",
        "Document private-prompt and credential reporting boundaries.",
    )
    _require(
        findings,
        "permissions:" in workflow and "contents: read" in workflow,
        "medium",
        "supply_chain",
        "CI least-privilege permission is not visible",
        "Set explicit read-only default workflow permissions.",
    )
    _require(
        findings,
        "role=\"alert\"" in web_html and "meta name=\"viewport\"" in web_html,
        "medium",
        "accessibility",
        "Local console misses basic accessibility signals",
        "Keep responsive viewport and live result status semantics.",
    )
    _require(
        findings,
        'type="checkbox" role="switch"' in web_html
        and "execute:" in web_javascript
        and "textContent" in web_javascript
        and "innerHTML" not in web_javascript,
        "high",
        "execution_safety",
        "Console execution or rendering boundary is unsafe",
        "Default to decision-only and render response data as text.",
    )

    scores = {area: 10 for area in (
        "governance", "licensing", "truthfulness", "privacy",
        "supply_chain", "accessibility", "execution_safety",
    )}
    deduction = {"high": 4, "medium": 2, "low": 1}
    for finding in findings:
        scores[finding.area] = max(0, scores[finding.area] - deduction[finding.severity])

    return {
        "tool": "ai-gateway-readiness-agent",
        "mode": "local_deterministic_audit",
        "root": str(root),
        "files_required": list(REQUIRED_PUBLIC_FILES),
        "files_present": sorted(present),
        "scores": scores,
        "findings": [asdict(finding) for finding in findings],
        "external_model_calls": False,
        "ready": not findings,
    }


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _require(
    findings: list[Finding],
    condition: bool,
    severity: str,
    area: str,
    title: str,
    next_action: str,
) -> None:
    if not condition:
        findings.append(Finding(severity, area, title, next_action))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit local AI gateway readiness.")
    parser.add_argument("command", choices=("audit",))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = audit(args.root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['tool']} · {result['mode']}")
        for area, score in result["scores"].items():
            print(f"- {area}: {score}/10")
        for finding in result["findings"]:
            print(f"[{finding['severity']}] {finding['title']}: {finding['next_action']}")
        if result["ready"]:
            print("No deterministic readiness findings.")
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
