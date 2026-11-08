"""A fixture operation table shaped like the pinned contract's, and helpers to drive the platform
executor over ``httpx.MockTransport`` (no network). The rows mirror real operations at
the pinned commit, so the retry classes are the ones the contract gives them."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

import httpx

from fi._core.origins import PlatformOrigin
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.policy import OperationSpec as Op
from fi._core.policy import PaginationSpec as Page
from fi._core.policy import StreamSpec as Stream
from fi._core.transport import PlatformShared

ORIGIN = "https://api.futureagi.com/omega/api"
RUN_EVENTS = ("message_delta", "message_complete", "activity", "activity_output", "status", "error", "done")

OPS: dict[str, Op] = {
    "capabilities.get": Op(
        name="capabilities.get",
        family="platform",
        method="GET",
        path="/workspace/capabilities",
        operation_id="getWorkspaceCapabilities",
    ),
    "runs.create": Op(
        name="runs.create",
        family="runs",
        method="POST",
        path="/workspace/conversations",
        body="json",
        timeout="write",
        rate="model-start",
        idempotent=True,
        durable=True,
        idempotency_key_required=True,
        secret_fields=("request.env",),
    ),
    "runs.get": Op(
        name="runs.get", family="runs", method="GET", path="/workspace/conversations/{id}", path_params=("id",)
    ),
    "runs.list": Op(
        name="runs.list",
        family="runs",
        method="GET",
        path="/workspace/conversations",
        query=("agentId", "cursor", "limit"),
        pagination=Page(
            style="cursor",
            items_field="conversations",
            cursor_param="cursor",
            limit_param="limit",
            next_cursor_field="nextCursor",
        ),
    ),
    "runs.events": Op(
        name="runs.events",
        family="runs",
        method="GET",
        path="/workspace/conversations/{id}/events",
        path_params=("id",),
        query=("transport", "wait"),
        timeout="stream",
        stream=Stream(
            kind="sse-get",
            resume="last-event-id",
            events="OmegaRunEventFrame",
            known_events=RUN_EVENTS,
            keepalive_seconds=15,
            poll_param="transport",
            poll_value="poll",
            poll_wait_param="wait",
            poll_max_wait_ms=25000,
        ),
    ),
    "environments.create": Op(
        name="environments.create",
        family="environments",
        method="POST",
        path="/workspace/environments",
        body="json",
        idempotent=True,
        durable=False,
    ),
    "sandboxes.create": Op(
        name="sandboxes.create", family="sandboxes", method="POST", path="/workspace/sandboxes", body="json"
    ),
    "sandboxes.kill": Op(
        name="sandboxes.kill",
        family="sandboxes",
        method="DELETE",
        path="/workspace/sandboxes/{id}",
        path_params=("id",),
        not_found_means_applied=True,
    ),
    "sandboxes.list": Op(
        name="sandboxes.list",
        family="sandboxes",
        method="GET",
        path="/workspace/sandboxes",
        pagination=Page(style="single-page", items_field="sandboxes"),
    ),
    "files.write": Op(
        name="files.write",
        family="sandboxes",
        method="PUT",
        path="/workspace/sandboxes/{id}/files/{path}",
        path_params=("id", "path"),
        multi_segment=("path",),
        body="bundle",
        content_type="application/octet-stream",
    ),
    "approvals.decide": Op(
        name="approvals.decide",
        family="platform",
        method="POST",
        path="/workspace/approvals/{id}",
        path_params=("id",),
        body="json",
        human_only=True,
    ),
}


class Recorder:
    """A MockTransport handler that answers from a script and records every request."""

    def __init__(self, *answers: Any) -> None:
        self.answers = list(answers)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        answer = self.answers[min(len(self.requests) - 1, len(self.answers) - 1)]
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            return answer(request)
        return answer

    @property
    def keys(self) -> list[Optional[str]]:
        return [r.headers.get("Idempotency-Key") for r in self.requests]


def respond(status: int, body: Any = None, headers: Optional[dict[str, str]] = None) -> httpx.Response:
    if body is None:
        return httpx.Response(status, headers=headers)
    if isinstance(body, (bytes, str)):
        return httpx.Response(status, content=body, headers=headers)
    return httpx.Response(status, json=body, headers=headers)


def sse(*frames: tuple[Optional[str], str, Any], status: int = 200) -> httpx.Response:
    """An SSE response: each frame is ``(id, event, data)``."""
    lines = []
    for frame_id, event, data in frames:
        if frame_id is not None:
            lines.append(f"id: {frame_id}")
        lines.append(f"event: {event}")
        lines.append(f"data: {json.dumps(data)}")
        lines.append("")
    return httpx.Response(
        status, content=("\n".join(lines) + "\n").encode(), headers={"content-type": "text/event-stream"}
    )


def origin(base: str = ORIGIN, headers: Optional[dict[str, str]] = None) -> PlatformOrigin:
    return PlatformOrigin(
        httpx.URL(base),
        "keys",
        "derived",
        headers or {"X-Api-Key": "k-test-1234", "X-Secret-Key": "s-test-1234"},
        ("k-test-1234", "s-test-1234"),
    )


def make_core(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    retries: int = 3,
    sleeps: Optional[list[float]] = None,
    table: Optional[dict[str, Op]] = None,
    resolve: Optional[Callable[[], PlatformOrigin]] = None,
) -> PlatformCore:
    sink = sleeps if sleeps is not None else []
    shared = PlatformShared(
        resolve or origin,
        retries=retries,
        table=table or OPS,
        transport=httpx.MockTransport(handler),
        sleep=sink.append,
    )
    return PlatformCore(shared)


def make_async_core(
    handler: Callable[[httpx.Request], Any],
    *,
    retries: int = 3,
    sleeps: Optional[list[float]] = None,
    table: Optional[dict[str, Op]] = None,
) -> AsyncPlatformCore:
    sink = sleeps if sleeps is not None else []

    async def sleep(seconds: float) -> None:
        sink.append(seconds)

    shared = PlatformShared(
        origin, retries=retries, table=table or OPS, transport=httpx.MockTransport(handler), sleep=sleep
    )
    return AsyncPlatformCore(shared)
