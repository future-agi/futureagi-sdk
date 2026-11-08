#!/usr/bin/env python3
"""Check run reactivation against an installed wheel using mock HTTP transports."""
import asyncio
import inspect

import httpx
from fi.agents.runs import AsyncRuns, Runs
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared
from fi import AsyncFutureAGIClient, FutureAGIClient


async def call(value):
    return await value if inspect.isawaitable(value) else value


async def main():
    for mode in ("async", "sync"):
        for method in ("send", "retry", "resume"):
            before = {"conversation": {"id": "run-a", "status": "error" if method == "retry" else "done"}}
            receipt = {"accepted": True}
            after = {"conversation": {"id": "run-a", "status": "done"}, "messages": [{"id": "new-message"}]}
            responses = [before, receipt, {"conversation": {"id": "run-a", "status": "active"}}, after]
            requests = []

            def transport(request):
                requests.append(request.method)
                assert responses, "unexpected request"
                return httpx.Response(200, json=responses.pop(0))

            client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(
                base_url="http://127.0.0.1:9000", api_key="fixture-api", secret_key="fixture-secret")
            shared = PlatformShared(client._resolve_platform_origin, transport=httpx.MockTransport(transport))
            core = AsyncPlatformCore(shared) if mode == "async" else PlatformCore(shared)
            client.__dict__["_platform"] = core
            runs = client.agents.runs
            assert isinstance(runs, AsyncRuns if mode == "async" else Runs)
            try:
                run = await call(runs.get("run-a"))
                kwargs = {"input": "next"} if method == "send" else {}
                assert await call(getattr(run, method)(**kwargs)) == receipt
                assert await call(run.wait(timeout=1, sleep=lambda _: None)) is run
                assert requests == ["GET", "POST", "GET", "GET"]
                assert run.response == after
                print(f"PASS: installed wheel {mode} {method} waits for its new turn")
            finally:
                await call(shared.aclose() if mode == "async" else shared.close())


if __name__ == "__main__":
    asyncio.run(main())
