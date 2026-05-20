from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from fi.annotations import Annotation
from fi.api.auth import APIKeyAuth
from fi.api.apikeys import ProviderAPIKeyClient
from fi.api.types import ApiKey, HttpMethod, ModelProvider, RequestConfig
from fi.client import Client
from fi.datasets import Dataset, DatasetConfig
from fi.datasets.types import DataTypeChoices
from fi.kb import KnowledgeBase
from fi.prompt import ModelConfig, Prompt, PromptTemplate, UserMessage
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
                        "annotation_metadata_lifecycle",
                        "annotation_queue_management_lifecycle",
                        "dataset_lifecycle",
                        "dataset_management_lifecycle",
                        "knowledge_base_lifecycle",
                        "model_log_lifecycle",
                        "prompt_lifecycle",
                        "provider_api_key_lifecycle",
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

        if parsed.path == "/annotation/metadata":
            self._handle_annotation_metadata(payload)
            return

        if parsed.path == "/annotation-queue/management":
            self._handle_annotation_queue_management(payload)
            return

        if parsed.path == "/dataset/lifecycle":
            self._handle_dataset_lifecycle(payload)
            return

        if parsed.path == "/dataset/management":
            self._handle_dataset_management(payload)
            return

        if parsed.path == "/knowledge-base/lifecycle":
            self._handle_knowledge_base_lifecycle(payload)
            return

        if parsed.path == "/model/log":
            self._handle_model_log(payload)
            return

        if parsed.path == "/prompt/lifecycle":
            self._handle_prompt_lifecycle(payload)
            return

        if parsed.path == "/provider-api-key/lifecycle":
            self._handle_provider_api_key_lifecycle(payload)
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

    def _handle_provider_api_key_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            provider = ModelProvider[_required(payload, "provider")]
            api_key = ApiKey(provider=provider, key=_required(payload, "provider_key"))
            ProviderAPIKeyClient.set_api_key(
                api_key,
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
            )
            listed = ProviderAPIKeyClient.list_api_keys(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
            )
            fetched = ProviderAPIKeyClient.get_api_key(
                provider,
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
            )
            STATE.calls.append({"operation": "provider-api-key/lifecycle", "provider": provider.value})
            self._write_json(
                {
                    "success": True,
                    "result": {
                        "listed": _jsonable(listed),
                        "fetched": _jsonable(fetched),
                    },
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_annotation_metadata(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = Annotation(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            labels = client.get_labels(
                project_id=payload.get("project_id"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            projects = client.list_projects(
                project_type=payload.get("project_type"),
                name=payload.get("project_name"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            STATE.calls.append({"operation": "annotation/metadata", "labels": len(labels)})
            self._write_json(
                {
                    "success": True,
                    "result": {
                        "labels": _jsonable(labels),
                        "projects": _jsonable(projects),
                    },
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_annotation_queue_management(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = AnnotationQueue(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            label_payload = payload.get("label") or {}
            queue_payload = payload.get("queue") or {}
            item_payload = payload.get("item") or {}
            user_id = payload.get("user_id")
            label = client.create_label(
                name=_required(label_payload, "name"),
                type=_required(label_payload, "type"),
                settings=label_payload.get("settings"),
                description=label_payload.get("description"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            labels = client.list_labels(timeout=payload.get("timeout") or STATE.timeout)
            fetched_label = client.get_label(label_id=label.id, timeout=payload.get("timeout") or STATE.timeout)
            queue = client.create(
                name=_required(queue_payload, "name"),
                description=queue_payload.get("description"),
                instructions=queue_payload.get("instructions"),
                requires_review=queue_payload.get("requires_review"),
                annotations_required=queue_payload.get("annotations_required"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            queues = client.list_queues(
                status=queue_payload.get("status"),
                search=queue.name,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            fetched_queue = client.get(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            updated_queue = client.update(
                queue_id=queue.id,
                description=queue_payload.get("updated_description"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            activated_queue = client.activate(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            add_label = client.add_label(queue_id=queue.id, label_id=label.id, timeout=payload.get("timeout") or STATE.timeout)
            added_items = client.add_items(
                queue_id=queue.id,
                items=[{"source_type": _required(item_payload, "source_type"), "source_id": _required(item_payload, "source_id")}],
                timeout=payload.get("timeout") or STATE.timeout,
            )
            items = client.list_items(
                queue_id=queue.id,
                status=item_payload.get("status"),
                assigned_to=user_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            item_id = _required(item_payload, "id")
            assigned = client.assign_items(
                queue_id=queue.id,
                item_ids=[item_id],
                user_id=user_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            imported = client.import_annotations(
                queue_id=queue.id,
                item_id=item_id,
                annotations=payload.get("annotations") or [],
                annotator_id=user_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            annotations = client.get_annotations(
                queue_id=queue.id,
                item_id=item_id,
                timeout=payload.get("timeout") or STATE.timeout,
            )
            skipped = client.skip_item(queue_id=queue.id, item_id=item_id, timeout=payload.get("timeout") or STATE.timeout)
            removed_items = client.remove_items(
                queue_id=queue.id,
                item_ids=[item_id],
                timeout=payload.get("timeout") or STATE.timeout,
            )
            remove_label = client.remove_label(queue_id=queue.id, label_id=label.id, timeout=payload.get("timeout") or STATE.timeout)
            analytics = client.get_analytics(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            agreement = client.get_agreement(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            export_to_dataset = client.export_to_dataset(
                queue_id=queue.id,
                dataset_name=payload.get("dataset_name"),
                status_filter=payload.get("status_filter"),
                timeout=payload.get("timeout") or STATE.timeout,
            )
            completed_queue = client.complete_queue(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            deleted_label = client.delete_label(label_id=label.id, timeout=payload.get("timeout") or STATE.timeout)
            deleted_queue = client.delete(queue_id=queue.id, timeout=payload.get("timeout") or STATE.timeout)
            STATE.calls.append({"operation": "annotation-queue/management", "queue_id": queue.id})
            self._write_json(
                {
                    "success": True,
                    "result": _jsonable(
                        {
                            "label": label,
                            "labels": labels,
                            "fetched_label": fetched_label,
                            "queue": queue,
                            "queues": queues,
                            "fetched_queue": fetched_queue,
                            "updated_queue": updated_queue,
                            "activated_queue": activated_queue,
                            "add_label": add_label,
                            "added_items": added_items,
                            "items": items,
                            "assigned": assigned,
                            "imported": imported,
                            "annotations": annotations,
                            "skipped": skipped,
                            "removed_items": removed_items,
                            "remove_label": remove_label,
                            "analytics": analytics,
                            "agreement": agreement,
                            "export_to_dataset": export_to_dataset,
                            "completed_queue": completed_queue,
                            "deleted_label": deleted_label,
                            "deleted_queue": deleted_queue,
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

    def _handle_dataset_management(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            dataset = Dataset.get_dataset_config(
                _required(payload, "name"),
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            column_id = dataset.get_column_id(_required(payload, "lookup_column"))
            dataset.add_run_prompt(
                name=_required(payload, "run_prompt_name"),
                model=_required(payload, "model"),
                messages=payload.get("messages") or [],
            )
            eval_stats = dataset.get_eval_stats()
            dataset.add_optimization(
                optimization_name=_required(payload, "optimization_name"),
                prompt_column_name=_required(payload, "lookup_column"),
            )
            dataset.delete()
            STATE.calls.append({"operation": "dataset/management", "dataset_id": str(dataset.dataset_config) if dataset.dataset_config else None})
            self._write_json(
                {
                    "success": True,
                    "result": {
                        "column_id": column_id,
                        "eval_stats": _jsonable(eval_stats),
                        "deleted": True,
                    },
                }
            )
        except Exception as exc:
            self._write_json({"success": False, "error": str(exc)}, status=500)

    def _handle_knowledge_base_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            client = KnowledgeBase(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            name = _required(payload, "name")
            updated_name = payload.get("updated_name") or name
            client.create_kb(name=name)
            client.update_kb(kb_name=name, new_name=updated_name)
            client.delete_files_from_kb(file_names=payload.get("file_names") or [], kb_name=updated_name)
            client.delete_kb(kb_names=updated_name)
            STATE.calls.append({"operation": "knowledge-base/lifecycle", "name": name})
            self._write_json({"success": True, "result": {"deleted": True}})
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

    def _handle_prompt_lifecycle(self, payload: dict[str, Any]) -> None:
        try:
            _ensure_initialized()
            template = PromptTemplate(
                name=_required(payload, "name"),
                messages=[UserMessage(content=_required(payload, "message"))],
                model_configuration=ModelConfig(model_name=_required(payload, "model")),
            )
            prompt = Prompt(
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
                timeout=STATE.timeout,
            )
            prompt.template = template
            prompt.generate(_required(payload, "generate_requirements"))
            prompt.improve(_required(payload, "improve_requirements"))
            compiled = prompt.compile(**(payload.get("variables") or {}))
            prompt.create(label=payload.get("label"))
            prompt.commit_current_version(
                message=payload.get("commit_message") or "",
                set_default=bool(payload.get("set_default")),
            )
            fetched = Prompt.get_template_by_name(
                _required(payload, "name"),
                label=payload.get("label"),
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
            )
            labels = prompt.list_labels()
            template_labels = Prompt.get_template_labels(
                template_name=_required(payload, "name"),
                fi_api_key=STATE.api_key,
                fi_secret_key=STATE.secret_key,
                fi_base_url=STATE.base_url,
            )
            prompt.delete()
            STATE.calls.append({"operation": "prompt/lifecycle", "template": payload.get("name")})
            self._write_json(
                {
                    "success": True,
                    "result": {
                        "compiled": _jsonable(compiled),
                        "fetched_template": _jsonable(fetched.template),
                        "labels": _jsonable(labels),
                        "template_labels": _jsonable(template_labels),
                        "deleted": True,
                    },
                }
            )
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
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
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
