from __future__ import annotations

from importlib.resources import files

import pytest

from ai_gateway._version import __version__
from ai_gateway.cli import main as gateway_main
from ai_gateway.team_cli import main as team_main


@pytest.mark.parametrize("entrypoint", [gateway_main, team_main])
def test_cli_exposes_package_version(entrypoint, capsys) -> None:
    with pytest.raises(SystemExit) as error:
        entrypoint(["--version"])

    assert error.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_package_advertises_inline_typing_support() -> None:
    assert files("ai_gateway").joinpath("py.typed").is_file()
