"""Bind every score name to a dataset metric before the run is created.

- **Local scores** (functions, trace checks, ``judge()``) become SRV-5 external metrics:
  ``POST datasets/{id}/external-metrics/`` with the scoring definition and ``source_hash`` = sha256
  of the evaluator's source plus its names and settings. The server never runs them. Any edit to the
  evaluator gives a new metric, so a run never mixes scores from two versions of one evaluator: each
  binding journals the fingerprint of its metric body, and a resume whose evaluators no longer make
  the same fingerprints is refused (``evaluators_changed``).
- **Template scores** become a dataset user-eval created once with ``add_user_eval(run=False)``
  under the deterministic name ``sdk-<template>-<hash>`` (``hosted.metric_name``) and found again by
  that name (``_find_user_eval``).

The result maps each score name to its ``metric_id``; the run-create response then gives each
metric's pinned ``evaluator_version_id`` (``check_bindings``).
"""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, Sequence

from fi.experiments.errors import ExperimentError, NotSupportedByServerError


class MetricBindingError(ExperimentError):
    code = "METRIC_BINDING"


@dataclass(frozen=True)
class Binding:
    name: str
    metric_id: str
    kind: str  # "external" | "template"
    output_type: str  # pass_fail | percentage | numeric | template
    evaluator_version_id: Optional[str] = None
    fingerprint: Optional[str] = None  # sha256 of the body that made the metric; a resume compares it

    def to_json(self) -> dict[str, Any]:
        return {"name": self.name, "metric_id": self.metric_id, "kind": self.kind,
                "output_type": self.output_type, "evaluator_version_id": self.evaluator_version_id,
                "fingerprint": self.fingerprint}


def _result(payload: Any) -> Any:
    return payload["result"] if isinstance(payload, Mapping) and "result" in payload else payload


def output_type(ev: Any) -> str:
    """The SRV-5 ``output_type``, fixed before the run: trace checks and ``-> bool`` functions are
    ``pass_fail``; ``judge()`` is ``percentage`` (a 0-1 score); every other local score is ``numeric``."""
    if ev.kind == "trace":
        return "pass_fail"
    if ev.kind == "judge":
        return "percentage"
    fn = getattr(ev, "fn", None)
    if fn is not None:
        try:
            ret = inspect.signature(fn).return_annotation
        except (TypeError, ValueError):
            ret = inspect.Signature.empty
        if ret is bool or ret == "bool":
            return "pass_fail"
    return "numeric"


def source_hash(ev: Any, name: str) -> str:
    """sha256 over the evaluator's code and settings: its source (or qualified name), its score names,
    the score name being bound and its pass threshold."""
    fn = getattr(ev, "fn", None)
    try:
        code = inspect.getsource(fn) if fn is not None else ""
    except (OSError, TypeError):
        code = f"{getattr(fn, '__module__', '')}.{getattr(fn, '__qualname__', repr(fn))}"
    settings = {
        k: v for k, v in sorted(vars(ev).items())
        if not k.startswith("_") and k not in ("fn", "client")
        and isinstance(v, (str, int, float, bool, list, tuple, type(None)))
    }
    material = json.dumps(
        {"class": f"{type(ev).__module__}.{type(ev).__qualname__}", "code": code, "names": list(ev.names),
         "name": name, "settings": settings, "passing_score": getattr(ev, "passing_score", None)},
        sort_keys=True, default=str, separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def external_metric_body(ev: Any, name: str) -> dict[str, Any]:
    kind = output_type(ev)
    threshold = getattr(ev, "passing_score", None)
    body: dict[str, Any] = {"name": name, "output_type": kind, "higher_is_better": True,
                            "source_hash": source_hash(ev, name)}
    if threshold is not None:
        body["pass_threshold"] = float(threshold)
    return body


def _digest(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def fingerprints(evaluators: Sequence[Any]) -> dict[str, str]:
    """``{score name: sha256 of the metric body}``, computed locally (no request): the external
    metric body (its ``source_hash`` covers the evaluator's code and settings) or the template's
    ``add_user_eval`` body (its name carries the mapping/config hash). Equal fingerprints mean the
    same metric; a resume compares them with the journaled bindings."""
    out: dict[str, str] = {}
    for ev in evaluators:
        if ev.kind == "template":
            out[ev.names[0]] = _digest(ev.metric_body())
        else:
            for name in ev.names:
                out[name] = _digest(external_metric_body(ev, name))
    return out


def evaluators_changed(journaled: Mapping[str, "Binding"], evaluators: Sequence[Any]) -> Optional[str]:
    """None when ``evaluators`` make exactly the journaled metrics; else what differs, in words."""
    now = fingerprints(evaluators)
    then = {name: b.fingerprint for name, b in journaled.items()}
    if now == then:
        return None
    parts = []
    for label, names in (("added", sorted(set(now) - set(then))), ("removed", sorted(set(then) - set(now))),
                         ("edited", sorted(n for n in now if n in then and now[n] != then[n]))):
        if names:
            parts.append(f"{label}: {', '.join(names)}")
    return "; ".join(parts)


# get_evals_list?eval_type=user lists a dataset's user evals for the UI picker, so it leaves out every metric whose
# template is hidden there (GetEvalsListView._get_user_evals: template__visible_ui=True, backend @ the recorded revision). The
# simple function templates are hidden: on the stack server 24 system templates have visible_ui false (contains, equals,
# regex, starts_with, ...), so the metric add_user_eval had just made for `contains` was never found (CLI-22 implementation,
# evaluation regression on dsx-e2e-1, 10-22). The compare list (GetCompareEvalsListView) filters only on organization, deleted and
# show_in_sidebar, so it is asked when the first list has no such name. The EvalsClient has no wrapper for it (a SDK maintainers
# file), hence the client's own request method.
COMPARE_EVALS_LIST = "/model-hub/datasets/compare/get-evals-list/"


def _named(payload: Any, name: str) -> Optional[str]:
    evals = payload.get("evals") if isinstance(payload, Mapping) else payload
    hits = [str(e["id"]) for e in evals or [] if isinstance(e, Mapping) and e.get("name") == name]
    return hits[0] if hits else None


def _find_user_eval(client: Any, dataset_id: str, name: str) -> Optional[str]:
    found = _named(_result(client.evals.dataset_evals(dataset_id, eval_type="user", search_text=name)) or {}, name)
    if found is None:
        body = {"eval_type": "user", "dataset_ids": [str(dataset_id)], "search_text": name}
        found = _named(_result(client.evals._raw_request("POST", COMPARE_EVALS_LIST, body=body)) or {}, name)
    return found


# develop_dataset.py add_user_eval @ the recorded revision: a dataset user eval with this name exists → 400 with
# get_error_message("EVAL_NAME_EXISTS") (tfc/utils/error_codes.py: "Eval Template name must be unique").
EVAL_NAME_EXISTS = "Eval Template name must be unique"


def _server_message(exc: Any) -> str:
    payload = getattr(exc, "payload", None)
    if isinstance(payload, Mapping):
        for key in ("message", "detail", "error", "result"):
            if isinstance(payload.get(key), str) and payload[key]:
                return str(payload[key])[:500]
    return str(exc)[:500]


def bind_template(client: Any, dataset_id: str, ev: Any) -> Binding:
    from fi.errors import FutureAGIAPIError

    body = ev.metric_body()
    name = body["name"]
    metric_id = _find_user_eval(client, dataset_id, name)
    if metric_id is None:
        try:
            client.evals.add_dataset_user_eval(dataset_id, body)
        except FutureAGIAPIError as exc:
            message = _server_message(exc)
            if exc.status_code != 400:
                raise
            if EVAL_NAME_EXISTS not in message:  # the server's own reason (mapping, config, template kind)
                raise MetricBindingError(
                    f"the server refused the metric for template {ev.tpl.name!r}: {message}"
                ) from exc
            # the name exists: a concurrent run created it; find it again below
        metric_id = _find_user_eval(client, dataset_id, name)
    if metric_id is None:
        raise MetricBindingError(
            f"the server did not list the metric {name!r} for template {ev.tpl.name!r} after creating it, "
            "so the run cannot pin it"
        )
    return Binding(name=ev.names[0], metric_id=metric_id, kind="template", output_type="template",
                   fingerprint=_digest(body))


def bind_external(client: Any, dataset_id: str, ev: Any, name: str) -> Binding:
    from fi.errors import FutureAGIAPIError

    try:
        res = _result(client.datasets.external_metrics.create(dataset_id, external_metric_body(ev, name)))
    except FutureAGIAPIError as exc:
        if exc.status_code in (404, 405) and not isinstance(exc.payload, Mapping):
            raise NotSupportedByServerError(
                "SRV-5", f"Local scores ({name}) are uploaded as external metrics "
                "(POST /model-hub/datasets/{id}/external-metrics/)."
            ) from exc
        if exc.status_code == 409:
            raise MetricBindingError(
                f"the dataset already has a platform metric named {name!r}; rename the local evaluator "
                "(experiments.evaluator(fn, name=...)) so its scores are not confused with it"
            ) from exc
        raise
    body = external_metric_body(ev, name)
    return Binding(name=name, metric_id=str(res["metric_id"]), kind="external", output_type=output_type(ev),
                   evaluator_version_id=str(res["evaluator_version_id"]), fingerprint=_digest(body))


def bind_all(client: Any, dataset_id: str, evaluators: Sequence[Any]) -> dict[str, Binding]:
    """``{score name: Binding}`` for every score the run produces."""
    out: dict[str, Binding] = {}
    for ev in evaluators:
        if ev.kind == "template":
            out[ev.names[0]] = bind_template(client, dataset_id, ev)
        else:
            for name in ev.names:
                out[name] = bind_external(client, dataset_id, ev, name)
    return out


def check_bindings(bindings: Mapping[str, Binding], header: Mapping[str, Any]) -> dict[str, Binding]:
    """Fill each binding's ``evaluator_version_id`` from the run header; an external metric must be
    pinned at exactly the version its create call returned."""
    pinned = {str(b.get("metric_id")): str(b.get("evaluator_version_id"))
              for b in header.get("evaluator_bindings") or []}
    out: dict[str, Binding] = {}
    for name, b in bindings.items():
        version = pinned.get(b.metric_id)
        if version is None:
            raise MetricBindingError(f"the run was created without the metric for {name!r} ({b.metric_id})")
        if b.evaluator_version_id and b.evaluator_version_id != version:
            raise MetricBindingError(
                f"the run pinned {name!r} at evaluator version {version}, not {b.evaluator_version_id}; "
                "the metric changed while the run was created. Run again."
            )
        out[name] = replace(b, evaluator_version_id=version)
    return out


def bindings_from_plan(raw: Sequence[Mapping[str, Any]]) -> dict[str, Binding]:
    return {str(b["name"]): Binding(str(b["name"]), str(b["metric_id"]), str(b["kind"]), str(b["output_type"]),
                                    b.get("evaluator_version_id"), b.get("fingerprint")) for b in raw}
