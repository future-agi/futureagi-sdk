import os
import time
from uuid import uuid4

import pytest

from fi.annotations import Annotation
from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.datasets import Dataset, DatasetConfig
from fi.datasets.types import DataTypeChoices
from fi.kb import KnowledgeBase
from fi.queues import AnnotationQueue
from fi.utils.types import ModelTypes


def _live_options():
    api_key = os.environ.get("FI_API_KEY")
    secret_key = os.environ.get("FI_SECRET_KEY")
    base_url = os.environ.get("FI_BASE_URL")
    if not api_key or not secret_key or not base_url:
        pytest.skip("FI_API_KEY, FI_SECRET_KEY, and FI_BASE_URL are required for live SDK smoke tests")
    return {
        "fi_api_key": api_key,
        "fi_secret_key": secret_key,
        "fi_base_url": base_url.rstrip("/"),
        "timeout": int(os.environ.get("FI_LIVE_TIMEOUT", "20")),
    }


def _first_dataset_name(client: APIKeyAuth, base_url: str) -> str | None:
    response = client.request(
        RequestConfig(
            method=HttpMethod.GET,
            url=f"{base_url}/model-hub/develops/get-datasets-names/",
            timeout=20,
        )
    )
    body = response.json()
    datasets = ((body or {}).get("result") or {}).get("datasets") or []
    return datasets[0]["name"] if datasets else None


def test_live_read_surfaces_against_real_backend():
    opts = _live_options()
    base_url = opts["fi_base_url"]

    raw = APIKeyAuth(**opts)
    health = raw.request(
        RequestConfig(method=HttpMethod.GET, url=f"{base_url}/health/", timeout=10)
    )
    assert health.status_code == 200

    annotation = Annotation(**opts)
    assert isinstance(annotation.get_labels(), list)
    assert isinstance(annotation.list_projects(page_size=5), list)

    queue = AnnotationQueue(**opts)
    assert isinstance(queue.list_labels(), list)
    assert isinstance(queue.list_queues(), list)

    dataset_name = os.environ.get("FI_LIVE_DATASET_NAME") or _first_dataset_name(raw, base_url)
    if dataset_name:
        dataset = Dataset.get_dataset_config(dataset_name, **opts)
        config = dataset.get_config()
        assert config.id
        assert config.name == dataset_name


def test_live_knowledge_base_write_flow_against_real_backend():
    if os.environ.get("FI_LIVE_KB_WRITE") != "1":
        pytest.skip("Set FI_LIVE_KB_WRITE=1 to run the mutating KB live smoke test")

    opts = _live_options()
    name = f"sdk-live-kb-{uuid4().hex[:8]}"
    updated_name = f"{name}-renamed"
    kb = KnowledgeBase(**opts)

    try:
        kb.create_kb(name)
        kb.update_kb(name, new_name=updated_name)
        listed = kb.list_kbs(updated_name)
        assert any(item.name == updated_name for item in listed)
    finally:
        try:
            kb.delete_kb(kb_names=updated_name)
        except Exception:
            if name != updated_name:
                kb.delete_kb(kb_names=name)


def test_live_dataset_write_flow_against_real_backend():
    if os.environ.get("FI_LIVE_DATASET_WRITE") != "1":
        pytest.skip("Set FI_LIVE_DATASET_WRITE=1 to run the mutating dataset live smoke test")

    opts = _live_options()
    dataset = Dataset(
        dataset_config=DatasetConfig(
            name=f"sdk-live-dataset-{int(time.time())}-{uuid4().hex[:6]}",
            model_type=ModelTypes.GENERATIVE_LLM,
        ),
        **opts,
    )
    created = False
    try:
        dataset.create()
        created = True
        dataset.add_columns(
            [
                {"name": "input", "data_type": DataTypeChoices.TEXT},
                {"name": "score", "data_type": DataTypeChoices.FLOAT},
            ]
        )
        dataset.add_rows(
            [
                {
                    "cells": [
                        {"column_name": "input", "value": "hello"},
                        {"column_name": "score", "value": 0.7},
                    ]
                }
            ]
        )
        assert dataset.get_column_id("input")
    finally:
        if created:
            dataset.delete()


def test_live_model_log_route_is_not_currently_exposed():
    opts = _live_options()
    base_url = opts["fi_base_url"]
    raw = APIKeyAuth(**opts)
    for path in ("sdk/api/v1/log/model/", "log/model/"):
        response = raw.request(
            RequestConfig(
                method=HttpMethod.POST,
                url=f"{base_url}/{path}",
                json={},
                timeout=10,
            )
        )
        assert response.status_code == 404
