"""The published JSON schema of ``futureagi-py run --json`` and ``futureagi-py upload --json`` (e2e CLI-17).

The schema ships in the package as ``fi/experiments/schemas/cli-json.schema.json`` (JSON Schema draft 2020-12). One
``--json`` invocation prints exactly one JSON object on stdout, and it is one of three documents:

- **run** (``futureagi-py run ... --json``): ``{"runs": [...], "exit_code": N}``, one entry per run (a run file may
  declare several), each with its ``label``, ``run_id``, ``name``, ``status``, ``url`` / ``url_note``,
  ``journal_dir``, ``summary`` (``ExperimentResult.summary()``) and ``gate`` (``assert_passing``'s result);
  ``exit_code`` is the command's own exit code.
- **upload** (``futureagi-py upload FILE --json``): the stored run's ``run_id``, ``status``, ``url`` / ``url_note``,
  ``dataset_id``, ``dataset_version_id``, ``items`` and ``summary``.
- **error** (either command, any refusal or failure): ``{"error": {"code", "message", "exit_code"}}``;
  missing extras may also include ``reason``, ``python``, ``required_python``, ``extra`` and ``module``.

A command line that cannot be parsed at all (an unknown flag, a bad ``--error-policy`` value) is argparse's usage
error: exit 2, its message on stderr and nothing on stdout.

``summary`` and ``gate`` are generated from the result models, so the shipped file cannot drift from the code:
``tests/experiments/unit/test_cli_json_schema.py`` fails when the file and :func:`build_schema` differ, and validates
real CLI output against the file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "cli-json.schema.json"
SCHEMA_ID = "urn:futureagi:cli-json:1"


def build_schema() -> dict[str, Any]:
    from fi.experiments.results import GateResult, Summary

    defs: dict[str, Any] = {}
    for model in (Summary, GateResult):
        body = model.model_json_schema(ref_template="#/$defs/{model}", mode="serialization")  # what is printed
        defs.update(body.pop("$defs", {}))
        defs[model.__name__] = body
    url = {"url": {"type": ["string", "null"]}, "url_note": {"type": ["string", "null"]}}
    run_entry = {"type": "object", "additionalProperties": False,
                 "required": ["label", "run_id", "name", "status", "url", "url_note", "journal_dir", "summary", "gate"],
                 "properties": {"label": {"type": "string"}, "run_id": {"type": "string"}, "name": {"type": "string"},
                                "status": {"type": "string"}, **url, "journal_dir": {"type": ["string", "null"]},
                                "summary": {"$ref": "#/$defs/Summary"}, "gate": {"$ref": "#/$defs/GateResult"}}}
    defs["RunReport"] = {"type": "object", "additionalProperties": False, "required": ["runs", "exit_code"],
                         "description": "futureagi-py run --json",
                         "properties": {"runs": {"type": "array", "items": {"$ref": "#/$defs/RunEntry"}},
                                        "exit_code": {"type": "integer"}}}
    defs["RunEntry"] = run_entry
    defs["UploadReport"] = {
        "type": "object", "additionalProperties": False, "description": "futureagi-py upload FILE --json",
        "required": ["run_id", "status", "url", "url_note", "dataset_id", "dataset_version_id", "items", "summary"],
        "properties": {"run_id": {"type": ["string", "null"]}, "status": {"type": "string"}, **url,
                       "dataset_id": {"type": ["string", "null"]}, "dataset_version_id": {"type": ["string", "null"]},
                       "items": {"type": "integer", "minimum": 0}, "summary": {"$ref": "#/$defs/Summary"}}}
    defs["Error"] = {"type": "object", "additionalProperties": False, "required": ["error"],
                     "description": "any refusal or failure of either command under --json",
                     "properties": {"error": {"type": "object", "additionalProperties": False,
                                              "required": ["code", "message", "exit_code"],
                                              "properties": {"code": {"type": "string"}, "message": {"type": "string"},
                                                             "exit_code": {"type": "integer"},
                                                             "reason": {"type": "string", "enum": ["python_version", "missing_module"]},
                                                             "python": {"type": "string", "pattern": r"^[0-9]+\.[0-9]+$"},
                                                             "required_python": {"type": "string", "pattern": r"^[0-9]+\.[0-9]+$"},
                                                             "extra": {"type": "string"},
                                                             "module": {"type": "string", "pattern": r"^[A-Za-z0-9_.]+$"}}}}}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA_ID,
            "title": "futureagi-py run / upload --json output",
            "description": "One JSON object on stdout per --json invocation: a run report, an upload report or an "
                           "error.",
            "oneOf": [{"$ref": "#/$defs/RunReport"}, {"$ref": "#/$defs/UploadReport"}, {"$ref": "#/$defs/Error"}],
            "$defs": dict(sorted(defs.items()))}


def dump(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def load() -> dict[str, Any]:
    """The shipped schema file."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
