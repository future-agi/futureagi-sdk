"""Optional CLI error markers; text expectations pin the pre-marker byte contract."""

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

PYTHON = Path(__file__).resolve().parents[3]
EXPERIMENTS_HINT = 'pip install "futureagi[experiments]"'
EVALS_HINT = 'pip install "futureagi[evals]"'
EVALS_FALLBACK = f"Local evaluations require Python 3.11+ and {EVALS_HINT}"
EVALS_GUARD = (
    "Local metrics and LLM judges require Python 3.11+ and futureagi[evals]. "
    f"On Python 3.11+, install with: {EVALS_HINT}."
)


def _dispatch_process(tmp_path, handler, *, blocked=(), setup="", json_output=False):
    """Exercise the CLI dispatcher without loading command groups or optional packages."""
    blocker = tmp_path / "block"
    blocker.mkdir(exist_ok=True)
    (blocker / "sitecustomize.py").write_text(
        f"BLOCKED = {tuple(blocked)!r}\n" + textwrap.dedent("""
        import socket
        import sys

        def refuse(*args, **kwargs):
            raise AssertionError("no network in this test")

        socket.socket.connect = refuse
        socket.getaddrinfo = refuse

        class Block:
            def find_spec(self, name, path=None, target=None):
                if name.split(".", 1)[0] in BLOCKED:
                    raise ModuleNotFoundError(f"No module named {name!r}", name=name)
                return None

        sys.meta_path.insert(0, Block())
        """))
    source = (
        "import sys\n"
        "from argparse import Namespace\n"
        "from fi._cli.main import _dispatch, missing_extra\n"
        + setup + "\n"
        + "def handler(args):\n" + textwrap.indent(handler, "    ") + "\n"
        + f"args = Namespace(func=handler, json={json_output!r}, install_hint={EXPERIMENTS_HINT!r})\n"
        + "raise SystemExit(_dispatch(args))\n"
    )
    env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": os.pathsep.join((str(blocker), str(PYTHON))),
        "HOME": str(tmp_path),
        "FI_BASE_URL": "http://127.0.0.1:9",
        "FI_LOGIN_FILE": str(tmp_path / "no-login.json"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    # Keep bytes: text mode would normalise stderr newlines before the comparison.
    return subprocess.run([sys.executable, "-c", source], cwd=tmp_path, env=env,
                          capture_output=True, timeout=60)


def _assert_output(out, json_output, message, markers, *, code="MISSING_EXTRA"):
    assert out.returncode == 3, (out.stdout, out.stderr)
    assert b"Traceback" not in out.stdout + out.stderr
    if json_output:
        assert out.stderr == b""
        assert json.loads(out.stdout) == {
            "error": {"code": code, "message": message, "exit_code": 3, **markers},
        }
    else:
        assert out.stdout == b""
        assert out.stderr == f"error: {message}\n".encode("utf-8")


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("root,extra", [
    ("litellm", "evals"), ("nltk", "evals"), ("yaml", "evals"),
    ("traceai_openai", "openai"), ("traceai_openai_agents", "openai-agents"),
    ("fi_cli_unknown_dependency", None), ("opentelemetry", None), ("dotenv", None),
])
def test_blocked_module_markers_and_unchanged_text(tmp_path, root, extra, json_output):
    out = _dispatch_process(tmp_path, f"__import__({root!r})", blocked=(root,), json_output=json_output)
    message = f"No module named '{root}'. "
    if extra == "evals":
        message += EVALS_FALLBACK
    else:
        message += f'Run: pip install "futureagi[{extra or "experiments"}]"'
    markers = {"reason": "missing_module", "module": root}
    if extra:
        markers["extra"] = extra
    _assert_output(out, json_output, message, markers)


@pytest.mark.parametrize("json_output", [False, True])
def test_unique_experiments_mapping_and_unchanged_text(tmp_path, json_output):
    # No current production root is unique to experiments: dotenv and instrumentation
    # are shared. Use an isolated table fixture, never a command hint, for this case.
    root = "fi_cli_fixture_experiments"
    setup = (
        "from fi._cli.extra_roots import EXTRA_ROOTS\n"
        f"EXTRA_ROOTS[{root!r}] = 'experiments'\n"
    )
    out = _dispatch_process(tmp_path, f"__import__({root!r})", blocked=(root,),
                            setup=setup, json_output=json_output)
    _assert_output(out, json_output, f"No module named '{root}'. Run: {EXPERIMENTS_HINT}",
                   {"reason": "missing_module", "extra": "experiments", "module": root})


@pytest.mark.parametrize("json_output", [False, True])
def test_python_guard_markers_and_unchanged_text(tmp_path, json_output):
    # Import HTTP dependencies before spoofing only the guard/reporting interval.
    setup = "import httpx\nfrom fi.evals._extras import require_evals_python\n"
    handler = 'sys.version_info = (3, 10, 0, "final", 0)\nrequire_evals_python()'
    out = _dispatch_process(tmp_path, handler, setup=setup, json_output=json_output)
    _assert_output(out, json_output, EVALS_GUARD,
                   {"reason": "python_version", "python": "3.10", "required_python": "3.11", "extra": "evals"})
    if json_output:
        error = json.loads(out.stdout)["error"]
        assert re.fullmatch(r"[0-9]+\.[0-9]+", error["python"])
        assert re.fullmatch(r"[0-9]+\.[0-9]+", error["required_python"])


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("module,root,extra", [
    ("litellm.router", "litellm", "evals"),
    ("unknown.child", "unknown", None),
    ("valid.bad-name", "valid", None),
    ("bad-name.child", None, None),
    ("bad/name.child", None, None),
    ("bad\nname.child", None, None),
    ("naïve.child", None, None),
    (".hidden", None, None),
])
def test_only_valid_roots_are_emitted(tmp_path, module, root, extra, json_output):
    message = f"No module named {module!r}"
    handler = f"raise ModuleNotFoundError({message!r}, name={module!r})"
    out = _dispatch_process(tmp_path, handler, json_output=json_output)
    markers = {"reason": "missing_module"}
    if root is not None:
        markers["module"] = root
    if extra:
        markers["extra"] = extra
    message += f". {EVALS_FALLBACK}" if extra == "evals" else f". Run: {EXPERIMENTS_HINT}"
    _assert_output(out, json_output, message, markers)


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("exception", ["ImportError", "ModuleNotFoundError"])
def test_unknown_cause_has_no_markers(tmp_path, exception, json_output):
    handler = (
        f"exc = {exception}('optional backend unavailable')\n"
        "raise missing_extra(args, exc)"
    )
    out = _dispatch_process(tmp_path, handler, json_output=json_output)
    _assert_output(out, json_output, f"optional backend unavailable. Run: {EXPERIMENTS_HINT}", {})


@pytest.mark.parametrize("json_output", [False, True])
def test_unrelated_import_error_has_no_markers(tmp_path, json_output):
    out = _dispatch_process(tmp_path, 'raise ImportError("cannot import name broken")', json_output=json_output)
    _assert_output(out, json_output,
                   "cannot import name broken. An installed package failed to import; reinstall or upgrade it",
                   {}, code="IMPORT_FAILED")


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("module,markers", [
    ("litellm.router", {"reason": "missing_module", "module": "litellm", "extra": "evals"}),
    ("unknown.child", {"reason": "missing_module", "module": "unknown"}),
])
def test_explicit_hint_does_not_supply_extra_or_suppress_markers(tmp_path, module, markers, json_output):
    message = f"No module named {module!r}"
    handler = (
        f"exc = ModuleNotFoundError({message!r}, name={module!r})\n"
        "exc.install_hint = 'custom repair instruction'\n"
        "exc.extra = 'untrusted-extra'\n"
        "exc.reason = 'untrusted-reason'\n"
        "raise exc"
    )
    out = _dispatch_process(tmp_path, handler, json_output=json_output)
    _assert_output(out, json_output, f"{message}. Run: custom repair instruction", markers)


def test_wrapping_preserves_existing_exception_attributes():
    from argparse import Namespace

    from fi._cli.main import missing_extra
    from fi.errors import MissingExtraError

    exc = ModuleNotFoundError("No module named 'litellm.router'", name="litellm.router")
    exc.install_hint = "custom repair instruction"
    wrapped = missing_extra(Namespace(install_hint=EXPERIMENTS_HINT), exc)
    assert isinstance(wrapped, MissingExtraError)
    assert wrapped.__cause__ is exc
    assert wrapped.module == "litellm.router"
    assert wrapped.extra is None  # the pre-marker, explicit-hint contract
    assert wrapped.install_hint == exc.install_hint
    assert str(wrapped) == "No module named 'litellm.router'. Run: custom repair instruction"
    assert wrapped._cli_error_fields == {"reason": "missing_module", "module": "litellm", "extra": "evals"}
