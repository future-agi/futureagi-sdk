"""Provider settings given to one guardrails gateway stay with that gateway.

``with_openai``, ``with_azure`` and ``with_local_model`` hold the keys, endpoints and server URLs
they are given on the instance, read the process environment only for fields they were not given,
and do not write to the environment. Keys are derived at runtime; nothing here reaches a provider.
"""

from __future__ import annotations

import os
import secrets
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Iterator, List

import pytest

from fi.evals.guardrails.base import Guardrails
from fi.evals.guardrails.config import GuardrailModel, GuardrailsConfig
from fi.evals.guardrails.gateway import GuardrailsGateway

OPENAI = GuardrailModel.OPENAI_MODERATION
AZURE = GuardrailModel.AZURE_CONTENT_SAFETY
PROVIDER_ENV = (
    "OPENAI_API_KEY",
    "AZURE_CONTENT_SAFETY_ENDPOINT",
    "AZURE_CONTENT_SAFETY_KEY",
    "VLLM_SERVER_URL",
    "VLLM_WILDGUARD_7B_URL",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
)
THREADS = 8
ROUNDS = 6


def _derive(label: str) -> str:
    return f"{label}-{secrets.token_hex(16)}"


def _backend(gateway: GuardrailsGateway, model: GuardrailModel):
    return gateway._guardrails.backends[model]


@pytest.fixture(autouse=True)
def _no_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def busy_switching() -> Iterator[None]:
    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        yield
    finally:
        sys.setswitchinterval(interval)


def _run_concurrently(build: Callable[[int], None]) -> None:
    for _ in range(ROUNDS):
        barrier = threading.Barrier(THREADS)

        def work(i: int) -> None:
            barrier.wait()
            build(i)

        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            list(pool.map(work, range(THREADS)))


def test_openai_key_is_not_seen_by_a_later_gateway_without_one() -> None:
    key_a = _derive("tenant-a")
    env_before = dict(os.environ)
    gateway_a = GuardrailsGateway.with_openai(api_key=key_a)
    assert _backend(gateway_a, OPENAI)._api_key == key_a
    assert dict(os.environ) == env_before
    with pytest.raises(RuntimeError, match="OpenAI API key required"):
        GuardrailsGateway.with_openai()
    assert dict(os.environ) == env_before


def test_openai_reads_the_process_key_when_none_is_given(monkeypatch: pytest.MonkeyPatch) -> None:
    process_key, key_a = _derive("process"), _derive("tenant-a")
    monkeypatch.setenv("OPENAI_API_KEY", process_key)
    env_before = dict(os.environ)
    gateway_a = GuardrailsGateway.with_openai(api_key=key_a)
    gateway_b = GuardrailsGateway.with_openai()
    assert _backend(gateway_a, OPENAI)._api_key == key_a
    assert _backend(gateway_b, OPENAI)._api_key == process_key
    assert dict(os.environ) == env_before


def test_openai_gateways_built_from_eight_threads_keep_their_own_keys(busy_switching: None) -> None:
    keys = {"tenant-a": _derive("tenant-a"), "tenant-b": _derive("tenant-b")}
    seen: List[tuple] = []
    lock = threading.Lock()
    env_before = dict(os.environ)

    def build(i: int) -> None:
        tenant = ("tenant-a", "tenant-b")[i % 2]
        gateway = GuardrailsGateway.with_openai(api_key=keys[tenant])
        with lock:
            seen.append((tenant, _backend(gateway, OPENAI)._api_key))

    _run_concurrently(build)
    assert len(seen) == THREADS * ROUNDS
    assert [(t, k) for t, k in seen if k != keys[t]] == []
    assert dict(os.environ) == env_before


def test_azure_settings_are_not_seen_by_a_later_gateway_without_them() -> None:
    endpoint_a, key_a = "https://127.0.0.1:9/tenant-a", _derive("tenant-a")
    env_before = dict(os.environ)
    gateway_a = GuardrailsGateway.with_azure(endpoint=endpoint_a, api_key=key_a)
    backend = _backend(gateway_a, AZURE)
    assert (backend._endpoint, backend._api_key) == (endpoint_a, key_a)
    assert dict(os.environ) == env_before
    with pytest.raises(RuntimeError, match="Azure endpoint required"):
        GuardrailsGateway.with_azure()
    with pytest.raises(RuntimeError, match="Azure API key required"):
        GuardrailsGateway.with_azure(endpoint=endpoint_a)
    assert dict(os.environ) == env_before


def test_azure_reads_only_the_fields_it_was_not_given(monkeypatch: pytest.MonkeyPatch) -> None:
    process_endpoint, process_key = "https://127.0.0.1:9/process", _derive("process")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", process_endpoint)
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_KEY", process_key)
    key_a = _derive("tenant-a")
    env_before = dict(os.environ)
    backend_a = _backend(GuardrailsGateway.with_azure(api_key=key_a), AZURE)
    backend_b = _backend(GuardrailsGateway.with_azure(), AZURE)
    assert (backend_a._endpoint, backend_a._api_key) == (process_endpoint, key_a)
    assert (backend_b._endpoint, backend_b._api_key) == (process_endpoint, process_key)
    assert dict(os.environ) == env_before


def test_azure_gateways_built_from_eight_threads_keep_their_own_settings(busy_switching: None) -> None:
    settings: Dict[str, tuple] = {
        tenant: (f"https://127.0.0.1:9/{tenant}", _derive(tenant)) for tenant in ("tenant-a", "tenant-b")
    }
    seen: List[tuple] = []
    lock = threading.Lock()
    env_before = dict(os.environ)

    def build(i: int) -> None:
        tenant = ("tenant-a", "tenant-b")[i % 2]
        endpoint, key = settings[tenant]
        backend = _backend(GuardrailsGateway.with_azure(endpoint=endpoint, api_key=key), AZURE)
        with lock:
            seen.append((tenant, (backend._endpoint, backend._api_key)))

    _run_concurrently(build)
    assert len(seen) == THREADS * ROUNDS
    assert [(t, s) for t, s in seen if s != settings[t]] == []
    assert dict(os.environ) == env_before


def test_local_model_url_stays_with_its_gateway() -> None:
    url_a = "http://127.0.0.1:9/tenant-a"
    env_before = dict(os.environ)
    gateway_a = GuardrailsGateway.with_local_model(GuardrailModel.WILDGUARD_7B, vllm_url=url_a)
    gateway_b = GuardrailsGateway.with_local_model(GuardrailModel.WILDGUARD_7B)
    assert _backend(gateway_a, GuardrailModel.WILDGUARD_7B)._vllm_url == url_a
    assert _backend(gateway_b, GuardrailModel.WILDGUARD_7B)._vllm_url is None
    assert dict(os.environ) == env_before


def test_backend_options_are_copied_per_instance() -> None:
    key_a, key_b = _derive("tenant-a"), _derive("tenant-b")
    options = {OPENAI: {"api_key": key_a}}
    config = GuardrailsConfig(models=[OPENAI])
    guardrails_a = Guardrails(config=config, backend_options=options)
    options[OPENAI]["api_key"] = key_b
    guardrails_b = Guardrails(config=config, backend_options=options)
    assert guardrails_a.backends[OPENAI]._api_key == key_a
    assert guardrails_b.backends[OPENAI]._api_key == key_b
    assert guardrails_a._backend_options[OPENAI]["api_key"] == key_a
