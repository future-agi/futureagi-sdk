"""``futureagi-py evals``: the command group that replaces ai-evaluation's ``fi`` console script."""

from __future__ import annotations

import json

import pytest

from fi._cli.main import main
from tests.evals import _mock_http


def _json(capsys: pytest.CaptureFixture) -> dict:
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_help_lists_evals_under_evaluate(capsys: pytest.CaptureFixture) -> None:
    assert main(["--help"]) == 0
    text = capsys.readouterr().out
    section = text.split("Evaluate:", 1)[1].split("\n\n", 1)[0]
    commands = [line.split()[0] for line in section.splitlines() if line.strip()]
    assert commands.count("evals") == 1 and "run evaluations" in section
    assert commands.count("run") == 1 and commands.count("upload") == 1
    assert "doctor" not in commands and "fi" not in commands
    setup = text.split("Setup:", 1)[1].split("\n\n", 1)[0]
    assert {line.split()[0] for line in setup.splitlines() if line.strip()} == {
        "doctor", "login", "logout",
    }


def test_evals_alone_prints_its_help_and_exits_2(capsys: pytest.CaptureFixture) -> None:
    assert main(["evals"]) == 2
    assert "list" in capsys.readouterr().err


def test_list_json(backend: _mock_http.FakeBackend, capsys: pytest.CaptureFixture) -> None:
    assert main(["evals", "list", "--json"]) == 0
    assert _json(capsys) == {"templates": _mock_http.REGISTRY}
    assert [(c["method"], c["path"], c["x_api_key"]) for c in backend.calls] == [
        ("GET", "/sdk/api/v1/get-evals/", _mock_http.KEY)
    ]


def test_list_text(backend: _mock_http.FakeBackend, capsys: pytest.CaptureFixture) -> None:
    assert main(["evals", "list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "groundedness  (inputs: output, context)"
    assert sorted(line.split()[0] for line in lines) == sorted(r["name"] for r in _mock_http.REGISTRY)


def test_run_json(backend: _mock_http.FakeBackend, capsys: pytest.CaptureFixture) -> None:
    code = main(["evals", "run", "toxicity", "--input", "output=hello", "--input", "extra=dropped",
                 "--model", "turing_flash", "--json"])
    assert code == 0
    out = _json(capsys)
    assert out["template"] == "toxicity"
    assert out["results"][0]["output"] == "Passed" and out["results"][0]["model"] == "turing_flash"
    post = [c for c in backend.calls if c["method"] == "POST"]
    assert len(post) == 1 and post[0]["path"] == "/sdk/api/v1/new-eval/"
    # the registry says toxicity takes only `output`, so the extra input is not sent (as Evaluator does)
    assert post[0]["json"]["eval_name"] == "toxicity" and post[0]["json"]["inputs"] == {"output": "hello"}


def test_run_reads_an_inputs_file_and_flags_override_it(backend, capsys, tmp_path) -> None:
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps({"output": "from file", "context": "Paris is in France."}))
    assert main(["evals", "run", "groundedness", "--inputs", str(path), "--input", "output=from flag"]) == 0
    assert capsys.readouterr().out.startswith("groundedness: Passed (fake reason for groundedness)")
    post = [c for c in backend.calls if c["method"] == "POST"][0]
    assert post["json"]["inputs"] == {"output": "from flag", "context": "Paris is in France."}


@pytest.mark.parametrize("argv, text", [
    (["evals", "run", "toxicity"], "--input KEY=VALUE"),
    (["evals", "run", "toxicity", "--input", "novalue"], "is not KEY=VALUE"),
    (["evals", "run", "toxicity", "--inputs", "/nonexistent/inputs.json"], "cannot read --inputs"),
])
def test_run_usage_errors_exit_2_before_any_request(argv, text, backend, capsys) -> None:
    assert main(argv) == 2
    assert text in capsys.readouterr().err
    assert backend.calls == []


def test_run_inputs_must_be_a_json_object(backend, capsys, tmp_path) -> None:
    path = tmp_path / "inputs.json"
    path.write_text("[1, 2]")
    assert main(["evals", "run", "toxicity", "--inputs", str(path), "--json"]) == 2
    err = _json(capsys)["error"]
    assert err["code"] == "EVALS_USAGE" and err["exit_code"] == 2 and "one JSON object" in err["message"]


def test_run_exits_3_when_the_evaluation_comes_back_without_output(capsys) -> None:
    forbidden = {("POST", "/sdk/api/v1/new-eval/"): lambda call: (403, {"detail": "no"})}
    with _mock_http.serve(_mock_http.FakeBackend(forbidden)):
        assert main(["evals", "run", "toxicity", "--input", "output=x", "--json"]) == 3
    out = _json(capsys)
    assert out["results"][0]["output"] is None and out["results"][0]["reason"]


def test_list_exits_3_with_one_line_when_the_server_fails(capsys) -> None:
    broken = {("GET", "/sdk/api/v1/get-evals/"): lambda call: (500, {"detail": "boom"})}
    with _mock_http.serve(_mock_http.FakeBackend(broken)):
        assert main(["evals", "list"]) == 3
    err = capsys.readouterr().err
    assert err.startswith("error: listing the eval templates failed") and "Traceback" not in err


def test_missing_keys_exit_3_before_any_request(backend, capsys, monkeypatch) -> None:
    monkeypatch.delenv("FI_API_KEY")
    monkeypatch.delenv("FI_SECRET_KEY")
    assert main(["evals", "list", "--json"]) == 3
    err = _json(capsys)["error"]
    assert err["exit_code"] == 3 and "FI_API_KEY" in err["message"]
    assert backend.calls == []


def test_the_group_imports_only_argparse_at_module_level() -> None:
    import ast
    from pathlib import Path

    import fi.evals._cli as cli

    tree = ast.parse(Path(cli.__file__).read_text())
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    names = sorted({a.name for n in top if isinstance(n, ast.Import) for a in n.names}
                   | {n.module for n in top if isinstance(n, ast.ImportFrom)})
    assert names == ["__future__", "argparse", "json", "sys", "typing"]
