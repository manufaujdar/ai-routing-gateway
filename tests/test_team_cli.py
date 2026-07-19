from __future__ import annotations

import json
from pathlib import Path

from ai_gateway.team_cli import main


def test_plan_cli_outputs_machine_readable_decision(capsys) -> None:
    result = main(
        [
            "plan",
            "Design a routing policy",
            "--research",
            "--ai-policy",
            "--high-stakes",
            "--ambiguous",
            "--hard-to-reverse",
            "--competing-approaches",
            "--independent-views-useful",
            "--council-resources-fit",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["council_recommended"] is True
    assert payload["steps"][0]["roles"] == ["team_lead"]


def test_roles_cli_lists_all_roles(capsys) -> None:
    assert main(["roles", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 12


def test_init_cli_reports_collisions_on_stderr(tmp_path: Path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()

    assert main(["init", str(tmp_path)]) == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    assert "refusing to overwrite" in streams.err


def test_plan_cli_rejects_external_authorization_without_release(capsys) -> None:
    assert main(["plan", "test", "--authorize-external-actions"]) == 2
    assert "external actions" in capsys.readouterr().err


def test_validate_cli_accepts_generated_team(tmp_path: Path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["validate", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out) == {"valid": True, "errors": []}


def test_validate_cli_reports_invalid_registry_as_json(tmp_path: Path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()
    (tmp_path / ".ai" / "team.json").write_text("[]", encoding="utf-8")

    assert main(["validate", str(tmp_path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert "root must be a JSON object" in payload["errors"][0]
