from dataclasses import fields
from importlib import import_module

import httpx
import pytest


@pytest.mark.parametrize(
    "resource",
    [
        "batches",
        "completions",
        "embeddings",
        "files",
        "images",
        "models",
        "moderations",
        "rerank",
        "responses",
    ],
)
def test_request_options_081_positional_arguments(resource: str) -> None:
    request_options = import_module(f"fi.gateway.resources.{resource}").RequestOptions
    headers = {"X-Request-ID": "example"}
    files = {"file": ("example.txt", b"example")}
    timeout = httpx.Timeout(5.0)
    retries = 2
    options = request_options("POST", "/x", None, headers, files, timeout, retries)

    expected = {
        "method": "POST",
        "url": "/x",
        "body": None,
        "headers": headers,
        "files": files,
        "timeout": timeout,
        "max_retries": retries,
    }
    assert {name: getattr(options, name) for name in expected} == expected
    assert tuple(field.name for field in fields(options)[:len(expected)]) == tuple(expected)


@pytest.mark.parametrize(
    ("resource", "name", "owner"),
    [
        ("audio", "RequestOptions", "_base_client"),
        ("audio", "build_extra_headers", "_agentcc_params"),
        ("audio", "collect_agentcc_params", "_agentcc_params"),
        ("audio", "merge_session_headers", "_agentcc_params"),
        ("audio", "Transcription", "types.audio"),
        ("audio", "Translation", "types.audio"),
        ("chat.completions", "RequestOptions", "_base_client"),
    ],
)
def test_gateway_081_resource_import(resource: str, name: str, owner: str) -> None:
    resource_module = import_module(f"fi.gateway.resources.{resource}")
    owner_module = import_module(f"fi.gateway.{owner}")
    assert getattr(resource_module, name) is getattr(owner_module, name)
