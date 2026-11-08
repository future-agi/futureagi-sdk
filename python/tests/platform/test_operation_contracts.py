"""Generated per-operation wire checks: sync and async use the identical independent oracle."""
from __future__ import annotations

import asyncio
import dataclasses
import json

import httpx
import pytest

from fi import errors
from fi._core.pagination import alist_page, list_page
from ._contract_runtime import Runtime, path_args, resolve, success, stream_events
from ._contract_payloads import envelope_adapter, payloads, plain
from ._gates_support import REPO
from ._console_absence import assert_console_absent

DATA = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
EE_RESOURCE_ERROR = json.loads((REPO / "tests/fixtures/server-contracts/console-404.json").read_text())["ee"][0]["body"]
ROWS = DATA["operations"]
PUBLIC = [(row, mode) for mode in ("sync", "async") for row in ROWS
          if row["id"] in DATA["public_cases"]["py_" + mode] or row.get("public_absence")]
PUBLIC_IDS = [mode + ":" + row["id"] for row, mode in PUBLIC]


def check_wire(row, request):
    path = row["path"]
    for key, value in path_args(row).items():
        path = path.replace("{" + key + "}", value)
    if row["adapter"] == "platform" or row.get("platform_origin"):
        path = "/omega/api" + path
    assert request.method == row["method"], row["id"]
    assert request.url.path == path, row["id"]
    assert ("idempotency-key" in request.headers) is row["idempotent"], row["id"]
    if row["adapter"] == "platform" or row.get("platform_origin"):
        assert request.extensions["fi.retry"]["class"] == row["retry"]


async def wire_case(row, mode):
    requests = []
    def handler(request):
        requests.append(request)
        return success(row)
    runtime = Runtime(row, mode, handler)
    try:
        if row.get("public_absence"):
            assert_console_absent(runtime)
            assert requests == []
            return
        result = await resolve(runtime.call())
        assert len(requests) == 1
        check_wire(row, requests[0])
        if row["stream"]:
            assert [event["type"] for event in result] == stream_events(row)
            assert all(event["marker"] == "kept" for event in result)
        if row["adapter"] != "platform":
            # Compare the public return value. Do not manually unwrap result.result:
            # doing so would hide a missing/bypassed public envelope adapter.
            assert plain(getattr(result, "raw", result)) == payloads(row)[1]
    finally:
        await runtime.close()


@pytest.mark.parametrize("row,mode", PUBLIC, ids=PUBLIC_IDS)
def test_operation_wire_shape(row, mode):
    asyncio.run(wire_case(row, mode))


async def error_case(row, mode):
    answers = [(int(status), None, cls) for status, cls in DATA["status_classes"].items()]
    answers += [(status, code, DATA["status_classes"][str(status)]) for code, status in DATA["fa_codes"].items()]
    answers += [(404, "product_not_admitted", "ProductNotAvailableError"),
                (422, "idempotency_key_reused", "IdempotencyKeyReusedError"),
                (409, "idempotency_key_in_progress", "IdempotencyKeyInProgressError")]
    current = [None]
    def handler(request):
        status, code = current[0]
        body = {"status": False, "code": code, "message": "fixture refusal", "result": "fixture refusal"}
        # This oracle covers resource 404s, not the separately tested unserved Console origin.
        if status == 404 and code is None and request.url.path.startswith("/omega/api/workspace/"):
            body = EE_RESOURCE_ERROR
        return httpx.Response(status, json=body,
                              headers={"Retry-After": "999", "X-Request-Id": "contract-request"})
    runtime = Runtime(row, mode, handler)
    try:
        if row.get("public_absence"):
            for status, code, cls in answers:
                current[0] = (status, code)
                assert_console_absent(runtime)
            return
        for status, code, cls in answers:
            current[0] = (status, code)
            if status == 409 and code in (None, "conflict") and row["adapter"] == "platform" and row["namespace"] == "sandboxes":
                cls = "SandboxStateError"
            with pytest.raises((errors.FutureAGIAPIError, errors.StreamInterruptedError)) as caught:
                await resolve(runtime.call())
            error = caught.value
            if row["stream"] and status not in (401, 403, 404):
                assert isinstance(error, errors.StreamInterruptedError)
                assert error.last_sequence is None
                error = error.__cause__
            assert type(error).__name__ == cls, (row["id"], status, code)
            assert error.status_code == status
            assert error.request_id == "contract-request"
            if code:
                assert error.code == code
    finally:
        await runtime.close()


@pytest.mark.parametrize("row,mode", PUBLIC, ids=PUBLIC_IDS)
def test_operation_status_and_code_classes(row, mode):
    asyncio.run(error_case(row, mode))


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("row", [r for r in ROWS if r["adapter"] == "platform" and r["pagination"]], ids=lambda r: r["id"])
def test_descriptor_pagination_policy(row, mode):
    # Descriptor conformance is not public API acceptance. Unavailable namespaces
    # remain explicitly excluded from PUBLIC, never routed here as a fallback.
    async def run():
        requests = []
        page = row["pagination"]
        def handler(request):
            requests.append(request)
            body = {page["itemsField"]: [{"n": len(requests)}]}
            if page.get("nextCursorField"):
                body[page["nextCursorField"]] = "opaque/+==" if len(requests) == 1 else None
            if page.get("truncatedField"):
                body[page["truncatedField"]] = True
            return httpx.Response(200, json=body)
        runtime = Runtime(row, mode, handler)
        try:
            method = alist_page if mode == "async" else list_page
            result = await resolve(method(runtime.core, row["name"], path=path_args(row)))
            assert result.items == [{"n": 1}]
            if page["style"] == "cursor":
                assert result.next_cursor == "opaque/+=="
                following = await resolve(result.next_page())
                assert following.items == [{"n": 2}] and not following.has_more
                assert requests[1].url.params[page["cursorParam"]] == "opaque/+=="
            else:
                assert not result.has_more
            if page["style"] == "window":
                assert result.truncated
        finally:
            await runtime.close()
    asyncio.run(run())


@pytest.mark.parametrize("row,mode", PUBLIC, ids=PUBLIC_IDS)
def test_operation_retry_class_on_the_wire(row, mode):
    async def run():
        requests = []
        def handler(request):
            requests.append(request)
            if len(requests) == 1:
                return httpx.Response(503, json={"code": "service_unavailable"}, headers={"Retry-After": "0"})
            return success(row)
        runtime = Runtime(row, mode, handler, retries=1)
        try:
            if row.get("public_absence"):
                assert_console_absent(runtime)
                assert requests == []
                return
            retried = row["retry"] in ("http-idempotent", "keyed") and not row["stream"]
            if retried:
                await resolve(runtime.call())
            else:
                with pytest.raises(errors.StreamInterruptedError if row["stream"] else errors.ServerError) as caught:
                    await resolve(runtime.call())
                if row["stream"]:
                    assert isinstance(caught.value.__cause__, errors.ServerError)
                    assert caught.value.__cause__.status_code == 503
            assert len(requests) == (2 if retried else 1)
            for request in requests:
                check_wire(row, request)
            if row["idempotent"]:
                assert len({r.headers["Idempotency-Key"] for r in requests}) == 1
        finally:
            await runtime.close()
    asyncio.run(run())


@pytest.mark.parametrize("row,mode", [(r, m) for r, m in PUBLIC if envelope_adapter(r)],
                         ids=[m + ":" + r["id"] for r, m in PUBLIC if envelope_adapter(r)])
def test_public_operation_maps_http_200_logical_failure(row, mode):
    async def run():
        runtime = Runtime(row, mode, lambda _: httpx.Response(200,
            json={"status": False, "code": "invalid", "result": "fixture refusal"},
            headers={"X-Request-Id": "logical-refusal"}))
        try:
            with pytest.raises(errors.BadRequestError) as caught:
                await resolve(runtime.call())
            assert caught.value.code == "invalid"
            assert caught.value.request_id == "logical-refusal"
        finally:
            await runtime.close()
    asyncio.run(run())


@pytest.mark.parametrize("mutation", ["method", "idempotency"])
def test_seeded_wire_defects_fail_the_gate(mutation):
    row = next(r for r in ROWS if r["adapter"] == "platform" and r["idempotent"] and not r["stream"])
    async def run():
        captured = []
        runtime = Runtime(row, "sync", lambda request: captured.append(request) or success(row))
        original = runtime.core.operation(row["name"])
        changed = dataclasses.replace(original, **({"method": "PUT"} if mutation == "method" else {"idempotent": False}))
        # Inject at the real table lookup, not at the expected contract case.
        runtime.shared.table = {row["name"]: changed}
        try:
            # This control isolates policy mutation; public-wrapper coverage is
            # separately mandatory above and never falls back to this executor.
            body = None if not row["content_type"] else ({} if row["content_type"] == "application/json" else b"fixture")
            await resolve(runtime.core.call(row["name"], path=path_args(row), body=body))
            with pytest.raises(AssertionError):
                check_wire(row, captured[0])
        finally:
            await runtime.close()
    asyncio.run(run())
