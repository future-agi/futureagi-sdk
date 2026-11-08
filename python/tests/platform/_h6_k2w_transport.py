"""H6/K2W mock-only public-client harness; no production error/policy oracle.

Authoring base: 219fa74698afa6173e8f48192783643d54e5c873.
All credentials are synthetic. Regional hostnames are configuration strings, not
readiness evidence. Only transport construction and backoff sleep are replaced;
origin resolution, public namespaces, retries, parsing and error mapping are real.
"""
import asyncio
import inspect
import re
import socket

import httpx
import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient, errors
from fi.generated.platform.policy import OPERATIONS

US = "https://api.futureagi.com"
EU = "https://api-eu.futureagi.com"
API_KEY = "h6-synthetic-api-key-not-valid"
SECRET_KEY = "h6-synthetic-secret-key-not-valid"
TOKEN = "h6-synthetic-bearer-token-not-valid"
SUBMITTED = "h6-synthetic-private-input"
SID = "sbx_" + "a" * 24
ACTIONS = ("json", "create", "sse", "upload", "download")
SANDBOX_ABSENT = not any(name.startswith("sandboxes.") for name in OPERATIONS)
NOT_APPLICABLE_AT_FOLD = 'NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns'


def success(request):
    return httpx.Response(200, json={"environments": [], "count": 0, "next": None,
                                    "previous": None, "results": []})


class Wire:
    def __init__(self):
        self.requests = []
        self.sleeps = []
        self.respond = success

    def send(self, request):
        self.requests.append(request)
        return self.respond(request)

    def client(self, asynchronous=False, mode="keys", retries=None, **options):
        auth = {"api_key": API_KEY, "secret_key": SECRET_KEY} if mode == "keys" else {"platform_token": TOKEN}
        kwargs = {**auth, **options}
        if retries is not None:
            kwargs["retries"] = retries
        cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
        c = cls(**kwargs)
        # Do not replace the executor or resolver; disable only wall-clock backoff.
        c._platform.shared.sleep = lambda delay: self.sleeps.append(delay)
        return c


@pytest.fixture
def wire(monkeypatch, _no_egress):
    # Explicit dependence ensures the enclosing no-egress fixture runs first.
    for key in ("FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY",
                "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID",
                "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"):
        monkeypatch.delenv(key, raising=False)
    attempts = []

    def no_socket(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("H6/K2W tests must not open sockets or resolve hosts")

    monkeypatch.setattr(socket.socket, "connect", no_socket)
    monkeypatch.setattr(socket, "getaddrinfo", no_socket)
    result = Wire()
    monkeypatch.setattr(httpx, "HTTPTransport", lambda *a, **kw: httpx.MockTransport(result.send))
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda *a, **kw: httpx.MockTransport(result.send))
    yield result
    assert attempts == [], "a fake was bypassed (including loopback)"


def invoke(c, asynchronous, action):
    if action in ACTIONS:
        raise AssertionError(NOT_APPLICABLE_AT_FOLD)
    if action == "console":
        return c.environments.list()
    if action == "core":
        return c.prompts.list()
    raise AssertionError(f"Unknown action: {action}")


def run(asynchronous, call):
    if not asynchronous:
        return call()

    async def go():
        result = call()
        return await result if inspect.isawaitable(result) else result
    return asyncio.run(go())


def close(c, asynchronous):
    run(asynchronous, c.aclose if asynchronous else c.close)


def assert_private(error, logs="", extra=()):
    dump = str(error) + repr(error) + repr(vars(error)) + logs
    for value in (API_KEY, SECRET_KEY, TOKEN, SUBMITTED, *extra):
        assert value not in dump
    assert error.__cause__ is None
    assert error.__context__ is None


def assert_selected_only(wire, base, mode, count):
    assert len(wire.requests) == count
    selected = httpx.URL(base)
    foreign = [r for r in wire.requests if (r.url.scheme, r.url.host, r.url.port) !=
               (selected.scheme, selected.host, selected.port)]
    assert foreign == [], "zero requests to any other origin, not merely no auth headers"
    for r in wire.requests:
        if mode == "keys":
            assert r.headers.get("x-api-key") == API_KEY
            assert r.headers.get("x-secret-key") == SECRET_KEY
            assert "authorization" not in r.headers
        else:
            assert r.headers.get("authorization") == "Bearer " + TOKEN
            assert "x-api-key" not in r.headers and "x-secret-key" not in r.headers
    assert not [(str(r.url), name) for r in foreign for name in
                ("authorization", "x-api-key", "x-secret-key") if name in r.headers]


def regional_guidance(error):
    assert isinstance(error, errors.FutureAGIAPIError)
    assert error.status_code == 403 and error.code == "wrong_region"
    # The contract requires a distinct typed error, but does not freeze its class
    # spelling. Do not invent a new import which would mask transport RED at collection.
    assert type(error) not in (errors.FutureAGIAPIError, errors.PermissionDeniedError)
    assert getattr(errors, type(error).__name__, None) is type(error), "publicly catchable type"
    text = str(error)
    assert US in text and EU in text
    assert re.search(r"manual|explicit", text, re.I)
    assert re.search(r"select|configur|set .*base", text, re.I)
    assert not re.search(r"(?:your |the )(?:org|organization|workspace) (?:is|resides|belongs) (?:in|to)", text, re.I)
