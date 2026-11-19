"""The futureagi-py CLI core (fi/_cli): registry, hooks, doctor, dispatch. It names no command group."""

import argparse
import ast
import json
import sys
import types
from pathlib import Path

import httpx
import pytest

from fi._cli import main as main_mod
from fi._cli import registry

CLI_DIR = Path(main_mod.__file__).parent


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


@pytest.fixture
def groups(monkeypatch):
    """Only the given fake groups are installed; hooks start empty and are restored after."""
    from fi._cli import doctor

    for attr in ("_PRE_PARSE", "_ON_INTERRUPT", "_ON_EXIT"):
        monkeypatch.setattr(registry, attr, [])
    monkeypatch.setattr(doctor, "_SECTIONS", [])
    monkeypatch.setattr(registry, "_SECTION_OF", {})
    installed = []
    monkeypatch.setattr(registry, "entry_points", lambda: list(installed))
    for var in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL", "FI_PLATFORM_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/futureagi-test-login.json")
    return installed


def test_core_imports_no_command_group():
    for path in CLI_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert not name.startswith("fi.experiments"), f"{path.name} imports {name}"


def test_fake_group_added_and_broken_group_skipped():
    def ok_register(sub):
        p = sub.add_parser("deployments")
        p.set_defaults(func=lambda args: 0)

    parser = argparse.ArgumentParser(prog="futureagi-py")
    sub = parser.add_subparsers(dest="command")
    warnings = []
    loaded = registry.load_groups(
        sub,
        eps=[FakeEP("deployments", _module("fake_deploy", ok_register)),
             FakeEP("broken", _module("bad", lambda sub: 1 / 0))],
        warn=warnings.append,
    )
    assert loaded == ["deployments"]
    assert len(warnings) == 1 and "'broken'" in warnings[0] and "other commands still work" in warnings[0]
    assert parser.parse_args(["deployments"]).command == "deployments"


def test_source_tree_table_is_read_from_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry.scripts]\nfutureagi-py = "fi._cli.main:main"\n\n'
        '[tool.poetry.plugins."futureagi.cli"]\n'
        'experiments = "fi.experiments._cli.commands"  # experiments\n'
        "deployments = 'fi.deployments._cli'\n\n"
        "[tool.poetry.group.dev.dependencies]\npytest = \"^8\"\n"
    )
    assert registry.source_tree_groups(pyproject) == {
        "experiments": "fi.experiments._cli.commands",
        "deployments": "fi.deployments._cli",
    }
    assert registry.source_tree_groups(tmp_path / "missing.toml") == {}


def test_this_checkout_table_matches_the_pyproject():
    table = registry.source_tree_groups()
    text = (CLI_DIR.parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert '[tool.poetry.plugins."futureagi.cli"]' in text
    assert '[tool.poetry.scripts]\nfutureagi-py = "fi._cli.main:main"' in text
    for name, value in table.items():
        assert f'{name} = "{value}"' in text


def test_help_and_doctor_with_no_groups(groups, capsys):
    assert main_mod.main(["--help"]) == 0
    assert "doctor" in capsys.readouterr().out
    assert main_mod.main([]) == 2
    assert main_mod.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "Server     https://api.futureagi.com" in out
    assert "Platform   https://api.futureagi.com/omega/api  (from derived)" in out


def test_broken_group_does_not_break_main(groups, capsys):
    groups.append(FakeEP("broken", _module("bad2", lambda sub: 1 / 0)))
    assert main_mod.main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "Server" in captured.out and captured.err.count("could not be loaded") == 1


def _group_with(handler, **defaults):
    def register(sub):
        p = sub.add_parser("thing")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=handler, **defaults)

    return FakeEP("thing", _module("thing_group", register))


def test_pre_parse_hook_answers_before_argparse(groups, capsys):
    def register(sub):
        sub.add_parser("thing").set_defaults(func=lambda a: 0)
        registry.add_pre_parse(lambda argv: 2 if "--" in argv else None)

    def broken(argv):
        raise RuntimeError("bad hook")

    groups.append(FakeEP("thing", _module("thing_pre", register)))
    registry.add_pre_parse(broken)  # a broken hook warns and is skipped
    assert main_mod.main(["thing", "--", "python", "app.py"]) == 2
    assert main_mod.main(["thing"]) == 0
    assert capsys.readouterr().err.count("pre-parse hook") == 2  # once per main() call


def test_interrupt_prints_the_hook_message_or_the_default(groups, capsys):
    def boom(args):
        raise KeyboardInterrupt()

    groups.append(_group_with(boom))
    assert main_mod.main(["thing"]) == 4
    assert capsys.readouterr().err.strip() == "Interrupted."
    registry.add_on_interrupt(lambda exc, argv: None)
    registry.add_on_interrupt(lambda exc, argv: f"Interrupted. Resume with: futureagi-py {' '.join(argv)}")
    assert main_mod.main(["thing"]) == 4
    assert capsys.readouterr().err.strip() == "Interrupted. Resume with: futureagi-py thing"


def test_exit_hooks_run_in_the_console_script_only(groups, monkeypatch):
    seen = []
    groups.append(_group_with(lambda args: 5))
    registry.add_on_exit(seen.append)
    registry.add_on_exit(seen.append)  # added once
    assert main_mod.main(["thing"]) == 5 and seen == []
    monkeypatch.setattr(sys, "argv", ["futureagi-py", "thing"])
    assert main_mod.main() == 5 and seen == [5]


def test_transport_error_is_one_line_exit_3(groups, capsys):
    def boom(args):
        raise httpx.ConnectTimeout("timed out", request=httpx.Request("GET", "http://srv.test:8000/x"))

    groups.append(_group_with(boom))
    assert main_mod.main(["thing"]) == 3
    err = capsys.readouterr().err
    assert err.strip() == "error: cannot reach http://srv.test:8000 (timed out); check FI_BASE_URL"
    assert main_mod.main(["thing", "--json"]) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["error"]["code"] == "SERVER_UNREACHABLE" and doc["error"]["exit_code"] == 3


def test_missing_module_names_the_groups_hint_or_the_module(groups, capsys):
    def needs_extra(args):
        raise ModuleNotFoundError("No module named 'livekit'", name="livekit")

    groups.append(_group_with(needs_extra, install_hint='pip install "futureagi[voice]"'))
    assert main_mod.main(["thing"]) == 3
    assert capsys.readouterr().err.strip() == (
        "error: No module named 'livekit'. Run: pip install \"futureagi[voice]\""
    )
    groups[:] = [_group_with(needs_extra)]
    assert main_mod.main(["thing", "--json"]) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["error"]["code"] == "MISSING_EXTRA"
    assert "provides the 'livekit' module" in doc["error"]["message"]


def test_sdk_exception_uses_its_exit_code(groups, capsys):
    from fi.errors import MissingExtraError

    class Gate(MissingExtraError):
        exit_code = 1

    def fail(args):
        raise Gate(extra="langgraph", module="traceai_langchain")

    groups.append(_group_with(fail))
    assert main_mod.main(["thing"]) == 1
    assert 'pip install "futureagi[langgraph]"' in capsys.readouterr().err


def test_a_group_adds_the_doctor_arguments_its_section_reads(groups, capsys):
    from fi._cli import doctor

    def register(sub):
        doctor.add_argument(sub, "target", nargs="?", help="what to check")
        doctor.add_argument(sub, "--dataset")
        doctor.add_argument(sub, "--dataset")  # already there: left alone
        doctor.add_section("thing", lambda args: [f"target={args.target} dataset={args.dataset}"])

    groups.append(FakeEP("thing", _module("thing_doctor", register)))
    assert main_mod.main(["doctor", "agent.py:task", "--dataset", "rows.jsonl"]) == 0
    assert "[thing]\ntarget=agent.py:task dataset=rows.jsonl" in capsys.readouterr().out
    assert [title for title, _ in doctor._SECTIONS] == ["thing"]
    bare = argparse.ArgumentParser().add_subparsers()
    doctor.add_argument(bare, "--dataset")  # no doctor command here: nothing to do, no error


def test_help_lists_commands_by_section(groups, capsys):
    def register(sub):
        for name, section in (("run", "evaluate"), ("upload", "evaluate"), ("deployments", "platform"),
                              ("sandboxes", "platform"), ("misc", None)):
            sub.add_parser(name, help=f"{name} help").set_defaults(func=lambda a: 0)
            if section:
                registry.set_section(name, section)

    groups.append(FakeEP("several", _module("several", register)))
    assert main_mod.main(["--help"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: futureagi-py [-h] [--version] COMMAND ...")
    tail = out[out.index("Evaluate:"):]
    assert tail.split("\n\n") == [
        "Evaluate:\n  run          run help\n  upload       upload help",
        "Platform:\n  deployments  deployments help\n  sandboxes    sandboxes help",
        "Setup:\n  doctor       check the host, the keys and each command group's setup"
        "\n  login        save one login (keys bound to their server) for every command"
        "\n  logout       remove the saved login",
        "Other:\n  misc         misc help\n",
    ]
    with pytest.raises(ValueError):
        registry.set_section("x", "Evaluate")


def test_doctor_takes_json(groups, capsys):
    """Every command takes --json, doctor included: one object."""
    from fi._cli import doctor

    def register(sub):
        doctor.add_argument(sub, "--thing-name")
        doctor.add_section("thing", lambda args: [f"name={args.thing_name}"])
        doctor.add_section("broken", lambda args: 1 / 0)

    groups.append(FakeEP("thing", _module("thing_json", register)))
    assert main_mod.main(["doctor", "--json", "--thing-name", "x"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["server"] == {"base_url": "https://api.futureagi.com", "source": "default"}
    assert doc["keys"] == {"present": False, "source": "none"}
    assert doc["platform"] == {"base_url": "https://api.futureagi.com/omega/api", "source": "derived"}
    assert doc["login"]["exists"] is False and doc["note"] is None
    assert doc["sections"]["thing"] == {"lines": ["name=x"]}
    assert doc["sections"]["broken"]["error"].startswith("ZeroDivisionError")
    assert main_mod.main(["doctor"]) == 0  # the text form shows the same section lines
    out = capsys.readouterr().out
    assert "[thing]\nname=None" in out and "could not check: ZeroDivisionError" in out


def test_doctor_json_never_prints_a_key(groups, capsys, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "k-secret-1234")
    monkeypatch.setenv("FI_SECRET_KEY", "s-secret-5678")
    # --offline: with keys and no FI_BASE_URL, "who you are" would ask the default (production) server
    assert main_mod.main(["doctor", "--json", "--offline"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["keys"] == {"present": True, "source": "env"}
    assert json.loads(out)["who"]["line"] == "not checked (--offline)"
    assert "secret" not in out


def test_help_lists_a_command_without_help_and_its_aliases(groups, capsys):
    """argparse only makes a help row when help= is given; the list falls back to the
    registered choices, shows aliases, and still hides help=SUPPRESS."""

    def register(sub):
        sub.add_parser("deployments").set_defaults(func=lambda a: 0)  # no help=
        sub.add_parser("sandboxes", aliases=["sbx"], help="manage sandboxes").set_defaults(func=lambda a: 0)
        sub.add_parser("hidden", help=argparse.SUPPRESS).set_defaults(func=lambda a: 0)
        registry.set_section("deployments", "platform")
        registry.set_section("sandboxes", "platform")

    groups.append(FakeEP("plat", _module("plat_help", register)))
    assert main_mod.main(["--help"]) == 0
    out = capsys.readouterr().out
    block = out[out.index("Platform:"):].split("\n\n")[0]
    assert block == "Platform:\n  deployments\n  sandboxes (sbx)  manage sandboxes"
    assert "hidden" not in out
    assert main_mod.main(["sbx"]) == 0 and main_mod.main(["deployments"]) == 0


def test_a_broken_installed_package_is_not_called_a_missing_extra(groups, capsys):
    """An installed package's "cannot import name X" must not say "install it"."""

    def broken(args):
        raise ImportError("cannot import name 'Thing' from 'somepkg' (/x/somepkg/__init__.py)", name="somepkg")

    groups.append(_group_with(broken, install_hint='pip install "futureagi[voice]"'))
    assert main_mod.main(["thing"]) == 3
    err = capsys.readouterr().err
    assert "cannot import name 'Thing'" in err and "reinstall or upgrade it" in err
    assert "pip install" not in err and "provides the" not in err
    assert main_mod.main(["thing", "--json"]) == 3
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "IMPORT_FAILED"


def test_transport_error_lines_say_what_happened(groups, capsys):
    """Through the CLI: a read timeout reached the server, so it is not "cannot reach"."""

    def slow(args):
        raise httpx.ReadTimeout("read timed out", request=httpx.Request("GET", "http://srv.test:8000/x"))

    groups.append(_group_with(slow))
    assert main_mod.main(["thing"]) == 3
    err = capsys.readouterr().err.strip()
    assert err == "error: http://srv.test:8000 did not answer in time (read timed out); the server may be busy, retry later"


def test_a_section_problem_makes_doctor_exit_3(groups, capsys):
    """A section that returns a doctor.Problem line: printed, listed under problems, exit 3 (CLI-03)."""
    from fi._cli import doctor

    def register(sub):
        doctor.add_section("thing", lambda args: ["fine line", doctor.Problem("Thing      http://127.0.0.1:9 is down")])

    groups.append(FakeEP("thing", _module("thing_problem", register)))
    assert main_mod.main(["doctor"]) == 3
    assert "[thing]\nfine line\nThing      http://127.0.0.1:9 is down" in capsys.readouterr().out
    assert main_mod.main(["doctor", "--json"]) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["sections"]["thing"] == {"lines": ["fine line", "Thing      http://127.0.0.1:9 is down"],
                                        "problems": ["Thing      http://127.0.0.1:9 is down"]}
