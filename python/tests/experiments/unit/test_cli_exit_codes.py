"""Exit codes: 0 ok, 1 gate, 2 usage, 3 setup, 4 interrupted (subprocess test), 5 errors under CI."""

import json

from tests.experiments.unit.cli_helpers import cli, write_rows


def _agent(tmp_path, body="return row.input.upper()"):
    (tmp_path / "agent.py").write_text(f"def task(row):\n    {body}\n")


def test_ok_and_json(tmp_path):
    _agent(tmp_path)
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}, {"q": "b"}])
    code, out, err = cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--json")
    assert code == 0, err
    doc = json.loads(out)
    assert doc["exit_code"] == 0 and doc["runs"][0]["summary"]["completed"] == 2


def test_gate_fails_with_1(tmp_path):
    (tmp_path / "run_eval.py").write_text(
        "from fi import experiments\n"
        "def wrong(output):\n    return False\n"
        "experiments.run([{'q': 1}], lambda row: 1, [wrong], upload=False)\n"
    )
    code, out, err = cli("run", "run_eval.py", "--fail-under", "0.5", "--quiet")
    assert code == 1 and "wrong" in err


def test_usage_errors_are_2(tmp_path):
    assert cli("run", "--bogus-flag")[0] == 2
    assert cli("run", "https://x/agent", "--dataset", "r.jsonl")[0] == 2
    code, _, err = cli("run", "--", "node", "app.js")
    assert code == 2 and "not a TARGET" in err
    assert cli("run", "agent.py:task")[0] == 2  # no --dataset
    assert cli()[0] == 2


def test_setup_errors_are_3(tmp_path):
    _agent(tmp_path)
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}])
    named = ["--dataset", rows, "--dataset-name", "rows"]  # an uploaded rows file needs a name (S3 (a))
    code, out, err = cli("run", "agent.py:task", *named)  # upload needs keys; there are none
    assert code == 3 and "--no-upload" in err and "upload=False" not in err
    code, out, err = cli("run", "agent.py:task", *named, "--json")
    assert code == 3 and json.loads(out)["error"]["code"] == "MISSING_AUTH"


def test_errors_exit_5_under_ci(tmp_path, monkeypatch):
    _agent(tmp_path, "raise RuntimeError('bad key')")
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}, {"q": "b"}])
    assert cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--quiet")[0] == 0
    monkeypatch.setenv("CI", "true")
    assert cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--quiet")[0] == 5
    assert cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--quiet", "--max-error-rate", "1")[0] == 0


def test_env_file_loaded_environment_wins(tmp_path, monkeypatch):
    for name in ("MY_VAR", "OTHER"):  # restored (unset) after the test
        monkeypatch.setenv(name, "x")
        monkeypatch.delenv(name)
    (tmp_path / "agent.py").write_text("import os\ndef task(row):\n    return os.environ.get('MY_VAR')\n")
    (tmp_path / ".env").write_text("MY_VAR=from-dotenv\nOTHER=1\n")
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}])
    code, out, err = cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--json")
    assert code == 0 and json.loads(out)["runs"][0]["status"] == "no_upload"
    assert "loaded" in err and "from-dotenv" not in err
    import os

    assert os.environ["MY_VAR"] == "from-dotenv"
    monkeypatch.setenv("MY_VAR", "real")
    cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--quiet")
    assert os.environ["MY_VAR"] == "real"
