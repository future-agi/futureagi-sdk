"""The offline rename tool distinguishes executable contexts from package identity."""
import ast
import configparser
import importlib.util
import json
from pathlib import Path
import zipfile

from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("rename_cli", ROOT / "scripts/packaging/rename-cli.py")
rename_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rename_cli)
PKG = "futureagi"


def _tracked_checkout_paths(root):
    # Archives have no authoritative index. Never substitute a filesystem walk
    # or inherit an enclosing repository's index for the checkout contract.
    if not (root / ".git").exists():
        pytest.skip("checkout-only assertion requires the source repository's git index")
    return rename_cli.tracked_paths(root)


@pytest.fixture
def tracked_checkout_paths():
    return _tracked_checkout_paths(ROOT)


def test_checkout_scope_skips_only_archives(tmp_path, monkeypatch):
    tracked = Mock(return_value=[tmp_path / "tracked.py"])
    monkeypatch.setattr(rename_cli, "tracked_paths", tracked)
    with pytest.raises(pytest.skip.Exception, match="checkout-only"):
        _tracked_checkout_paths(tmp_path)
    tracked.assert_not_called()
    # A linked worktree uses a .git file rather than a directory.
    (tmp_path / ".git").write_text("gitdir: synthetic-index\n")
    assert _tracked_checkout_paths(tmp_path) == [tmp_path / "tracked.py"]
    tracked.assert_called_once_with(tmp_path)
    tracked.side_effect = RuntimeError("index unavailable")
    with pytest.raises(RuntimeError, match="index unavailable"):
        _tracked_checkout_paths(tmp_path)


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    content = {
        "python/pyproject.toml": (
            f'[tool.poetry]\nname = "{PKG}"\n[tool.poetry.scripts]\n'
            f'{PKG} = "fi._cli.main:main"\n'
            f'[tool.poetry.plugins."{PKG}.cli"]\nevals = "fi.evals._cli"\n'
        ),
        "python/fi/_cli/main.py": (
            f'prog="{PKG}"\nusage="{PKG} [-h] COMMAND ..."\n'
            f'description="{PKG} COMMAND --help"\n'
            f'version=f"{PKG} {{installed_version}}"\nversion("{PKG}")\n'
        ),
        "python/README.md": f'pip install {PKG}\r\n{PKG} doctor --offline\r\n',
        "python/fi/experiments/schemas/cli-json.schema.json": f'{{"description": "{PKG} run --json", "$id": "urn:{PKG}:cli-json:1"}}\n',
        "python/fi/experiments/_options.yaml": f'# {PKG} upload\n',
        "python/tests/evals/fixtures/differences-ai-evaluation-1.1.0.json": f'{{"{PKG}": "`{PKG} evals list`"}}\n',
        "python/tests/gateway/port_manifest.json": f'{{"note": "the {PKG} version ({PKG}-python/<v>)"}}\n',
        "examples/cli.sh": f'{PKG} --help\n{PKG} run a.py\n',
    }
    for relative, text in content.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
    monkeypatch.setattr(rename_cli, "tracked_paths", lambda root: [root / rel for rel in content])
    return tmp_path, content


def test_rename_is_idempotent_swappable_and_byte_preserving(checkout, capsys):
    root, original = checkout
    first = "sdk-choice-one"
    count, occurrences = rename_cli.rename(root, first, dry_run=True)
    assert count == 7 and occurrences == 11
    assert all((root / rel).read_bytes() == text.encode() for rel, text in original.items())
    assert rename_cli.rename(root, first) == (count, occurrences)
    assert (root / "python/README.md").read_bytes() == f'pip install {PKG}\r\n{first} doctor --offline\r\n'.encode()
    assert rename_cli.rename(root, first) == (0, 0)
    assert "0 files, 0 occurrences" in capsys.readouterr().out
    second = "sdk.choice_two"
    assert rename_cli.rename(root, second) == (count, occurrences)
    project = (root / "python/pyproject.toml").read_text()
    assert f'"{second}" = "fi._cli.main:main"' in project
    assert rename_cli.current_name(project) == second
    assert rename_cli.rename(root, PKG) == (count, occurrences)
    assert all((root / rel).read_bytes() == text.encode() for rel, text in original.items())


@pytest.mark.parametrize("name", ["", "-help", "../escape", "two words", "x;y", "x\ny", "a/b", 'x"y'])
def test_invalid_name_writes_nothing(checkout, name):
    root, original = checkout
    with pytest.raises(ValueError, match="NEW_NAME"):
        rename_cli.rename(root, name)
    assert all((root / rel).read_bytes() == text.encode() for rel, text in original.items())


@pytest.mark.parametrize("name", [
    *rename_cli.COMMANDS, "version", "list", "ls", "show", "runs", "create",
    "rotate-secret", "validate", "wait-for-approval", "--json", "--offline",
])
def test_subcommand_and_flag_names_are_rejected_without_writes(checkout, name):
    root, original = checkout
    with pytest.raises(ValueError, match="NEW_NAME"):
        rename_cli.rename(root, name)
    assert all((root / rel).read_bytes() == text.encode() for rel, text in original.items())


def test_two_swaps_cannot_turn_a_subcommand_into_the_executable(checkout):
    root, _ = checkout
    readme = root / "python/README.md"
    readme.write_text(f'{PKG} doctor --help\n{PKG} webhooks list --help\n')
    rename_cli.rename(root, "sdk-first")
    before = {path: path.read_bytes() for path in rename_cli.tracked_paths(root)}
    with pytest.raises(ValueError, match="subcommand"):
        rename_cli.rename(root, "doctor")
    assert all(path.read_bytes() == raw for path, raw in before.items())
    rename_cli.rename(root, "sdk-choice")
    assert readme.read_text() == 'sdk-choice doctor --help\nsdk-choice webhooks list --help\n'
    assert rename_cli.rename(root, "sdk-choice") == (0, 0)


def test_inconsistent_entry_points_fail_before_writes(checkout):
    root, original = checkout
    (root / "python/fi/_cli/main.py").write_text('prog="different"\n')
    with pytest.raises(ValueError, match="disagree"):
        rename_cli.rename(root, "sdk-choice")
    assert (root / "python/pyproject.toml").read_bytes() == original["python/pyproject.toml"].encode()


@pytest.mark.parametrize("command", [*rename_cli.COMMANDS, "version"])
def test_command_invocations_are_rewritten(command):
    before = f'`{PKG} {command}`\n$ {PKG} {command}\n{PKG} {command}\n'
    after, count = rename_cli.rewrite(before, "python/README.md", PKG, "sdk-choice")
    assert after == before.replace(PKG, "sdk-choice")
    assert count == 3


def test_distribution_and_noun_contexts_are_unchanged():
    text = "\n".join([
        f'pip install {PKG}', f'pip install "{PKG}[experiments]"',
        f'pip install {PKG} --version', f'pip install {PKG} run',
        f'version("{PKG}")', f'Name: {PKG}', f'{PKG}-0.7.0.dist-info',
        f'[tool.poetry.plugins."{PKG}.cli"]', f'GROUP = "{PKG}.cli"',
        '"@future-agi/sdk"', f'the {PKG} version', f'The {PKG} version (agentcc)',
        f'{PKG} is not installed as a distribution', f'Checked 12 {PKG} files.',
        f'"distribution": "{PKG}"', f'pip install {PKG} run-other-package',
        f'{PKG}-other doctor', f'some_{PKG} run', f'https://docs.{PKG}/run',
        # Synthetic negative fixtures for unavailable groups are not SDK commands.
        f'{PKG} deployments list', f'{PKG} sandboxes list',
    ])
    assert rename_cli.rewrite(text, "python/README.md", PKG, "sdk-choice") == (text, 0)


def test_nonliteral_commands_and_executable_assertions():
    cases = {
        "python/fi/experiments/_cli/commands.py": f'shlex.join(["{PKG}", *argv])',
        "python/fi/experiments/_resume_params.py": f"shlex.join(['{PKG}', *argv])",
        "python/tests/experiments/unit/test_process.py": f'assert words == ["{PKG}", "run"]',
        "python/tests/test_cli_core.py": f'monkeypatch.setattr(sys, "argv", ["{PKG}", "thing"])',
        "python/tests/experiments/unit/test_upload_review.py": f'assert resume[0] == "{PKG}"',
        "python/tests/evals/test_provenance.py": f'assert names == ["{PKG}"]',
        "python/tests/test_namespace_ownership_footprint.py": f'entries={{"console_scripts": ["{PKG}"]}}',
    }
    for path, text in cases.items():
        after, count = rename_cli.rewrite(text, path, PKG, "sdk-choice")
        assert (after, count) == (text.replace(PKG, "sdk-choice"), 1), path


def test_command_scanner_regex_escapes_dots_and_can_swap_again():
    text = f'return set(re.findall(r"`?{PKG} ([a-z][a-z-]*)", text))'
    path = "python/tests/experiments/unit/test_review_fixes.py"
    after, count = rename_cli.rewrite(text, path, PKG, "sdk.choice")
    assert r'sdk\.choice' in after and count == 1
    assert rename_cli.rewrite(after, path, "sdk.choice", PKG) == (text, 1)


def test_json_escaped_newlines_and_boundaries():
    text = f'"next: \\n{PKG} run --help"\n{PKG} --help-other\n'
    after, count = rename_cli.rewrite(text, "examples/help.json", PKG, "sdk-choice")
    assert after == f'"next: \\nsdk-choice run --help"\n{PKG} --help-other\n'
    assert count == 1


def test_scope_includes_installed_wheel_journeys_and_typescript_readme(tracked_checkout_paths):
    paths = {path.relative_to(ROOT).as_posix() for path in tracked_checkout_paths}
    assert {
        "scripts/journeys/installed_cli.py",
        "scripts/journeys/test_cli_entrypoint.py",
        "typescript/futureagi/README.md",
    } <= paths


def test_installed_console_metadata_rewrites_leave_distribution_identities():
    relative = "scripts/journeys/test_cli_entrypoint.py"
    executable_lines = (
        f"assert cfg.has_option('console_scripts', '{PKG}')\n"
        f"cfg.set('console_scripts', '{PKG}', 'fi._cli.main:missing_entrypoint')\n"
        f"cfg.remove_option('console_scripts', '{PKG}')\n"
        f"shutil.which('{PKG}')\n"
    )
    distribution_lines = (
        f"metadata.distribution('{PKG}')\n"
        f"cfg.has_option('{PKG}.cli', 'evals')\n"
        f"wheel = '{PKG}-0.7.0-py3-none-any.whl'\n"
    )
    after, count = rename_cli.rewrite(executable_lines + distribution_lines, relative, PKG, "sdk-choice")
    assert after == executable_lines.replace(PKG, "sdk-choice") + distribution_lines
    assert count == 4


def test_installed_journeys_and_typescript_follow_two_swaps(checkout, monkeypatch):
    root, content = checkout
    current = rename_cli.current_name((ROOT / "python/pyproject.toml").read_text())
    for relative in ("scripts/journeys/installed_cli.py", "scripts/journeys/test_cli_entrypoint.py"):
        # Copy the real harness, normalized to this fixture's starting executable.
        content[relative] = (ROOT / relative).read_text().replace(current, PKG)
    readme = "typescript/futureagi/README.md"
    content[readme] = (
        f'Use the `{PKG} webhooks` CLI.\n'
        'import { verifyWebhook } from "@future-agi/sdk/webhooks";\n'
        f'pip install {PKG}\n'
    )
    for relative in ("scripts/journeys/installed_cli.py", "scripts/journeys/test_cli_entrypoint.py", readme):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content[relative])
    monkeypatch.syspath_prepend(str(ROOT / "scripts/journeys"))

    def load(relative):
        path = root / relative
        spec = importlib.util.spec_from_file_location("journey_under_test", path)
        module = importlib.util.module_from_spec(spec)
        # Same-length swaps within one second must not reuse cached bytecode.
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        return module

    for new in ("sdk-choice-one", "sdk.choice_two"):
        rename_cli.rename(root, new)
        assert (root / readme).read_text() == content[readme].replace(f'{PKG} webhooks', f'{new} webhooks')
        installed = load("scripts/journeys/installed_cli.py")
        run = Mock()
        with monkeypatch.context() as patch:
            patch.setattr(installed.sysconfig, "get_path", lambda key: str(root / "bin"))
            patch.setattr(installed.subprocess, "run", run)
            installed.futureagi("doctor", "--offline")
        assert run.call_args.args[0] == [str(root / "bin" / new), "doctor", "--offline"]

        journey = load("scripts/journeys/test_cli_entrypoint.py")
        source = root / f"{PKG}-0.7.0-py3-none-any.whl"
        prefix = f"{PKG}-0.7.0.dist-info/"
        entry = prefix + "entry_points.txt"
        unchanged = {
            prefix + "METADATA": f"Name: {PKG}\nVersion: 0.7.0\n".encode(),
            "fi/_cli/main.py": b"def main(): return 0\n",
        }
        with zipfile.ZipFile(source, "w") as wheel:
            wheel.writestr(entry, (
                f"[console_scripts]\n{new} = fi._cli.main:main\nother-tool = other:main\n"
                f"[{PKG}.cli]\nevals = fi.evals._cli\n"
            ))
            wheel.writestr(prefix + "RECORD", "")
            for name, raw in unchanged.items():
                wheel.writestr(name, raw)
        for broken in (False, True):
            destination = root / f"mutant-{broken}.whl"
            journey.mutate_entrypoint(source, destination, broken=broken)
            with zipfile.ZipFile(destination) as wheel:
                cfg = configparser.ConfigParser()
                cfg.read_string(wheel.read(entry).decode())
                assert cfg.has_option("console_scripts", new) is broken
                if broken:
                    assert cfg.get("console_scripts", new) == "fi._cli.main:missing_entrypoint"
                assert cfg.get("console_scripts", "other-tool") == "other:main"
                assert cfg.get(f"{PKG}.cli", "evals") == "fi.evals._cli"
                assert all(wheel.read(name) == raw for name, raw in unchanged.items())

        # Exercise the exact presence probe without launching Docker or installing.
        consumer = object.__new__(journey.CheckedConsumers)
        for present in (False, True):
            consumer.expect_cli = present
            execute = Mock(return_value=0)
            which = Mock(return_value=str(root / "bin" / new) if present else None)
            with monkeypatch.context() as patch:
                patch.setattr(journey.Consumers, "execute", execute)
                patch.setattr("shutil.which", which)
                consumer.execute("box", "python-probe", ["python", "probe.py"])
                probe = execute.call_args_list[0].args[2]
                assert probe[:3] == ["python", "-I", "-c"]
                exec(probe[3], {})
            which.assert_called_once_with(new)
        assert rename_cli.rename(root, new) == (0, 0)


def test_current_checkout_can_swap_names_and_round_trip_without_writes(tracked_checkout_paths):
    old = rename_cli.current_name((ROOT / "python/pyproject.toml").read_text())
    alternate = old + ".alternate_cli"
    changed = 0
    for path in tracked_checkout_paths:
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        try:
            before = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT).as_posix()
        after, count = rename_cli.rewrite(before, relative, old, alternate)
        if not count:
            continue
        changed += 1
        if path.suffix == ".py":
            ast.parse(after)
        elif path.suffix == ".json":
            json.loads(after)
        restored, reverse_count = rename_cli.rewrite(after, relative, alternate, old)
        assert restored == before and reverse_count == count, relative
    assert changed > 50
