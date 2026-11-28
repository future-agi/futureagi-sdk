"""A mock sandbox server driven by the frozen scoped OpenAPI (no network).

Routes come from ``openapi/platform/generated/futureagi-platform.openapi.json``: each sandbox
operation's method and path template, matched against the request the SDK sends, so a wrong
path in the generated operation table fails here. A default answer is synthesized from the
operation's success schema (required fields, first enum value, one array item). Tests replace
answers per operation with :meth:`MockServer.on`, and stream SSE bytes in any chunking with
:class:`Chunks`.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional, Union

import httpx
from fi._core.origins import PlatformOrigin
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared
from fi.sandbox import AsyncSandboxes, Sandboxes
from fi.sandbox._connection import OriginRule, scope_headers

from ._gates_support import REPO

SPEC_PATH = REPO / "openapi" / "platform" / "generated" / "futureagi-platform.openapi.json"
ORIGIN = "https://sbx.example.test/omega/api"
#: The environment path sends Future AGI keys only to origins in the Future AGI zone
#: (or to loopback) unless FI_ALLOW_CUSTOM_PLATFORM_URL allows another host.
HOSTED = "https://sbx.futureagi.com/omega/api"
SBX = "sbx_" + "a" * 24
EXEC = "exec_" + "b" * 24
SNAP = "snap_1"
#: Synthetic credentials for tests.
FAKE_KEY, FAKE_SECRET, FAKE_TOKEN = "fake-api-key-0001", "fake-secret-key-0002", "fake-bearer-token-0003"
#: The ETag the mock's network-policy answers carry (the quoted desired revision).
ETAG = '"7"'


@dataclass
class Route:
    name: str
    method: str
    template: str
    pattern: re.Pattern
    status: int
    schema: Any


@dataclass
class Seen:
    name: str
    request: httpx.Request
    body: bytes = b""

    def json(self) -> Any:
        return json.loads(self.body) if self.body else None


@functools.lru_cache(maxsize=1)
def _spec_text() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


def load_spec() -> dict:
    return json.loads(_spec_text())


def routes(spec: dict) -> dict[str, Route]:
    """Every sandbox operation in the scoped spec, by SDK name (``<family>.<method>``)."""
    out: dict[str, Route] = {}
    for template, item in spec["paths"].items():
        for method, op in item.items():
            sdk = op.get("x-sdk-operation") if isinstance(op, dict) else None
            if not sdk or sdk.get("family") != "sandboxes":
                continue
            regex = re.escape(template).replace(re.escape("{path}"), ".+")
            regex = "^" + re.sub(r"\\\{[^}]+\\\}", "[^/]+", regex) + "$"
            status, schema = next(
                (int(code), r) for code, r in op["responses"].items() if code.startswith("2")
            )
            content = schema.get("content", {}).get("application/json", {})
            out[sdk["family"] + "." + sdk["method"]] = Route(
                sdk["family"] + "." + sdk["method"], method.upper(), template,
                re.compile(regex), status, content.get("schema"),
            )
    return out


def example(spec: dict, schema: Any, name: str = "") -> Any:
    """A minimal value matching ``schema`` (required fields only)."""
    if not isinstance(schema, dict):
        return None
    if "$ref" in schema:
        return example(spec, spec["components"]["schemas"][schema["$ref"].split("/")[-1]], name)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return next((v for v in schema["enum"] if v is not None), None)
    for key in ("oneOf", "anyOf", "allOf"):
        if key in schema:
            return example(spec, schema[key][0], name)
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), None)
    if kind == "object" or "properties" in schema:
        props = schema.get("properties", {})
        return {k: example(spec, props[k], k) for k in schema.get("required", []) if k in props}
    if kind == "array":
        return [example(spec, schema.get("items"), name)]
    if kind in ("integer", "number"):
        return schema.get("minimum", 1)
    if kind == "boolean":
        return False
    if name in ("id", "sandboxId"):
        return SBX
    return "2026-11-11T00:00:00Z" if schema.get("format") == "date-time" else name or "x"


class Chunks(httpx.SyncByteStream, httpx.AsyncByteStream):
    """A response body sent in exactly these chunks; ``fail`` raises after them (a drop)."""

    def __init__(self, chunks: Iterable[bytes], fail: Optional[BaseException] = None) -> None:
        self.chunks, self.fail, self.closed = list(chunks), fail, False

    def __iter__(self):
        yield from self.chunks
        if self.fail is not None:
            raise self.fail

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.fail is not None:
            raise self.fail

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True


def sse(*frames: tuple[str, Any], ident: bool = True) -> bytes:
    """SSE blocks ``event: <type>`` / ``id: <n>`` / ``data: <json>``."""
    out = []
    for n, (event, data) in enumerate(frames, 1):
        out.append(f"event: {event}\n" + (f"id: {n}\n" if ident else "") + f"data: {json.dumps(data, ensure_ascii=False)}\n\n")
    return "".join(out).encode("utf-8")


def stream_response(body: Union[bytes, Chunks]) -> httpx.Response:
    chunks = body if isinstance(body, Chunks) else Chunks([body])
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=chunks)


def error(status: int, code: Optional[str] = None, **extra: Any) -> httpx.Response:
    body = {"code": code or "refused", "message": "fixture refusal", **extra}
    return httpx.Response(status, json=body, headers={"x-request-id": "req-fixture"})


@dataclass
class MockServer:
    spec: dict = field(default_factory=load_spec)
    seen: list[Seen] = field(default_factory=list)
    answers: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.routes = routes(self.spec)

    def on(self, name: str, answer: Union[httpx.Response, Callable[[httpx.Request], Any]]) -> None:
        """Answer ``name`` with a response, or a callable (raise an httpx error to drop)."""
        assert name in self.routes, name
        self.answers[name] = answer

    def route(self, request: httpx.Request) -> Route:
        path = request.url.raw_path.decode("ascii").split("?", 1)[0]
        path = path[len(httpx.URL(ORIGIN).raw_path):] if path.startswith("/omega/api") else path
        found = [r for r in self.routes.values() if r.method == request.method and r.pattern.match(path)]
        found.sort(key=lambda r: (r.template.count("{"), -len(r.template)))
        assert found, f"no contract route for {request.method} {path}"
        return found[0]

    def handler(self, request: httpx.Request) -> httpx.Response:
        route = self.route(request)
        self.seen.append(Seen(route.name, request, request.read()))
        answer = self.answers.get(route.name)
        if callable(answer):
            answer = answer(request)
        if isinstance(answer, httpx.Response):
            return answer
        if route.name == "sandboxes.files.download":
            return httpx.Response(200, content=b"file-bytes", headers={"content-type": "application/octet-stream"})
        if route.name == "sandboxes.commands.run":
            return stream_response(sse(("started", {"execId": EXEC, "sandboxId": SBX}), ("exit", EXIT0)))
        headers = {"ETag": ETAG} if route.name.startswith("sandboxes.networkPolicy.") else {}
        return httpx.Response(route.status, json=example(self.spec, route.schema), headers=headers)

    @property
    def last(self) -> Seen:
        return self.seen[-1]

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)


EXIT0 = {"exitCode": 0, "timedOut": False, "cancelled": False, "truncated": False,
         "durationMs": 5, "stdoutBytes": 0, "stderrBytes": 0}


def origin(mode: str = "keys", workspace: Optional[str] = None, organization: Optional[str] = None,
           base: str = ORIGIN) -> PlatformOrigin:
    if mode == "bearer":
        headers, secrets = {"Authorization": f"Bearer {FAKE_TOKEN}"}, (FAKE_TOKEN,)
    else:
        headers, secrets = {"X-Api-Key": FAKE_KEY, "X-Secret-Key": FAKE_SECRET}, (FAKE_KEY, FAKE_SECRET)
    headers.update(scope_headers(mode, workspace, organization))
    return PlatformOrigin(httpx.URL(base), mode, "argument", headers, secrets)


def api(server: MockServer, mode: str, auth: str = "keys", retries: int = 3,
        rule: Optional[OriginRule] = None, base: str = ORIGIN) -> Any:
    """``client.sandboxes`` (sync or async) over the mock server; no sleeping between retries.
    The default rule allows the mock's nonloopback HTTPS origin in Bearer mode too."""
    found = origin(auth, base=base)
    shared = PlatformShared(lambda: found, transport=server.transport(), retries=retries,
                            sleep=lambda _s: None, backoff_base_s=0.0)
    rule = rule or OriginRule(allow_custom_base_url=True)
    if mode == "async":
        return AsyncSandboxes(AsyncPlatformCore(shared), rule=rule)
    return Sandboxes(PlatformCore(shared), rule=rule)


async def resolve(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


async def collect(stream: Any) -> list:
    if hasattr(stream, "__aiter__"):
        return [frame async for frame in stream]
    return list(stream)


async def close(stream: Any) -> None:
    await resolve(stream.aclose() if hasattr(stream, "aclose") else stream.close())


def run(coro: Any) -> Any:
    return asyncio.run(coro)


MODES = ("sync", "async")
