"""An in-memory stand-in for the platform routes an uploaded run uses, for unit tests only.

PROVENANCE (read before trusting a green unit test):
- NOT recorded from a server. The E2E VM (dsx-e2e-1) was unreachable when this was written
  (2026-10-22: the staging gcloud login had expired), so nothing could be recorded.
- Request/response shapes come from:
  - the SDK's OpenAPI spec ``openapi/sdk/generated/futureagi-sdk.openapi.json`` (backend revision
    the recorded revision, the stack the SDK is generated from): dataset versions, experiment-run create and
    results ingest. Request bodies are checked against those component schemas (required keys, no
    unknown keys) by ``check_body``;
  - backend ``feat/experiments-sdk-backend`` @ the recorded revision (``wt-backend/PR-DRAFT.md`` section, section and the
    serializers/services): SRV-3 run read + items, SRV-5 external metrics (strict body);
  - backend ``dataset_version_service.py`` @ the recorded revision: the per-item content hash over
    ``_strict_json`` values (an integral float is hashed and stored as an int: JSONB reads ``2.0``
    back as ``2``), ``external_id`` inheritance from the parent version, "not idempotent" version
    create; ``views/dataset_versions.py``: versions are listed newest first (``-created_at, -id``);
  - backend ``tfc/utils/api_errors.py`` ``build_error_envelope``: an error body carries the message
    under ``message`` / ``detail`` / ``error`` / ``result``; ``tfc/utils/error_codes.py``:
    ``EVAL_NAME_EXISTS`` ("Eval Template name must be unique"), ``DATASET_EXIST_IN_ORG`` ("A dataset
    with this name already exists in your organization."), raised by ``validate_dataset_name_unique``
    over every dataset of the org, while ``get-datasets-names`` lists only some sources;
  - ``develop_dataset.py`` @ the recorded revision: ``add_user_eval`` answers "success" (no id), user evals are
    listed by ``get_evals_list?eval_type=user`` with ``id`` / ``name``; ``get-dataset-table`` rows are
    ``{row_id, <column id>: {cell_value}}`` with ``column_config`` ``{id, name, origin_type}``.
- Replace with recordings from the E2E stack server in wave 1 (SDK-01..06, SDK-24, SDK-34, SDK-35).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import re
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import httpx

SPEC = json.loads((Path(__file__).resolve().parents[4] / "openapi/sdk/generated/futureagi-sdk.openapi.json").read_text())
SCHEMAS = SPEC["components"]["schemas"]
EXTERNAL_METRIC_FIELDS = {"name", "output_type", "higher_is_better", "pass_threshold", "source_hash"}


def check_body(schema: str, body: Any, path: str = "body") -> None:
    """Required keys present, no unknown keys where the schema forbids them (recursively via $ref)."""
    spec = SCHEMAS[schema]
    assert isinstance(body, dict), f"{path} must be an object"
    missing = [k for k in spec.get("required", []) if k not in body]
    assert not missing, f"{path} lacks {missing}"
    props = spec.get("properties", {})
    if spec.get("additionalProperties") is False:
        unknown = [k for k in body if k not in props]
        assert not unknown, f"{path} has unknown keys {unknown}"
    for key, value in body.items():
        sub = props.get(key, {})
        ref = (sub.get("items") or {}).get("$ref") if sub.get("type") == "array" else sub.get("$ref")
        if ref and value is not None:
            name = ref.rsplit("/", 1)[-1]
            for i, v in enumerate(value if isinstance(value, list) else [value]):
                check_body(name, v, f"{path}.{key}[{i}]")


def strict_json(value: Any) -> Any:
    """The backend's ``_strict_json`` value rule (dataset_version_service.py @ the recorded revision), copied from
    the backend, not from the SDK: ``type(value) is float`` and integral → ``int(Decimal(str(value)))``."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        assert math.isfinite(value), "Non-finite numbers are not valid JSON."
        return int(Decimal(str(value))) if value.is_integer() else value
    if type(value) is list:
        return [strict_json(v) for v in value]
    if type(value) is dict:
        return {k: strict_json(v) for k, v in value.items()}
    raise AssertionError("Value is not strict JSON.")


def item_hash(item: dict) -> str:
    payload = {"input": strict_json(item["input"]), "expected": strict_json(item.get("expected")),
               "metadata": strict_json(item.get("metadata") or {})}
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def ok(result: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json={"status": True, "result": result})


# tfc/utils/api_errors.py ERROR_TYPE_BY_STATUS / DEFAULT_CODE_BY_STATUS (others: "api_error" / "error")
_TYPE = {400: "validation_error", 401: "authentication_error", 403: "permission_error", 404: "not_found",
         409: "conflict", 429: "rate_limit", 500: "server_error", 503: "service_unavailable", 504: "timeout"}
_CODE = {400: "invalid", 401: "not_authenticated", 403: "permission_denied", 404: "not_found", 409: "conflict",
         429: "rate_limited", 500: "server_error", 503: "service_unavailable", 504: "timeout"}


def err(status: int, message: str) -> httpx.Response:
    """``build_error_envelope``'s shape for a string message."""
    return httpx.Response(status, json={"status": False, "type": _TYPE.get(status, "api_error"),
                                        "code": _CODE.get(status, "error"), "detail": message, "message": message,
                                        "error": message, "result": message})


NGINX_REASONS = {301: "Moved Permanently", 401: "Authorization Required", 403: "Forbidden", 404: "Not Found",
                 413: "Request Entity Too Large", 502: "Bad Gateway", 503: "Service Temporarily Unavailable",
                 504: "Gateway Time-out"}


def gateway_page(status: "int | httpx.Response") -> httpx.Response:
    """What nginx answers for the server behind it (down, or refused by nginx itself): its own default HTML page,
    never the API's JSON envelope (the stack's nginx router did this in e2e SDK-34, run 20261023T101220Z-vm). A
    ready ``httpx.Response`` is answered as it is (a web app's page, a JSON-speaking gateway)."""
    if isinstance(status, httpx.Response):
        return status
    reason = NGINX_REASONS.get(status, "Error")
    body = (f"<html>\r\n<head><title>{status} {reason}</title></head>\r\n<body>\r\n<center><h1>{status} {reason}"
            "</h1></center>\r\n<hr><center>nginx/1.27.2</center>\r\n</body>\r\n</html>\r\n")
    headers = {"content-type": "text/html"}
    if 300 <= status < 400:
        headers["location"] = "https://srv.test/"
    return httpx.Response(status, text=body, headers=headers)


EVAL_NAME_EXISTS = "Eval Template name must be unique"
DATASET_EXIST_IN_ORG = "A dataset with this name already exists in your organization."


class ContractServer:
    def __init__(self) -> None:
        self.datasets: dict[str, dict] = {}
        self.metrics: dict[str, dict] = {}  # metric_id -> record (external or template)
        self.runs: dict[str, dict] = {}
        self.requests: list[tuple[str, str, Any]] = []
        self.queries: list[tuple[str, str, dict]] = []  # (method, path, query parameters) of every request
        self.items_page: Optional[int] = None  # serve at most this many run items per page: paging is exercised
        self.experiments: dict[str, dict] = {}  # experiment_id -> {"name", "dataset_id"} (the experiment detail read)
        # the hosted eval API answers get-evals (this response) and new-eval only when a catalog is set
        self.eval_catalog: Optional[dict] = None
        self.eval_calls: list[dict] = []  # new-eval bodies, in call order
        self.fail_ingest: list[int] = []  # statuses to answer the next ingest calls with
        self.fail_create: list[int] = []  # statuses to answer the next run-create calls with
        # statuses a GATEWAY answers the next ingest / run-create calls with: an HTML page, not the API's JSON
        # (nginx in front of a restarting server: e2e SDK-34 behind the stack's router, implementation L-VM2c)
        self.gateway_ingest: list = []  # a status (nginx's page for it) or a ready httpx.Response
        self.gateway_create: list = []
        # template ids hidden from the UI picker (EvalTemplate.visible_ui false: contains, equals, regex, ... on the
        # stack server). get_evals_list?eval_type=user leaves their metrics out; the compare list does not.
        self.hidden_templates: set[str] = set()
        self.clock = 0
        # the deployment's frontend URL (SRV-4 app_url); None = a server with no frontend URL set (app_url null)
        self.app_url_base: Optional[str] = None

    # ---- seeding ----
    def add_dataset(self, name: str, table: Optional[list[dict]] = None, *, listed: bool = True) -> str:
        """``listed=False``: a source ``get-datasets-names`` does not list (scenario, knowledge base,
        experiment snapshot); its name is still taken in the org."""
        did = str(uuid.uuid4())
        cols = []
        for rec in table or []:
            for k in rec:
                if k not in [c["name"] for c in cols]:
                    cols.append({"id": str(uuid.uuid4()), "name": k, "origin_type": "OTHERS"})
        rows = [{"row_id": str(uuid.uuid4()), **{c["id"]: {"cell_value": rec.get(c["name"])} for c in cols}}
                for rec in table or []]
        self.datasets[did] = {"id": did, "name": name, "versions": [], "columns": cols, "rows": rows, "listed": listed}
        return did

    def count(self, method: str, pattern: str) -> int:
        return sum(1 for m, p, _ in self.requests if m == method and re.fullmatch(pattern, p))

    # ---- dispatch ----
    def __call__(self, request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        body = json.loads(request.content) if request.content else None
        self.requests.append((method, path, body))
        q = dict(request.url.params)
        self.queries.append((method, path, q))
        if path == "/model-hub/develops/get-datasets-names/":
            return ok({"datasets": [{"dataset_id": d["id"], "name": d["name"]} for d in self.datasets.values()
                                    if d["listed"]]})
        if path == "/model-hub/develops/create-empty-dataset/":
            if any(d["name"] == body["new_dataset_name"] for d in self.datasets.values()):
                return err(400, DATASET_EXIST_IN_ORG)
            did = self.add_dataset(body["new_dataset_name"])
            return ok({"message": "created", "dataset_id": did, "dataset_name": body["new_dataset_name"]})
        m = re.fullmatch(r"/model-hub/develops/([^/]+)/get-dataset-table/", path)
        if m:
            d = self.datasets[m.group(1)]
            return ok({"metadata": {"dataset_name": d["name"], "total_rows": len(d["rows"]), "total_pages": 1},
                       "column_config": d["columns"] + [{"id": "ev", "name": "score", "origin_type": "evaluation"}],
                       "table": [{**r, "ev": {"cell_value": "0.5"}} for r in d["rows"]]})
        m = re.fullmatch(r"/model-hub/datasets/([^/]+)/versions/", path)
        if m:
            return self._versions(m.group(1), method, body, q)
        m = re.fullmatch(r"/model-hub/datasets/([^/]+)/versions/([^/]+)/", path)
        if m:
            return self._version_detail(m.group(1), m.group(2), q)
        m = re.fullmatch(r"/model-hub/datasets/([^/]+)/external-metrics/", path)
        if m and method == "POST":
            return self._external_metric(m.group(1), body)
        m = re.fullmatch(r"/model-hub/develops/([^/]+)/get_evals_list/", path)
        if m:  # GetEvalsListView._get_user_evals: template__visible_ui=True
            evals = [{"id": k, "name": v["name"], "template_id": v.get("template_id")} for k, v in self.metrics.items()
                     if v["dataset"] == m.group(1) and v["kind"] == "template"
                     and v.get("template_id") not in self.hidden_templates and q.get("search_text", "") in v["name"]]
            return ok({"evals": evals, "eval_recommendations": []})
        if path == "/model-hub/datasets/compare/get-evals-list/" and method == "POST":
            # GetCompareEvalsListView._get_user_evals: organization, deleted, show_in_sidebar; no visible_ui filter
            if body.get("eval_type") != "user" or not body.get("dataset_ids"):
                return err(400, "Invalid or missing eval type")
            evals = [{"id": k, "name": v["name"], "template_name": v.get("template_id")} for k, v in self.metrics.items()
                     if v["dataset"] in body["dataset_ids"] and v["kind"] == "template"
                     and body.get("search_text", "") in v["name"]]
            return ok({"evals": evals})
        m = re.fullmatch(r"/model-hub/develops/([^/]+)/add_user_eval/", path)
        if m:
            if any(v["name"] == body["name"] and v["dataset"] == m.group(1) for v in self.metrics.values()):
                return err(400, EVAL_NAME_EXISTS)
            # UserEvalMutationRequestSerializer @ the recorded revision: model = CharField(max_length=100, required=False,
            # allow_blank=True) (no allow_null), name = CharField(max_length=50): what the VM refused (CLI-22 implementation)
            if "model" in body and not isinstance(body["model"], str):
                return err(400, "model: This field may not be null.")
            if len(body["name"]) > 50:
                return err(400, "name: Ensure this field has no more than 50 characters.")
            # UserEvalSerializer.validate_name -> eval_validators.validate_eval_name (what refused "sdk · contains · …")
            n = body["name"]
            if (not re.fullmatch(r"[a-z0-9_-]+", n) or n[0] in "-_" or n[-1] in "-_" or "_-" in n or "-_" in n):
                return err(400, "Name can only contain lowercase letters, numbers, hyphens (-), or underscores (_). "
                                "No spaces allowed.")
            assert body["run"] is False
            self.metrics[str(uuid.uuid4())] = {"name": body["name"], "dataset": m.group(1), "kind": "template",
                                               "template_id": body["template_id"], "version": str(uuid.uuid4()),
                                               "config": body.get("config") or {}, "model": body.get("model")}
            return ok("success")
        if path == "/model-hub/experiment-runs/" and method == "POST":
            return self._create_run(body)
        m = re.fullmatch(r"/model-hub/experiment-runs/([^/]+)/results/", path)
        if m:
            return self._ingest(m.group(1), body)
        m = re.fullmatch(r"/model-hub/experiment-runs/([^/]+)/", path)
        if m and method == "GET":
            return self._read_run(m.group(1))
        m = re.fullmatch(r"/model-hub/experiment-runs/([^/]+)/items/", path)
        if m and method == "GET":
            return self._items(m.group(1), q)
        m = re.fullmatch(r"/model-hub/experiments/v2/([^/]+)/", path)
        if m and method == "GET":
            return self._experiment(m.group(1))
        if self.eval_catalog is not None and path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=self.eval_catalog)
        if self.eval_catalog is not None and path == "/sdk/api/v1/new-eval/" and method == "POST":
            self.eval_calls.append(body)
            return httpx.Response(200, json={"result": [{"evaluations": [{"output": "Passed", "reason": "ok"}]}]})
        return err(404, f"no route {method} {path}")

    def _experiment(self, experiment_id: str) -> httpx.Response:
        """``ExperimentsTableV2View.get`` (``ExperimentDetailV2Serializer``): the fields a run read needs."""
        e = self.experiments.get(experiment_id)
        if e is None:
            return err(404, "Experiment not found")
        return ok({"id": experiment_id, "name": e["name"], "description": None, "dataset_id": e["dataset_id"],
                   "column_id": None, "experiment_type": "llm", "status": "Completed", "snapshot_dataset_id": None,
                   "prompt_configs": [], "agent_configs": [], "user_eval_metrics": [],
                   "created_at": "2026-10-22T00:00:00Z"})

    # ---- dataset versions ----
    def _versions(self, did: str, method: str, body: Any, q: dict) -> httpx.Response:
        d = self.datasets.get(did)
        if d is None:
            return err(404, "Dataset not found.")
        if method == "GET":
            off, lim = int(q.get("offset", 0)), int(q.get("limit", 100))
            vs = [self._version_read(v) for v in reversed(d["versions"])]  # newest first, as the view orders
            return ok({"dataset_id": did, "versions": vs[off:off + lim], "limit": lim, "offset": off,
                       "has_more": off + lim < len(vs)})
        check_body("DatasetVersionCreate", body)
        parent = next((v for v in d["versions"] if v["id"] == body.get("parent_version_id")), None)
        inherit = {i["external_id"]: i["example_id"] for i in (parent or {}).get("items", []) if i.get("external_id")}
        inherit_legacy = {i["legacy_row"]: i["example_id"] for i in (parent or {}).get("items", []) if i.get("legacy_row")}
        items = []
        for it in body["items"]:
            ext, legacy = it.get("external_id"), it.get("legacy_row_id")
            example = it.get("example_id") or inherit.get(ext) or (
                inherit_legacy.get(legacy) or (str(uuid.uuid5(uuid.NAMESPACE_URL, legacy)) if legacy else str(uuid.uuid4())))
            items.append({"id": str(uuid.uuid4()), "example_id": example, "external_id": ext, "legacy_row": legacy,
                          "input": strict_json(it["input"]), "expected": strict_json(it.get("expected")),
                          "metadata": strict_json(it.get("metadata") or {}), "content_hash": item_hash(it)})
        self.clock += 1
        # half a second apart: DRF prints microseconds only when non-zero, so "…:01Z" (older) sorts
        # after "…:01.500000Z" (newer) as a string, and only a parsed time orders them
        at = datetime.datetime(2026, 10, 22, tzinfo=datetime.timezone.utc) + datetime.timedelta(
            milliseconds=500 * self.clock)
        v = {"id": str(uuid.uuid4()), "dataset": did, "parent_version": body.get("parent_version_id"),
             "metadata": body.get("metadata") or {}, "created_at": at.isoformat().replace("+00:00", "Z"), "items": items}
        d["versions"].append(v)
        return ok(self._version_read(v), 201)  # the spec's createDatasetVersion answers 201

    @staticmethod
    def _version_read(v: dict) -> dict:
        return {k: v[k] for k in ("id", "dataset", "parent_version", "metadata", "created_at")} | {"item_count": len(v["items"])}

    def _version_detail(self, did: str, vid: str, q: dict) -> httpx.Response:
        v = next((v for v in self.datasets.get(did, {}).get("versions", []) if v["id"] == vid), None)
        if v is None:
            return err(404, "Dataset version not found.")
        off, lim = int(q.get("offset", 0)), min(int(q.get("limit", 100)), 2)  # a small server cap: paging is exercised
        return ok({"version": self._version_read(v), "items": v["items"][off:off + lim], "limit": lim, "offset": off,
                   "has_more": off + lim < len(v["items"])})

    # ---- metrics and runs ----
    def _external_metric(self, did: str, body: dict) -> httpx.Response:
        unknown = set(body) - EXTERNAL_METRIC_FIELDS
        if unknown or not re.fullmatch(r"[0-9a-f]{64}", body.get("source_hash", "")):
            return err(400, f"invalid external metric: {sorted(unknown) or 'source_hash'}")
        key = (did, body["name"], body["source_hash"], body["output_type"], body.get("higher_is_better", True),
               body.get("pass_threshold"))
        for mid, rec in self.metrics.items():
            if rec.get("key") == key:
                return ok({"metric_id": mid, "evaluator_version_id": rec["version"], "created": False})
        if any(r["dataset"] == did and r["name"] == body["name"] and r["kind"] == "template" for r in self.metrics.values()):
            return err(409, "A non-external metric with this name exists on the dataset.")
        mid = str(uuid.uuid4())
        self.metrics[mid] = {"name": body["name"], "dataset": did, "kind": "external", "key": key, "version": str(uuid.uuid4())}
        return ok({"metric_id": mid, "evaluator_version_id": self.metrics[mid]["version"], "created": True})

    def _app_url(self, b: dict) -> Optional[str]:
        """SRV-4's run_app_url: the dataset's Experiments tab from the frontend URL; None when none is set."""
        if not self.app_url_base:
            return None
        did = next((d["id"] for d in self.datasets.values()
                    if any(v["id"] == b["dataset_version_id"] for v in d["versions"])), None)
        return f"{self.app_url_base.rstrip('/')}/dashboard/develop/{did}?tab=experiments&run={b['run_id']}"

    def _header(self, run: dict) -> dict:
        """A run made in the app can be seeded with its own ``status``, ``task_kind`` and ``completed_at``, and with
        ``header_dataset_id`` (a header that also names the version's dataset, as a later server may send)."""
        b = run["body"]
        done = all((e["example_id"], e.get("trial_number", 1)) in run["items"] for e in b["expected_items"])
        status = run.get("status") or ("completed" if done else ("running" if run["items"] else "queued"))
        header = {"id": b["run_id"], "app_url": self._app_url(b),
                  "dataset_version_id": b["dataset_version_id"], "experiment_id": b.get("experiment_id"),
                  "task_kind": run.get("task_kind", "external"), "status": status,
                  "expected_items": b["expected_items"],
                  "evaluator_bindings": [self._binding(m) for m in b.get("evaluator_metric_ids", [])],
                  "model_config": b.get("model_config", {}), "metadata": b.get("metadata", {}),
                  "started_at": None, "completed_at": run.get("completed_at"), "created_at": "2026-10-22T00:00:00Z",
                  "updated_at": "2026-10-22T00:00:00Z"}
        if run.get("header_dataset_id"):
            header["dataset_id"] = next(d["id"] for d in self.datasets.values()
                                        if any(v["id"] == b["dataset_version_id"] for v in d["versions"]))
        return header

    def _binding(self, metric_id: str) -> dict:
        """``_evaluator_snapshots``: ``binding_config`` and ``binding_model`` are the metric's own config and model."""
        rec = self.metrics[metric_id]
        external = rec["kind"] == "external"
        return {"metric_id": metric_id, "evaluator_version_id": rec["version"],
                "template_id": rec.get("template_id") or str(uuid.uuid5(uuid.NAMESPACE_URL, metric_id)),
                "version_number": 1, "binding_config": rec.get("config") or {}, "binding_model": rec.get("model"),
                "prompt_messages": [],
                "config_snapshot": {"external": _external_snapshot(rec)} if external else {}, "criteria": None,
                "model": None, "output_type_normalized": None, "pass_threshold": None, "choice_scores": None}

    def _create_run(self, body: dict) -> httpx.Response:
        if self.gateway_create:
            return gateway_page(self.gateway_create.pop(0))
        if self.fail_create:
            return err(self.fail_create.pop(0), "temporarily unavailable")
        check_body("ExternalRunCreateRequest", body)
        run = self.runs.get(body["run_id"])
        if run is not None:
            if run["body"] != body:
                return err(409, "Run id already exists with a different payload.")
            return ok(self._header(run))
        for mid in body.get("evaluator_metric_ids", []):
            if mid not in self.metrics:
                return err(400, f"unknown metric {mid}")
        self.runs[body["run_id"]] = {"body": body, "items": {}}
        return ok(self._header(self.runs[body["run_id"]]))

    def _ingest(self, run_id: str, body: dict) -> httpx.Response:
        if self.gateway_ingest:
            return gateway_page(self.gateway_ingest.pop(0))
        if self.fail_ingest:
            return err(self.fail_ingest.pop(0), "temporarily unavailable")
        check_body("ExternalRunResultsRequest", body)
        assert 1 <= len(body["items"]) <= 100
        assert len(json.dumps(body).encode()) <= 2 * 1024 * 1024
        run = self.runs[run_id]
        planned = {(e["example_id"], e.get("trial_number", 1)) for e in run["body"]["expected_items"]}
        pinned = {(m, self.metrics[m]["version"]) for m in run["body"].get("evaluator_metric_ids", [])}
        staged = {}
        for it in body["items"]:
            ident = (it["example_id"], it.get("trial_number", 1))
            if ident not in planned:
                return err(400, f"{ident} is not in the plan")
            for ref in it.get("score_refs", []):
                if (ref["metric_id"], ref["evaluator_version_id"]) not in pinned:
                    return err(409, "score ref is not pinned by this run")
            have = run["items"].get(ident)
            if have is None and (run.get("completed_at") or run.get("status") in ("completed", "failed", "cancelled")):
                return err(409, "terminal run cannot accept a new result identity")  # experiment_run_ingestion
            if have is not None and have["_payload"] != it:
                return err(409, "Result receipt conflict.")
            staged[ident] = {**it, "trial_number": ident[1], "_payload": it}
        run["items"].update(staged)
        receipts = [{k: v for k, v in i.items() if k in ("example_id", "trial_number", "receipt_key", "status",
                                                          "trace_id", "root_span_id", "score_refs")} | {"id": str(uuid.uuid4())}
                    for i in staged.values()]
        return ok({"run": self._header(run), "items": receipts})

    def _read_run(self, run_id: str) -> httpx.Response:
        """``ExperimentRunReadSerializer``: the run header plus ordinal, label, plan_size and item_counts."""
        run = self.runs.get(run_id)
        if run is None:
            return err(404, "Experiment run not found.")
        h = self._header(run)
        counts = {s: sum(1 for i in run["items"].values() if i["status"] == s) for s in ITEM_STATUSES}
        ordinal = list(self.runs).index(run_id) + 1
        return ok({**h, "ordinal": ordinal, "label": f"#{ordinal}", "plan_size": len(h["expected_items"]),
                   "item_counts": {**counts, "not_started": len(h["expected_items"]) - len(run["items"])}})

    def _items(self, run_id: str, q: dict) -> httpx.Response:
        """``ExperimentRunItemsView``: recorded items in plan order, ``status`` a comma-separated filter, ``limit``
        1-500, ``limit * max_value_bytes`` at most 4 MiB (``ExperimentRunItemsQuerySerializer``)."""
        run = self.runs.get(run_id)
        if run is None:
            return err(404, "Experiment run not found.")
        statuses = [s.strip() for s in q.get("status", "").split(",") if s.strip()]
        unknown = sorted(set(statuses) - set(ITEM_STATUSES))
        if unknown:
            return err(400, f"Unknown item status: {', '.join(unknown)}.")
        off, lim, cap = int(q.get("offset", 0)), int(q.get("limit", 100)), int(q.get("max_value_bytes", 4096))
        if not 1 <= lim <= 500 or not 0 <= cap <= 262144 or lim * cap > 4194304 or off < 0:
            return err(400, "limit must be 1-500 and limit * max_value_bytes must not exceed 4194304.")
        items = sorted(run["items"].values(), key=lambda i: (i["example_id"], i["trial_number"]))
        items = [i for i in items if not statuses or i["status"] in statuses]
        served = min(lim, self.items_page or lim)
        return ok({"run_id": run_id, "run_status": self._header(run)["status"],
                   "items": [_item_read(i, cap) for i in items[off:off + served]], "total": len(items),
                   "limit": lim, "offset": off, "has_more": off + served < len(items)})


ITEM_STATUSES = ("pending", "running", "completed", "failed", "skipped")  # experiment_run_read.ITEM_STATUSES


def _external_snapshot(rec: dict) -> dict:
    """An external metric's pinned ``config_snapshot["external"]`` (``ExternalMetricDefinition.snapshot`` + key)."""
    if "key" not in rec:
        return {"name": rec["name"]}
    _, name, source_hash, output_type, higher_is_better, pass_threshold = rec["key"]
    return {"name": name, "output_type": output_type, "higher_is_better": higher_is_better,
            "pass_threshold": pass_threshold, "source_hash": source_hash,
            "key": hashlib.sha256(json.dumps(list(rec["key"]), default=str).encode()).hexdigest()}


def _item_read(item: dict, cap: int) -> dict:
    """``ExperimentRunItemReadSerializer`` for one stored item: output and error over ``cap`` bytes of canonical JSON
    come back as a prefix with ``*_truncated`` and the full size in ``*_bytes``."""
    out = {"id": item.get("id") or str(uuid.uuid5(uuid.NAMESPACE_URL, f"{item['example_id']}/{item['trial_number']}")),
           "example_id": item["example_id"], "trial_number": item["trial_number"], "status": item["status"],
           "receipt_key": item.get("receipt_key"), "trace_id": item.get("trace_id"),
           "root_span_id": item.get("root_span_id"), "latency_ms": item.get("latency_ms"), "cost": item.get("cost"),
           "token_usage": item.get("token_usage"),
           "score_refs": [{"metric_id": r.get("metric_id"), "evaluator_version_id": r.get("evaluator_version_id"),
                           "status": r.get("status"), "value": r.get("value"), "explanation": r.get("explanation"),
                           "trace_id": None, "span_id": None} for r in item.get("score_refs") or []],
           "created_at": "2026-10-22T00:00:00Z", "updated_at": "2026-10-22T00:00:00Z"}
    for name in ("output", "error"):
        value = item.get(name)
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        cut = value is not None and len(data) > cap
        out[name] = data[:cap].decode("utf-8", errors="ignore") if cut else value
        out[f"{name}_truncated"], out[f"{name}_bytes"] = cut, len(data) if value is not None else 0
    return out


def client_for(server: ContractServer, base_url: str = "http://srv.test"):
    from fi.futureagi_client import FutureAGIClient

    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url=base_url)
    client.generated_client.get_httpx_client()._transport = httpx.MockTransport(server)
    return client
