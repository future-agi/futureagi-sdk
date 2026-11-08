"""Wave 2g (e2e CLI-17): the published JSON schema of ``futureagi-py run --json`` / ``futureagi-py upload --json``.

The schema ships as ``fi/experiments/schemas/cli-json.schema.json``. These tests keep the file equal to what the code
builds (titles and descriptions aside, which pydantic versions word differently), check that it is a valid draft
2020-12 schema, and validate real CLI output against the shipped file: a run, a run file with two runs and a failing
gate, a refusal, and an upload to the contract server. No network, no model."""

import json

import jsonschema
import pytest

from fi.experiments._cli import json_schema
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for


def _shape(node):
    """The schema without "title" / "description" (wording only)."""
    if isinstance(node, dict):
        return {k: _shape(v) for k, v in node.items() if k not in ("title", "description")}
    if isinstance(node, list):
        return [_shape(v) for v in node]
    return node


def _validator():
    schema = json_schema.load()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _one_json_line(out):
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) == 1, out[-500:]
    return json.loads(lines[0])


def test_the_shipped_schema_is_what_the_code_builds_and_is_valid():
    assert json_schema.SCHEMA_PATH.is_file()
    assert _shape(json_schema.load()) == _shape(json_schema.build_schema())
    assert json_schema.load()["$id"] == "urn:futureagi:cli-json:1"
    _validator()


def _run_file(tmp_path):
    (tmp_path / "run_eval.py").write_text(
        "from fi import experiments\n"
        "def ok(output):\n    return output == 1\n"
        "rows = [{'q': 1}, {'q': 1}, {'q': 0}]\n"
        "experiments.run(rows, lambda row: row.input, [ok], name='first', upload=False, trace=False)\n"
        "experiments.run(rows, lambda row: row.input, [ok], name='second', limit=1, upload=False, trace=False)\n")


def test_run_json_output_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_file(tmp_path)
    v = _validator()
    code, out, _ = cli("run", "run_eval.py", "--json", "--no-env-file")
    doc = _one_json_line(out)
    v.validate(doc)
    assert code == 0 and doc["exit_code"] == 0 and [r["label"] for r in doc["runs"]] == ["first", "second"]
    code, out, _ = cli("run", "run_eval.py", "--json", "--fail-under", "0.9", "--no-env-file")  # first: 2 of 3
    doc = _one_json_line(out)
    v.validate(doc)
    assert code == 1 and doc["exit_code"] == 1 and doc["runs"][0]["gate"]["passed"] is False


def test_an_error_under_json_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    v = _validator()
    code, out, _ = cli("run", "frobnicate", "--json", "--no-env-file")
    doc = _one_json_line(out)
    v.validate(doc)
    assert code == 2 and doc["error"]["code"] == "UNKNOWN_TARGET" and doc["error"]["exit_code"] == 2


@pytest.mark.parametrize("markers", [
    {"reason": "python_version", "python": "3.10", "required_python": "3.11", "extra": "evals"},
    {"reason": "missing_module", "module": "litellm", "extra": "evals"},
    {"reason": "missing_module", "module": "unknown"},
    {},
])
def test_missing_extra_markers_validate(markers):
    _validator().validate({"error": {"code": "MISSING_EXTRA", "message": "missing dependency", "exit_code": 3,
                                   **markers}})


@pytest.mark.parametrize("markers", [
    {"reason": "unknown"}, {"python": "3.10.0"}, {"required_python": "3.11+"}, {"module": "bad-name"},
])
def test_missing_extra_marker_value_constraints(markers):
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate({"error": {"code": "MISSING_EXTRA", "message": "missing dependency", "exit_code": 3,
                                       **markers}})


def test_upload_json_output_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    server = ContractServer()
    (tmp_path / "rows.jsonl").write_text(json.dumps({"id": "T1", "question": "where is order 1?"}) + "\n")
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "T1", "output": "shipped"}) + "\n")
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=client_for(server), **k))
    code, out, _ = cli("upload", "results.jsonl", "--dataset", "rows.jsonl", "--dataset-name", "support", "--json",
                       "--no-env-file")
    doc = _one_json_line(out)
    _validator().validate(doc)
    assert code == 0 and doc["items"] == 1 and doc["run_id"]


@pytest.mark.parametrize("bad", [{"runs": []}, {"runs": [], "exit_code": 0, "extra": 1},
                                 {"error": {"code": "X", "message": "m"}}, {"run_id": "r", "status": "completed"}])
def test_the_schema_refuses_documents_of_another_shape(bad):
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bad)
