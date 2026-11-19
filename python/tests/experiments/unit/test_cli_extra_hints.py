"""CLI extra selection and target-import boundaries, in isolated child processes."""

import json
import os
import subprocess
import sys
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

PYTHON = Path(__file__).resolve().parents[3]
EXPERIMENTS_HINT = 'pip install "futureagi[experiments]"'
EVALS_HINT = 'pip install "futureagi[evals]"'


def _run(tmp_path, source, *, target="agent.py:task", blocked=(), json_output=False):
    (tmp_path / "agent.py").write_text(source)
    (tmp_path / "rows.jsonl").write_text('{"q": 1}\n')
    blocker = tmp_path / "block"
    blocker.mkdir()
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
    env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": os.pathsep.join((str(blocker), str(PYTHON))),
        "HOME": str(tmp_path),
        "FI_BASE_URL": "http://127.0.0.1:9",
        "FI_LOGIN_FILE": str(tmp_path / "no-login.json"),
        "FI_RUN_DIR": str(tmp_path / "runs"),
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    args = [sys.executable, "-m", "fi.experiments", "run", target, "--dataset", "rows.jsonl",
            "--no-upload", "--no-trace", "--no-env-file", "--quiet"]
    if json_output:
        args.append("--json")
    return subprocess.run(args, capture_output=True, text=True, cwd=tmp_path, env=env, timeout=60)


def _assert_evals(out, json_output):
    assert out.returncode == 3, (out.stdout, out.stderr)
    assert "Traceback" not in out.stdout + out.stderr
    assert "futureagi[experiments]" not in out.stdout + out.stderr
    if json_output:
        error = json.loads(out.stdout)["error"]
        assert error["code"] == "MISSING_EXTRA"
        assert error["exit_code"] == 3
        message = error["message"]
    else:
        message = out.stderr
    assert EVALS_HINT in message
    assert "Python 3.11+" in message
    return message


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("module,root", [("fi.evals.llm", "litellm"), ("fi.evals.metrics", "nltk")])
def test_run_local_evals_import_selects_evals(tmp_path, module, root, json_output):
    # A task module that initialises local evaluators before the run starts.
    out = _run(tmp_path, f"import {module}\ndef task(row):\n    return 1\n",
               blocked=("litellm", "nltk"), json_output=json_output)
    message = _assert_evals(out, json_output)
    if sys.version_info >= (3, 11):
        assert f"No module named '{root}'" in message


@pytest.mark.parametrize("target", ["agent.py:task", "agent:task"])
@pytest.mark.parametrize("root", ["litellm", "nltk"])
@pytest.mark.parametrize("json_output", [False, True])
def test_target_import_of_evals_root_is_missing_extra(tmp_path, target, root, json_output):
    out = _run(tmp_path, f"import {root}\ndef task(row):\n    return 1\n", target=target,
               blocked=(root,), json_output=json_output)
    assert f"No module named '{root}'" in _assert_evals(out, json_output)
    if json_output:
        error = json.loads(out.stdout)["error"]
        assert error["reason"] == "missing_module"
        assert error["extra"] == "evals"
        assert error["module"] == root
        assert "python" not in error and "required_python" not in error


@pytest.mark.parametrize("target", ["agent.py:task", "agent:task"])
@pytest.mark.parametrize("json_output", [False, True])
def test_unknown_target_import_is_usage_error(tmp_path, target, json_output):
    root = "fi_cli_nonexistent_user_dependency"
    out = _run(tmp_path, f"import {root}\ndef task(row):\n    return 1\n", target=target,
               blocked=(root,), json_output=json_output)
    assert out.returncode == 2, (out.stdout, out.stderr)
    if json_output:
        error = json.loads(out.stdout)["error"]
        assert error["code"] == "USAGE_ERROR"
        assert error["exit_code"] == 2
        message = error["message"]
    else:
        message = out.stderr
    assert "cannot import" in message and "agent" in message
    assert f"No module named '{root}'" in message
    assert "futureagi[experiments]" not in out.stdout + out.stderr
    assert "Traceback" not in out.stdout + out.stderr


@pytest.mark.parametrize("json_output", [False, True])
def test_python_version_guard_is_missing_extra(monkeypatch, capsys, json_output):
    from fi._cli.main import _dispatch, missing_extra
    from fi.evals._extras import EVALS_REQUIREMENT, require_evals_python

    # Spoof only the guard call, not interpreter startup or third-party imports:
    # globally spoofing 3.10 in sitecustomize changes unrelated compatibility branches.
    with monkeypatch.context() as patch:
        patch.setattr(sys, "version_info", (3, 10, 0, "final", 0))
        with pytest.raises(ImportError) as raised:
            require_evals_python()
    exc = raised.value
    assert str(exc) == EVALS_REQUIREMENT  # the non-CLI library contract is unchanged

    def handler(args):
        raise exc

    args = Namespace(func=handler, json=json_output, install_hint=EXPERIMENTS_HINT)
    wrapped = missing_extra(args, exc)
    assert wrapped.get_error_code() == "MISSING_EXTRA"
    assert wrapped.install_hint == EVALS_HINT
    assert str(wrapped) == EVALS_REQUIREMENT
    assert _dispatch(args) == 3
    output = capsys.readouterr()
    if json_output:
        error = json.loads(output.out)["error"]
        assert error == {
            "code": "MISSING_EXTRA", "message": EVALS_REQUIREMENT, "exit_code": 3,
            "reason": "python_version", "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
            "required_python": "3.11", "extra": "evals",
        }
    else:
        assert EVALS_REQUIREMENT in output.err
        assert output.err == f"error: {EVALS_REQUIREMENT}\n"
    assert "futureagi[experiments]" not in output.out + output.err
    assert "Traceback" not in output.out + output.err


def test_other_import_error_is_not_missing_extra(capsys):
    from fi._cli.main import _dispatch
    from fi.evals._extras import EVALS_REQUIREMENT

    def handler(args):
        # Even a message mentioning the requirement is not the exact version guard.
        raise ImportError(f"cannot import name 'broken'; {EVALS_REQUIREMENT}")

    assert _dispatch(Namespace(func=handler, json=True, install_hint=EXPERIMENTS_HINT)) == 3
    error = json.loads(capsys.readouterr().out)["error"]
    assert error["code"] == "IMPORT_FAILED"
    assert "An installed package failed to import" in error["message"]
    assert EXPERIMENTS_HINT not in error["message"]


@pytest.mark.parametrize("target", ["agent.py:task", "agent:task"])
def test_missing_import_during_task_call_is_not_reclassified(tmp_path, monkeypatch, target):
    from fi.experiments._cli.targets import load_object, parse_target

    (tmp_path / "agent.py").write_text(
        "def task(row):\n    import fi_cli_nonexistent_runtime_dependency\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    # Keep a module target isolated from other in-process target tests.
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    monkeypatch.delitem(sys.modules, "_fi_target_agent", raising=False)
    try:
        task = load_object(parse_target(target))
        with pytest.raises(ModuleNotFoundError) as raised:
            task(None)
        assert raised.value.name == "fi_cli_nonexistent_runtime_dependency"
    finally:
        sys.modules.pop("agent", None)
        sys.modules.pop("_fi_target_agent", None)
