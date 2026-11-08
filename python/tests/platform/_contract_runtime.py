"""Mock-only public-wrapper dispatch in both Python modes; no executor fallback."""
from __future__ import annotations

import inspect

import httpx

from fi import AsyncFutureAGIClient, FutureAGIClient
from ._contract_public import UUID, invoke, method_at, public_path
from ._contract_payloads import payloads

BASE = "http://127.0.0.1:9"


def path_args(row):
    return {p: str(row.get("path_values", {}).get(p, UUID)) for p in row["path_params"]}


class Runtime:
    def __init__(self, row, mode, handler, retries=0):
        wrapper = row.get("public_wrappers", {}).get("py_" + mode)
        self.row, self.mode = ({**row, "public_wrapper": wrapper} if wrapper else row), mode
        self.preparing, self.setup_requests, self.handles = None, [], {}

        def transport_handler(request):
            if self.preparing is None:
                return handler(request)
            fixture = self.preparing
            self.setup_requests.append(request)
            assert request.method == fixture["request"]["method"]
            assert str(request.url) == BASE + fixture["request"]["path"]
            assert "idempotency-key" not in request.headers
            return httpx.Response(200, json=fixture["response"])

        cls = AsyncFutureAGIClient if mode == "async" else FutureAGIClient
        self.client = cls(api_key="contract-api", secret_key="contract-secret", base_url=BASE, retries=retries)
        transport = self.client.generated_client._httpx_args["transport"]
        transport._wrapped = httpx.MockTransport(transport_handler)
        transport._wrapped_async = httpx.MockTransport(transport_handler)
        # Keep the actual root's composed tables and namespace registration. Only
        # replace the HTTP boundary, including the supplemental connector table.
        self.core = self.client._platform
        self.shared = self.core.shared
        self.shared.sleep = lambda _: None
        self.shared._recorder._inner = httpx.MockTransport(transport_handler)
        self.shared._recorder._inner_async = httpx.MockTransport(transport_handler)
        if row["adapter"] == "management":
            management = self.client._management.shared
            management.sleep = lambda _: None
            management._recorder._inner = httpx.MockTransport(transport_handler)
            management._recorder._inner_async = httpx.MockTransport(transport_handler)

    async def prepare(self, path=None):
        # Absence candidates can have only a comparison-language spelling; do
        # not require an offered Python wrapper to construct their real handle.
        root = (path if path is not None else public_path(self.row)).split(".")[0]
        if root != "client" and root not in self.handles:
            fixture = self.row.get("handle_fixtures", {}).get(root)
            if fixture is None or "py" not in fixture:
                raise ValueError(f"public handle fixture required for {root}; no executor fallback")
            self.preparing = fixture
            try:
                before = len(self.setup_requests)
                factory = method_at(self.client, fixture["py"]["path"])
                self.handles[root] = await resolve(factory(*fixture["py"].get("args", []), **fixture["py"].get("kwargs", {})))
                assert len(self.setup_requests) == before + 1
                assert self.handles[root].id == UUID
            finally:
                self.preparing = None

    async def call(self):
        await self.prepare()
        result = await resolve(invoke(self.client, self.row, self.handles))
        if self.row.get("stream"):
            if self.mode == "async":
                return [event async for event in result]
            return list(result)
        return result

    async def close(self):
        if self.mode == "async":
            await self.client.aclose()
        else:
            self.client.close()


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def stream_events(row):
    events = row["stream"]["known_events"]
    # A public Run iterator ends at done; exercise every declared frame before it.
    return [event for event in events if event != "done"] + (["done"] if "done" in events else [])


def success(row):
    if row["stream"]:
        text = ": heartbeat\n\n" + "".join(f'event: {e}\nid: {i}\ndata: {{"type":"{e}","marker":"kept"}}\n\n' for i, e in enumerate(stream_events(row), 1))
        return httpx.Response(200, text=text, headers={"content-type": "text/event-stream"})
    status = row.get("success_status", 200)
    return httpx.Response(status) if status == 204 else httpx.Response(status, json=payloads(row)[0])
