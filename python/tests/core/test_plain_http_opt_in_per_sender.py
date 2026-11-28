"""Every sender of the API keys treats a plain-http base URL that names a host which is neither loopback nor a Future AGI
host the same way: the keys are sent only when ``FI_ALLOW_INSECURE_HTTP`` is exactly ``"1"`` (``"true"``, ``"1 "``,
``"yes"``, ``"01"``, an empty value and an unset variable all refuse before any connection), and a send goes straight to
the host, bypassing proxies named by ``HTTP_PROXY``, ``http_proxy`` or ``ALL_PROXY``. The host name resolves to a loopback
listener through a resolver shim, so no real host is contacted. The marker keys and the connections are counted at the
listener of the host and at a proxy sink."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Callable
from unittest import mock

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import ConfigurationError
from fi.gateway._exceptions import AgentCCError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)

HOST = "census-host.test"
GW_KEY = "sk-agentcc-" + MARKER_KEY
NOT_ONE = ["true", "1 ", " 1", "yes", "01", "", "TRUE", "on"]
PROXY_VARIABLES = ["HTTP_PROXY", "http_proxy", "ALL_PROXY"]


def _sync_client(base: str, **extra: Any) -> FutureAGIClient:
    return FutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, retries=0, **extra)


def _async_client(base: str, **extra: Any) -> AsyncFutureAGIClient:
    return AsyncFutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, retries=0, **extra)


def _gateway(base: str) -> None:
    from fi.gateway import AgentCC

    client = AgentCC(api_key=GW_KEY, base_url=base, max_retries=0)
    try:
        client.models.list()
    finally:
        client.close()


def _gateway_async(base: str) -> None:
    from fi.gateway import AsyncAgentCC

    async def go() -> None:
        client = AsyncAgentCC(api_key=GW_KEY, base_url=base, max_retries=0)
        try:
            await client.models.list()
        finally:
            await client.aclose()

    asyncio.run(go())


def _gateway_check_valid_key(base: str) -> None:
    from fi.gateway._utils import check_valid_key

    if not check_valid_key(GW_KEY, base):
        raise RuntimeError("check_valid_key answered False")


def _gateway_health_check(base: str) -> None:
    from fi.gateway._utils import health_check

    if health_check(api_key=GW_KEY, base_url=base)["status"] != "ok":
        raise RuntimeError("health_check answered an error")


def _gateway_health_check_model(base: str) -> None:
    from fi.gateway._utils import health_check

    if health_check("m", api_key=GW_KEY, base_url=base)["status"] != "ok":
        raise RuntimeError("health_check answered an error")


def _management(base: str) -> None:
    with _sync_client(base) as client:
        client.gateway.config.get_active()


def _management_async(base: str) -> None:
    async def go() -> None:
        async with _async_client(base) as client:
            await client.gateway.config.get_active()

    asyncio.run(go())


def _generated(base: str) -> None:
    with _sync_client(base) as client:
        client.users.current()


def _sandbox_list(base: str) -> None:
    with _sync_client(base, platform_base_url=base + "/omega/api") as client:
        client.sandboxes.list()


def _sandbox_list_async(base: str) -> None:
    async def go() -> None:
        async with _async_client(base, platform_base_url=base + "/omega/api") as client:
            await client.sandboxes.list()

    asyncio.run(go())


def _sandbox_download(base: str) -> None:
    with _sync_client(base, platform_base_url=base + "/omega/api") as client:
        client.sandboxes.files.download("sbx-1", "a.txt")


def _sandbox_download_async(base: str) -> None:
    async def go() -> None:
        async with _async_client(base, platform_base_url=base + "/omega/api") as client:
            await client.sandboxes.files.download("sbx-1", "a.txt")

    asyncio.run(go())


def _platform(base: str) -> None:
    import fi.platform as fp

    client = fp.Client(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, max_retries=0)
    try:
        client.request("GET", "/probe/")
    finally:
        client.close()


def _platform_async(base: str) -> None:
    import fi.platform as fp

    async def go() -> None:
        async with fp.AsyncClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, max_retries=0) as client:
            await client.request("GET", "/probe/")

    asyncio.run(go())


def _knowledge_base(base: str) -> None:
    from fi.kb.client import KnowledgeBase

    with mock.patch.dict(os.environ, {"FI_BASE_URL": base, "FI_API_KEY": MARKER_KEY, "FI_SECRET_KEY": MARKER_SECRET}):
        KnowledgeBase().create_kb("kb")


def _session_client(base: str) -> None:
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    client = APIKeyAuth(MARKER_KEY, MARKER_SECRET, base)
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/x", retry_attempts=1))
    finally:
        client.close()


def _subclass_client(path: str, cls: str) -> Callable[[str], None]:
    def send(base: str) -> None:
        import importlib

        from fi.api.types import HttpMethod, RequestConfig

        client = getattr(importlib.import_module(path), cls)(fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET, fi_base_url=base)
        try:
            client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/x", retry_attempts=1))
        finally:
            client.close()

    return send


def _annotation(base: str) -> None:
    from fi.annotations import Annotation

    client = Annotation(fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET, fi_base_url=base)
    try:
        client.get_labels()
    finally:
        client.close()


def _annotation_queue(base: str) -> None:
    from fi.queues import AnnotationQueue

    client = AnnotationQueue(fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET, fi_base_url=base)
    try:
        client.list_queues()
    finally:
        client.close()


def _eval_registry(base: str) -> None:
    from fi.evals.core import cloud_registry

    cloud_registry._CACHE.clear()
    if not cloud_registry.load_registry(base, MARKER_KEY, MARKER_SECRET, force_refresh=True):
        raise RuntimeError("the registry loaded nothing")


def _experiment_export(base: str) -> None:
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus

    outcome = ExportStatus("run-1", base + "/tracer/v1/traces", Redactor())
    make = exporter_factory(base_url=base, api_key=MARKER_KEY, secret_key=MARKER_SECRET, project="p", run_name="r", run_id="run-1",
                            redactor=Redactor(), outcome=outcome, _endpoint=base + "/tracer/v1/traces")
    provider = make()
    provider.get_tracer("t").start_span("s").end()
    provider.shutdown()
    outcome.failed()
    if outcome.error is not None:
        raise RuntimeError(f"the export failed with {outcome.error.status_code}")


def _evals_exporter(kind: str) -> Callable[[str], None]:
    def send(base: str) -> None:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from fi.evals.otel._tracer_factories import _create_exporter
        from fi.evals.otel.config import ExporterConfig
        from fi.evals.otel.types import ExporterType

        headers = {"X-Api-Key": MARKER_KEY, "X-Secret-Key": MARKER_SECRET}
        exporter = _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=base + "/v1/traces", headers=headers))
        span = TracerProvider().get_tracer("t").start_span("s")
        span.end()
        if exporter.export([span]) != SpanExportResult.SUCCESS:
            raise RuntimeError("the export failed")

    return send


#: sender name -> (the call that sends one keyed request to the base URL, whether the sender reports a refusal as a result and not an exception)
SENDERS: dict[str, tuple[Callable[[str], None], bool]] = {
    "gateway client": (_gateway, False),
    "async gateway client": (_gateway_async, False),
    "gateway check_valid_key": (_gateway_check_valid_key, True),
    "gateway health_check": (_gateway_health_check, True),
    "gateway health_check with a model": (_gateway_health_check_model, True),
    "management client": (_management, False),
    "async management client": (_management_async, False),
    "generated client": (_generated, False),
    "platform client": (_platform, False),
    "async platform client": (_platform_async, False),
    "knowledge base": (_knowledge_base, False),
    "session client": (_session_client, False),
    "evaluator": (_subclass_client("fi.evals.evaluator", "Evaluator"), False),
    "evaluation templates": (_subclass_client("fi.evals.manager", "EvalTemplateManager"), False),
    "prompt client": (_subclass_client("fi.prompt.client", "Prompt"), False),
    "dataset client": (_subclass_client("fi.datasets.dataset", "Dataset"), False),
    "annotations": (_annotation, False),
    "annotation queues": (_annotation_queue, False),
    "evaluation registry": (_eval_registry, True),
    "experiment trace exporter": (_experiment_export, True),
    "evals exporter FUTUREAGI": (_evals_exporter("FUTUREAGI"), True),
    "evals exporter ARIZE": (_evals_exporter("ARIZE"), True),
    "evals exporter PHOENIX": (_evals_exporter("PHOENIX"), True),
    "evals exporter LANGFUSE": (_evals_exporter("LANGFUSE"), True),
    "evals exporter OTLP_HTTP": (_evals_exporter("OTLP_HTTP"), True),
}
NAMES = sorted(SENDERS)
#: The sandbox calls refuse plain http to a host that is not loopback whatever the opt-in says (``insecure_sandbox_origin``).
SANDBOX_SENDERS: dict[str, Callable[[str], None]] = {
    "sandbox list": _sandbox_list,
    "async sandbox list": _sandbox_list_async,
    "sandbox file download": _sandbox_download,
    "async sandbox file download": _sandbox_download_async,
}
SENDERS.update({name: (call, False) for name, call in SANDBOX_SENDERS.items()})


def _attempt(sinks_: dict, name: str, **env: str) -> tuple[str, Any]:
    """Run one sender against the target with ``env`` set; return ``("sent" | "failed", error)``."""
    for each in sinks_.values():
        each.reset()
    base = f"http://{HOST}:{sinks_['target'].port}"
    proxy = f"http://127.0.0.1:{sinks_['sinkA'].port}"
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    given = {k: v.replace("PROXY", proxy) for k, v in env.items()}
    with mock.patch.dict(os.environ, {**clean, **given}, clear=True):
        try:
            SENDERS[name][0](base)
        except Exception as error:  # a refusal, or the sink's body that no caller can use
            return "failed", error
    return "sent", None


def _no_byte_anywhere(sinks_: dict) -> None:
    for each in sinks_.values():
        assert each.marker_bytes == 0 and each.requests == 0, [bytes(c)[:80] for c in each.chunks]


def _assert_refused(sinks_: dict, name: str, outcome: str, error: Any) -> None:
    _no_byte_anywhere(sinks_)
    assert outcome == "failed"
    if not SENDERS[name][1]:
        assert isinstance(error, (ConfigurationError, AgentCCError)), repr(error)
    assert MARKER_KEY not in str(error) and MARKER_SECRET not in str(error)


@pytest.mark.parametrize("name", NAMES)
def test_a_sender_refuses_plain_http_to_a_non_loopback_host_without_the_opt_in(sinks, resolver, name):
    outcome, error = _attempt(sinks, name)
    _assert_refused(sinks, name, outcome, error)


@pytest.mark.parametrize("value", NOT_ONE)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_refuses_plain_http_when_the_opt_in_is_not_exactly_one(sinks, resolver, name, value):
    outcome, error = _attempt(sinks, name, FI_ALLOW_INSECURE_HTTP=value)
    _assert_refused(sinks, name, outcome, error)


@pytest.mark.parametrize("variable", PROXY_VARIABLES)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_without_the_opt_in_sends_nothing_to_the_host_or_the_proxy_when_a_proxy_is_set(sinks, resolver, name, variable):
    outcome, error = _attempt(sinks, name, **{variable: "PROXY"})
    _assert_refused(sinks, name, outcome, error)


@pytest.mark.parametrize("name", NAMES)
def test_a_sender_sends_plain_http_to_a_non_loopback_host_with_the_opt_in(sinks, resolver, name):
    _attempt(sinks, name, FI_ALLOW_INSECURE_HTTP="1")
    assert sinks["target"].requests >= 1 and sinks["target"].marker_bytes > 0
    assert sinks["sinkA"].requests == 0 and sinks["sinkB"].requests == 0


@pytest.mark.parametrize("variable", PROXY_VARIABLES)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_with_the_opt_in_sends_direct_whatever_the_proxy_variables_say(sinks, resolver, name, variable):
    _attempt(sinks, name, FI_ALLOW_INSECURE_HTTP="1", **{variable: "PROXY"})
    assert sinks["target"].requests >= 1 and sinks["target"].marker_bytes > 0
    for proxy in ("sinkA", "sinkB"):
        assert sinks[proxy].requests == 0 and sinks[proxy].marker_bytes == 0 and not sinks[proxy].chunks


@pytest.mark.parametrize("value", [None, "1", "true", "01"])
@pytest.mark.parametrize("name", sorted(SANDBOX_SENDERS))
def test_a_sandbox_call_refuses_plain_http_to_a_non_loopback_host_whatever_the_opt_in_says(sinks, resolver, name, value):
    outcome, error = _attempt(sinks, name, **({} if value is None else {"FI_ALLOW_INSECURE_HTTP": value}))
    _assert_refused(sinks, name, outcome, error)
    assert error.code == ("insecure_sandbox_origin" if value == "1" else error.code)


@pytest.mark.parametrize("variable", PROXY_VARIABLES)
@pytest.mark.parametrize("name", sorted(SANDBOX_SENDERS))
def test_a_sandbox_call_with_the_opt_in_and_a_proxy_sends_no_byte_to_a_non_loopback_http_host(sinks, resolver, name, variable):
    outcome, error = _attempt(sinks, name, FI_ALLOW_INSECURE_HTTP="1", **{variable: "PROXY"})
    _assert_refused(sinks, name, outcome, error)
    assert error.code == "insecure_sandbox_origin"
    assert "FI_ALLOW_INSECURE_HTTP" not in str(error) and "https://" in str(error)
