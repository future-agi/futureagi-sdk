"""The module launcher uses the console entry point, including exit hooks and prog."""
import runpy
import sys

import pytest

from fi._cli import doctor, main as cli, registry


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.setattr(registry, "entry_points", lambda: [])
    for attr in ("_PRE_PARSE", "_ON_INTERRUPT", "_ON_EXIT"):
        monkeypatch.setattr(registry, attr, [])
    monkeypatch.setattr(registry, "_SECTION_OF", {})
    monkeypatch.setattr(doctor, "_SECTIONS", [])


@pytest.mark.parametrize("argv,code", [([], 2), (["--help"], 0), (["--version"], 0), (["no-such-command"], 2)])
def test_module_uses_the_same_parser_and_exit_status(monkeypatch, capsys, argv, code):
    expected = cli.main(argv)
    direct = capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["fi._cli", *argv])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("fi._cli", run_name="__main__")
    assert caught.value.code == expected == code
    output = capsys.readouterr()
    assert output == direct
    assert cli.build_parser().prog in output.out + output.err
    assert "usage: fi._cli" not in output.out + output.err


def test_module_calls_main_without_argv_and_runs_console_exit_hooks(monkeypatch):
    seen = []
    monkeypatch.setattr(cli, "_dispatch", lambda args, argv: 5)
    registry.add_on_exit(seen.append)
    monkeypatch.setattr(sys, "argv", ["fi._cli", "doctor", "--offline"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("fi._cli", run_name="__main__")
    assert caught.value.code == 5
    assert seen == [5]
