"""The futureagi.cli registry: a fake entry point adds a group; a broken group is skipped with one warning."""

import argparse
import sys
import types

from fi._cli import registry


class FakeEP:
    def __init__(self, name, module):
        self.name = name
        self._module = module

    def load(self):
        return self._module


def _module(name, register):
    mod = types.ModuleType(name)
    mod.register = register
    return mod


def test_fake_group_added_and_broken_group_skipped():
    def ok_register(sub):
        p = sub.add_parser("deployments")
        p.set_defaults(func=lambda args: 0)

    def bad_register(sub):
        raise RuntimeError("boom")

    parser = argparse.ArgumentParser(prog="futureagi-py")
    sub = parser.add_subparsers(dest="command")
    warnings = []
    loaded = registry.load_groups(
        sub,
        eps=[FakeEP("deployments", _module("fake_deploy", ok_register)), FakeEP("broken", _module("bad", bad_register))],
        warn=warnings.append,
    )
    assert loaded == ["deployments"]
    assert len(warnings) == 1 and "'broken'" in warnings[0] and "other commands still work" in warnings[0]
    assert parser.parse_args(["deployments"]).command == "deployments"


def test_installed_entry_points_include_experiments():
    names = [ep.name for ep in registry.entry_points()]
    assert "experiments" in names


def test_broken_group_does_not_break_main(monkeypatch, capsys):
    from fi._cli import main as main_mod

    real = registry.entry_points

    def eps():
        return real() + [FakeEP("broken", _module("bad2", lambda sub: 1 / 0))]

    monkeypatch.setattr(registry, "entry_points", eps)
    code = main_mod.main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0 and "Server" in captured.out
    assert captured.err.count("could not be loaded") == 1


def test_group_module_imports_only_argparse():
    import subprocess

    code = (
        "import sys; import fi.experiments._cli.commands as c; "
        "bad=[m for m in ('fi.experiments._engine','opentelemetry','httpx','pydantic') if m in sys.modules]; "
        "print(bad)"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "[]", out.stderr
