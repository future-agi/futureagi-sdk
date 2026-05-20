from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from fi.annotations import Annotation
from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.client import Client
from fi.datasets import Dataset, DatasetConfig
from fi.datasets.types import DataTypeChoices
from fi.queues import AnnotationQueue
from fi.utils.types import Environments, ModelTypes


@dataclass
class AdapterState:
    api_key: str | None = None
    secret_key: str | None = None
    base_url: str | None = None
    timeout: int | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)


STATE = AdapterState()


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"futureagi-sdk Python compliance adapter listening on :{port}", flush=True)
    server.serve_forever()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(
                {
                    "sdk_name": "futureagi-sdk-python",
                    "sdk_version": _sdk_version(),
                    "adapter_version": "0.1.0",
                    "language": "python",
                    "capabilities": [
                        "auth_api_key",
                        "raw_request",
                        "annotation_bulk_log",
                        "annotation_queue_lifecycle",
                        "annotation_score_lifecycle",
                        "dataset_lifecycle",
                        "model_log_lifecycle",
                    ],
                }
            )
            return

        if self.path == "/state":
            self._write_json(
                {
                    "initialized": STATE.base_url is not None,
                    "base_url": STATE.base_url,
                    "calls": STATE.calls,
                }
            )
            return

        self._write_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        payload = self._read_json()

        if parsed.path == "/reset":
            STATE.api_key = None
            STATE.secret_key = None
            STATE.base_url = None
            STATE.timeout = None
            STATE.calls.clear()
            self._write_json({"success": True})
            return

        if parsed.path == "/init":
            STATE.api_key = _required(payload, "api_key")
            STATE.secret_key = _required(payload, "secret_key")
            STATE.base_url = _required(payload, "base_url").rstrip("/")
            STATE.timeout = int(payload.get("timeout") or 30)
            STATE.calls.append({"operation": "init", "base_url": STATE.base_url})
            self._write_json({"success": True})
            return

        if parsed.path == "/raw-request":
            self._handle_raw_request(payload)
            return

        if parsed.path == "/annotation/log":
            self._handle_annotation_log(payload)
            return

        if parsed.path == "/annotation-queue/lifecycle":
            self._handle_annotation_queue_lifecycle(payload)
            return

        if parsed.path == "/annotation-score/lifecycle":
            self._handle_annotation_score_lifecycle(payload)
            return

        if parsed.path == "/dataset/lifecycle":
            self._handle_dataset_lifecycle(payload)
            return

        if parsed.path == "/model/log":
            self._handle_model_log(payload)
            return

        self._write_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _handle_raw_request(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = APIKeyAuth(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            path = _required(payload, "path").lstrip("/")
            method = HttpMethod[_required(payload, "method").upper()]
            response = client.request(
                RequestConfig(
                    method=method,
                    url=f"{STATE.base_url}/{path}",
                    params=payload.get("params"),
                    json=payload.get("json"),
                    data=payload.get("data"),
                    timeout=payload.get("timeout") or STATE.timeout,
                )
            )
            STATE.calls.append({"operation": "raw-request", "path": path, "method": method.value})
            self._write_json(_response_payload(response))
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_annotation_score_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = AnnotationQueue(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            source_type = _required(payload, "source_type")
            source_id = _required(payload, "source_id")
            created = client.create_score(
                source_type=source_type,
                source_id=source_id,
                label_id=_required(payload, "label_id"),
                value=payload.get("value"),
                notes=payload.get("notes"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            bulk = client.create_scores(
                source_type=source_type,
                source_id=source_id,
                scores=payload.get("bulk_scores") or [],
                timeout=payload.get("timeout") or STATE.timeout,
            )
            fetched = client.get_scores(
                source_type=source_type,
                source_id=source_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            STATE.calls.append({"operation": "annotation-score/lifecycle", "source_id": source_id})
            self._write_json(
                {
                    "success": True,
                    "result": _jsonable(
                        {
                            "created": created,
                            "bulk": bulk,
                            "fetched": fetched,
                        }
                    ),
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_dataset_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            columns = payload.get("columns")
            rows = payload.get("rows")
            if not isinstance(columns, list) or not columns:
                raise ValueError("columns must be a non-empty list")
            if not isinstance(rows, list) or not rows:
                raise ValueError("rows must be a non-empty list")

            dataset = Dataset(
                dataset_config=DatasetConfig(
                    name=_required(payload, "name"),
                    model_type=ModelTypes[_required(payload, "model_type")],
                ),
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            dataset.create()
            dataset.add_columns(
                [
                    {
                        "name": _required(column, "name"),
                        "data_type": DataTypeChoices[_required(column, "data_type")],
                    }
                    for column in columns
                ]
            )
            dataset.add_rows(rows)
            STATE.calls.append({"operation": "dataset/lifecycle", "dataset_id": str(dataset.dataset_config.id)})
            self._write_json(
                {
                    "success": True,
                    "result": {
                        "dataset": _jsonable(dataset.dataset_config),
                        "columns_added": len(columns),
                        "rows_added": len(rows),
                    },
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_model_log(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = Client(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            result = client.log(
                model_id=_required(payload, "model_id"),
                model_type=ModelTypes[_required(payload, "model_type")],
                environment=Environments[_required(payload, "environment")],
                model_version=payload.get("model_version"),
                prediction_timestamp=payload.get("prediction_timestamp"),
                conversation=payload.get("conversation"),
                tags=payload.get("tags"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            STATE.calls.append({"operation": "model/log", "model_id": payload.get("model_id")})
            self._write_json({"success": True, "body": _jsonable(result)})
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_annotation_log(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            records = payload.get("records")
            if not isinstance(records, list):
                raise ValueError("records must be a list")

            client = Annotation(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            result = client.log_annotations(
                pd.DataFrame(records),
                project_name=payload.get("project_name"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            STATE.calls.append({"operation": "annotation/log", "records": len(records)})
            self._write_json({"success": True, "result": _jsonable(result)})
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_annotation_queue_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            queue_payload = payload.get("queue") or {}
            item_payload = payload.get("item") or {}
            label_id = _required(payload, "label_id")
            item_id = _required(item_payload, "id")
            source_type = _required(item_payload, "source_type")
            source_id = _required(item_payload, "source_id")
            annotations = payload.get("annotations")
            if not isinstance(annotations, list):
                raise ValueError("annotations must be a list")

            client = AnnotationQueue(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            queue = client.create(
                name=_required(queue_payload, "name"),
                description=queue_payload.get("description"),
                instructions=queue_payload.get("instructions"),
                assignment_strategy=queue_payload.get("assignment_strategy"),
                annotations_required=queue_payload.get("annotations_required"),
                requires_review=queue_payload.get("requires_review"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            add_label = client.add_label(
                queue_id=queue.id,
                label_id=label_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            added_items = client.add_items(
                queue_id=queue.id,
                items=[{"source_type": source_type, "source_id": source_id}],
                timeout=payload.get("timeout") or STATE.timeout,
            )
            submitted = client.submit_annotations(
                queue_id=queue.id,
                item_id=item_id,
                annotations=annotations,
                notes=payload.get("notes"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            completed = client.complete_item(
                queue_id=queue.id,
                item_id=item_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            progress = client.get_progress(
                queue_id=queue.id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            exported = client.export(
                queue_id=queue.id,
                export_format="json",
                status="completed",
                timeout=payload.get("timeout") or STATE.timeout,
            )
            STATE.calls.append({"operation": "annotation-queue/lifecycle", "queue_id": queue.id})
            self._write_json(
                {
                    "success": True,
                    "result": _jsonable(
                        {
                            "queue": queue,
                            "add_label": add_label,
                            "added_items": added_items,
                            "submitted": submitted,
                            "completed": completed,
                            "progress": progress,
                            "exported": exported,
                        }
                    ),
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def _write_json(self, payload: Any, status: int = 200) -> None:
        raw = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _ensure_initialized() -> None:
    if not STATE.api_key or not STATE.secret_key or not STATE.base_url:
        raise RuntimeError("adapter is not initialized")


def _required(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not value:
        raise ValueError(f"{key} is required")
    return str(value)


def _response_payload(response: Any) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception:
        body = getattr(response, "text", "")
    return {
        "success": 200 <= int(response.status_code) < 300,
        "status_code": int(response.status_code),
        "body": body,
    }


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _sdk_version() -> str:
    try:
        from fi import __version__

        return str(__version__)
    except Exception:
        return "unknown"


if __name__ == "__main__":
    main()
