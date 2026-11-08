"""Every platform template by name, through the hosted eval API.

- ``get-evals`` (``GET /sdk/api/v1/get-evals/``) gives each template's required keys.
- The default mapping, before the first trial:
  output ← the task output for whichever of ``output | response | hypothesis | conversation |
  text | generated_transcript | generated_audio`` the template names (never guessed when it names
  two); expected ← ``expected | expected_response | expected_text | reference``; input ← the row
  input; any other key ← the row column with exactly that name.
- ``--eval-map EVAL:key=column|@file|==literal`` (Python ``map=``) overrides it. A key still unmapped
  stops the run with ``UnmappedEvalKeysError`` and the exact line to add.
- Template config: ``NAME:k=v,...`` on the CLI, ``template(name, **config)`` in Python.
- Every template needs ``judge_model`` (model configuration) unless its type is known to be deterministic
  (``CustomCodeEval``): ``get-evals`` also returns org-owned templates of other types, which would
  otherwise run on the server's default model. No keys → ``HostedEvalNeedsServerError``; an
  unreachable server → ``ServerUnreachableError`` (exit 3).
- An empty or missing ``output`` from the server is ``status="error"`` with its reason, never a
  silent "assessed" score.
- Each trial calls ``new-eval`` (``POST /sdk/api/v1/new-eval/``) under the run's concurrency.
- No vendored template code: function templates run their own code on the server.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from fi.experiments.errors import (
    HostedEvalNeedsServerError,
    JudgeModelRequiredError,
    UnmappedEvalKeysError,
    UsageError,
    server_unreachable,
)
from fi.experiments.evaluators._base import EvalContext, Evaluator, error_score
from fi.experiments.results import EvalScore

OUTPUT_KEYS = ("output", "response", "hypothesis", "conversation", "text", "generated_transcript", "generated_audio")
EXPECTED_KEYS = ("expected", "expected_response", "expected_text", "reference")
INPUT_KEYS = ("input",)
# Template types that run code, not a model: the only ones that need no judge_model.
DETERMINISTIC_TYPES = frozenset({"CustomCodeEval"})
ROLE_SOURCES = ("output", "expected", "input")
PASS_LABELS = {"passed": True, "pass": True, "true": True, "failed": False, "fail": False, "false": False}


@dataclass(frozen=True)
class Template:
    """``experiments.template(name, map=None, model=None, pass_label=None, **config)``."""

    name: str
    config: Mapping[str, Any] = field(default_factory=dict)
    map: Mapping[str, str] = field(default_factory=dict)
    model: Optional[str] = None
    pass_label: Optional[str] = None


def template(
    name: str,
    *,
    map: Optional[Mapping[str, str]] = None,
    model: Optional[str] = None,
    pass_label: Optional[str] = None,
    **config: Any,
) -> Template:
    """A platform template by name, with optional key mapping, judge model and config."""
    return Template(name, dict(config), dict(map or {}), model, pass_label)


# ---- CLI parsing ---------------------------------------------------------------------------------


def _json_value(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return text


def parse_eval_spec(spec: str) -> Template:
    """``NAME`` or ``NAME:k=v,k2=v2`` (values JSON-typed)."""
    name, _, rest = spec.partition(":")
    if not name:
        raise UsageError(f"--eval {spec!r}: expected NAME[:k=v,...]")
    config: dict[str, Any] = {}
    if rest:
        for part in rest.split(","):
            if "=" not in part:
                raise UsageError(f"--eval {spec!r}: config items are k=v")
            k, v = part.split("=", 1)
            config[k.strip()] = _json_value(v.strip())
    return Template(name, config)


def parse_eval_map(item: str) -> tuple[str, str, str]:
    """``EVAL:key=column|@file|==literal`` → (eval, key, source)."""
    head, sep, source = item.partition("=")
    name, colon, key = head.partition(":")
    if not sep or not colon or not name or not key:
        raise UsageError(f"--eval-map {item!r}: expected EVAL:key=column|@file|==literal")
    return name, key, source


def templates_from_cli(specs: Sequence[str], maps: Sequence[str], pass_labels: Sequence[str]) -> list[Template]:
    tpls = [parse_eval_spec(s) for s in specs]
    by_name = {t.name: t for t in tpls}
    extra_maps: dict[str, dict[str, str]] = {}
    for item in maps:
        name, key, source = parse_eval_map(item)
        if name not in by_name:
            raise UsageError(f"--eval-map names {name!r}, which is not an --eval")
        extra_maps.setdefault(name, {})[key] = source
    labels: dict[str, str] = {}
    for item in pass_labels:
        name, sep, label = item.partition("=")
        if not sep or name not in by_name:
            raise UsageError(f"--pass-label {item!r}: expected EVAL=LABEL for an --eval")
        labels[name] = label
    return [Template(t.name, t.config, {**t.map, **extra_maps.get(t.name, {})}, t.model, labels.get(t.name))
            for t in tpls]


# ---- mapping -------------------------------------------------------------------------------------


@dataclass
class Plan:
    mapping: dict[str, str]  # key -> source ("output" | "expected" | "input" | column | "@file" | "==literal")
    unmapped: list[str]
    note: Optional[str] = None


def default_mapping(required: Sequence[str], columns: Sequence[str], has_expected: bool,
                    overrides: Mapping[str, str]) -> Plan:
    mapping: dict[str, str] = {}
    unmapped: list[str] = []
    out_keys = [k for k in required if k in OUTPUT_KEYS]
    note = None
    if len(out_keys) > 1 and not all(k in overrides for k in out_keys):
        note = f"names {len(out_keys)} output keys ({', '.join(out_keys)}); map them explicitly"
    for key in required:
        if key in overrides:
            mapping[key] = overrides[key]
        elif key in OUTPUT_KEYS and len(out_keys) == 1:
            mapping[key] = "output"
        elif key in EXPECTED_KEYS and has_expected:
            mapping[key] = "expected"
        elif key in INPUT_KEYS:
            mapping[key] = "input"
        elif key in columns:
            mapping[key] = key
        else:
            unmapped.append(key)
    return Plan(mapping, unmapped, note)


def fix_line(name: str, keys: Sequence[str]) -> str:
    cli = " ".join(f"--eval-map {name}:{k}=COLUMN" for k in keys)
    py = ", ".join(f'"{k}": "COLUMN"' for k in keys)
    return f"{cli}    (Python: experiments.template(\"{name}\", map={{{py}}}); COLUMN may be @file or ==literal)"


def metric_name(tpl: Template, mapping: Mapping[str, str], judge_model: Optional[str]) -> str:
    """The deterministic dataset-metric name: ``sdk-<template>-<mapping+config hash>``.

    The server's ``validate_eval_name`` (``model_hub/utils/eval_validators.py``) takes only
    ``^[a-z0-9_-]+$``, no leading or trailing ``-`` / ``_``, no ``_-`` / ``-_``, at most 50 characters, so
    the template's name is folded to that alphabet (the stack server refused ``sdk · contains · <hash>``,
    VM-ROWS B3-1)."""
    # the template's own name is in the hash: two names that fold to one slug ("Is JSON", "is-json") get two
    # metric names, so a metric is never bound to another template's
    material = json.dumps({"template": tpl.name, "map": dict(mapping), "config": dict(tpl.config),
                           "model": judge_model}, sort_keys=True, separators=(",", ":"))
    slug = re.sub(r"[^a-z0-9_]+", "-", tpl.name.lower())
    slug = re.sub(r"[-_]*-[-_]*", "-", slug).strip("-_")[:37].strip("-_") or "template"
    return f"sdk-{slug}-{hashlib.sha256(material.encode()).hexdigest()[:8]}"


def metric_body(record: Mapping[str, Any], tpl: Template, mapping: Mapping[str, str],
                judge_model: Optional[str]) -> dict[str, Any]:
    """The ``add_user_eval`` body (``run=False``: never adds grid columns or evaluates rows); ``binding.bind_template`` sends it.

    ``model`` is sent only for a judge template: the server's ``UserEvalMutationRequestSerializer`` takes
    ``model`` as an optional non-null string, so ``"model": null`` for a function template (``contains``) was
    refused with "model: This field may not be null." and the run stopped with METRIC_BINDING (exit 3;
    CLI-22 implementation, evaluation regression on the stack server)."""
    body: dict[str, Any] = {
        "name": metric_name(tpl, mapping, judge_model),
        "template_id": record["id"],
        "config": {"mapping": dict(mapping), "config": dict(tpl.config)},
        "run": False,
    }
    if judge_model:
        body["model"] = judge_model
    return body


# ---- the evaluator --------------------------------------------------------------------------------


class HostedTemplate(Evaluator):
    kind = "template"
    is_async = True

    def __init__(self, tpl: Template, judge_model: Optional[str]) -> None:
        self.tpl = tpl
        self.judge_model: Optional[str] = tpl.model or judge_model
        label = tpl.name if not tpl.config else f"{tpl.name}:" + ",".join(f"{k}={v}" for k, v in tpl.config.items())
        self.names: tuple[str, ...] = (label,)
        self.record: Optional[Mapping[str, Any]] = None
        self.mapping: dict[str, str] = {}
        self.client: Any = None
        self._files: dict[str, str] = {}

    @property
    def is_judge(self) -> bool:
        """Every template whose type is not known to be deterministic runs on a model."""
        return bool(self.record) and (self.record.get("config") or {}).get("eval_type_id") not in DETERMINISTIC_TYPES

    def describe(self) -> str:
        pairs = ", ".join(f"{k} ← {v}" for k, v in self.mapping.items())
        judge = f"judge: {self.judge_model}; " if self.is_judge else ""
        return f"{self.names[0]} ({judge}{pairs})" if pairs or judge else self.names[0]

    def preflight(self, catalog: Mapping[str, Mapping[str, Any]], columns: Sequence[str], has_expected: bool) -> None:
        record = catalog.get(self.tpl.name)
        if record is None:
            close = sorted(n for n in catalog if self.tpl.name.lower() in n.lower())[:5]
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            raise UsageError(f"no platform template named {self.tpl.name!r}.{hint}")
        self.record = record
        if self.is_judge and not self.judge_model:
            raise JudgeModelRequiredError(self.tpl.name)
        required = list((record.get("config") or {}).get("required_keys") or [])
        plan = default_mapping(required, columns, has_expected, self.tpl.map)
        missing = list(plan.unmapped)
        if plan.note:
            missing += [k for k in required if k in OUTPUT_KEYS and k not in self.tpl.map]
        if missing:
            raise UnmappedEvalKeysError(self.tpl.name, missing, fix_line(self.tpl.name, missing))
        for key, source in plan.mapping.items():
            if source.startswith("@"):
                path = Path(source[1:])
                if not path.is_file():
                    raise UsageError(f"{self.tpl.name}:{key}=@{path}: the file does not exist")
                self._files[source] = path.read_text(encoding="utf-8")
            elif source not in ROLE_SOURCES and not source.startswith("==") and source not in columns:
                raise UsageError(f"{self.tpl.name}:{key}={source}: the dataset has no column {source!r}")
        self.mapping = plan.mapping

    def inputs(self, ec: EvalContext) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, source in self.mapping.items():
            if source == "output":
                value = ec.output
            elif source == "expected":
                value = ec.expected
            elif source == "input":
                value = ec.input
            elif source.startswith("=="):
                value = source[2:]
            elif source.startswith("@"):
                value = self._files[source]
            else:
                value = ec.row[source]
            out[key] = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=repr)
        return out

    def body(self, ec: EvalContext) -> dict[str, Any]:
        body: dict[str, Any] = {"eval_name": self.tpl.name, "inputs": self.inputs(ec)}
        if self.tpl.config:
            # the server reads SDK config under "params" (sdk/utils/evaluations.py _run_eval)
            body["config"] = {"params": dict(self.tpl.config)}
        if self.is_judge:
            body["model"] = self.judge_model
        return body

    def score(self, payload: Any) -> EvalScore:
        result = payload.get("result") if isinstance(payload, Mapping) else None
        try:
            item = result[0]["evaluations"][0]
        except (TypeError, KeyError, IndexError):
            raise ValueError(f"unexpected new-eval response: {str(payload)[:300]}") from None
        output, kind = item.get("output"), str(item.get("output_type") or "")
        reason = item.get("reason") or None
        if output is None or output == "":  # the server sends `value or ""` when the eval failed
            return EvalScore(status="error", explanation=reason or "the eval API returned no output")
        if isinstance(output, str) and output.lower() in PASS_LABELS:
            passed = PASS_LABELS[output.lower()]
            return EvalScore(passed, label=output, explanation=reason)
        if isinstance(output, bool):
            return EvalScore(output, explanation=reason)
        if isinstance(output, (int, float)):
            threshold = (self.record or {}).get("pass_threshold") or ((self.record or {}).get("config") or {}).get(
                "pass_threshold")
            passed = float(output) >= float(threshold) if threshold is not None else None
            return EvalScore(float(output), explanation=reason, passed=passed)
        label = output if isinstance(output, str) else json.dumps(output)
        passed = (label == self.tpl.pass_label) if self.tpl.pass_label else None
        value = (1.0 if passed else 0.0) if passed is not None else None
        return EvalScore(value, label=label, explanation=reason or (kind or None), passed=passed)

    def metric_body(self) -> dict[str, Any]:
        """The dataset user-eval that holds this template's scores on an uploaded run (after preflight)."""
        if self.record is None:
            raise UsageError(f"{self.tpl.name}: the template was not resolved before upload")
        return metric_body(self.record, self.tpl, self.mapping, self.judge_model if self.is_judge else None)

    async def aevaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        from fi.experiments._sync import run_in_daemon_thread

        name = self.names[0]
        try:
            payload = await run_in_daemon_thread(self.client.evals.new_eval, self.body(ec))
            return {name: self.score(payload)}
        except Exception as exc:
            return {name: error_score(exc)}


def as_template_evaluator(ev: Any, *, judge_model: Optional[str]) -> HostedTemplate:
    tpl = ev if isinstance(ev, Template) else parse_eval_spec(str(ev))
    return HostedTemplate(tpl, judge_model)


def catalog_from_response(payload: Any) -> dict[str, Mapping[str, Any]]:
    records = payload.get("result") if isinstance(payload, Mapping) else payload
    if not isinstance(records, list):
        raise ValueError(f"unexpected get-evals response: {str(payload)[:300]}")
    return {r["name"]: r for r in records if isinstance(r, Mapping) and r.get("name")}


def prepare(evaluators: Sequence[Evaluator], *, client: Any, columns: Sequence[str], has_expected: bool) -> None:
    """Pre-flight every template evaluator before the first trial (no template is executed)."""
    hosted = [ev for ev in evaluators if isinstance(ev, HostedTemplate)]
    if not hosted:
        return
    if client is None:
        raise HostedEvalNeedsServerError([ev.tpl.name for ev in hosted])
    try:
        client.auth  # raises when there are no keys
    except Exception:
        raise HostedEvalNeedsServerError([ev.tpl.name for ev in hosted]) from None
    import httpx

    try:
        payload = client.evals.list_sdk_evals()
    except httpx.TransportError as exc:  # refused, DNS, timeout: exit 3 with one line, no traceback
        raise server_unreachable(exc, getattr(client, "base_url", None)) from None
    catalog = catalog_from_response(payload)
    for ev in hosted:
        ev.client = client
        ev.preflight(catalog, columns, has_expected)
