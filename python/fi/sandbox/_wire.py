"""Helpers both modes share: the no-retry count, upload bodies, If-Match values, records, and what
``create`` / ``connect`` return in each mode."""

from __future__ import annotations

import os
from typing import IO, Any, Awaitable, Dict, Generator, Mapping, TypeVar, Union

from fi._core.request import BODY_LIMITS

from .errors import ConfigurationError, SandboxError
from .types import NetworkPolicyInfo

#: ``retries=`` for a call that must never be sent twice.
NO_RETRY = 0
UploadBody = Union[bytes, bytearray, memoryview, str, "os.PathLike[str]", IO[bytes]]


def payload(body: UploadBody) -> bytes:
    """Raw upload bytes; a path or a binary file is read up to one byte past the limit, so an
    oversized one is refused before anything is sent."""
    cap = BODY_LIMITS["bundle"] + 1
    if isinstance(body, (bytes, bytearray, memoryview)):
        return bytes(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    if isinstance(body, os.PathLike):
        with open(body, "rb") as handle:
            return handle.read(cap)
    read = getattr(body, "read", None)
    data = read(cap) if callable(read) else None
    if isinstance(data, str):
        data = data.encode("utf-8")
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    raise ConfigurationError(
        "sandboxes.files.upload: the body must be bytes, str, a path or a binary file",
        code="invalid_body",
        operation="sandboxes.files.upload",
    )


def etag(value: Union[str, int]) -> str:
    """``If-Match`` as the server wants it: the quoted revision (``"3"``)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return f'"{value}"'
    text = str(value)
    return text if text.startswith('"') else f'"{text}"'


def policy_info(data: Any, headers: Mapping[str, str]) -> NetworkPolicyInfo:
    """A network-policy response and its ``ETag`` header (the contract's If-Match source). A
    server that sends no ``ETag`` gets the quoted ``policy.desiredRevision`` instead."""
    raw = dict(data) if isinstance(data, Mapping) else {}
    policy = dict(raw["policy"]) if isinstance(raw.get("policy"), Mapping) else {}
    tag = headers.get("etag") or None
    revision = policy.get("desiredRevision")
    if tag is None and isinstance(revision, int) and not isinstance(revision, bool):
        tag = etag(revision)
    return NetworkPolicyInfo(tag, policy, raw)


def sandbox_record(raw: Any, operation: str) -> Mapping[str, Any]:
    record = raw.get("sandbox") if isinstance(raw, Mapping) else None
    if not isinstance(record, Mapping) or not isinstance(record.get("id"), str):
        raise SandboxError(
            f"{operation}: the response has no sandbox record",
            code="invalid_response",
            operation=operation,
        )
    return record


def present(**fields: Any) -> Dict[str, Any]:
    """The fields that are not None (an optional field left out is not sent)."""
    return {key: value for key, value in fields.items() if value is not None}


H = TypeVar("H")


def ready_handle(handle: H) -> H:
    """Sync ``Sandbox.create`` / ``connect``: the handle itself (``with`` deletes it on exit)."""
    return handle


class PendingSandbox(Awaitable[H]):
    """What ``AsyncSandbox.create`` / ``connect`` return: ``await`` it for the handle, or use it
    directly in ``async with`` (the handle is entered, then deleted on exit)."""

    def __init__(self, pending: Awaitable[H]) -> None:
        self._pending = pending
        self._handle: Any = None

    def __await__(self) -> Generator[Any, None, H]:
        return self._pending.__await__()

    async def __aenter__(self) -> H:
        self._handle = await self._pending
        return await self._handle.__aenter__()

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return await self._handle.__aexit__(exc_type, exc, tb)


def awaitable_handle(pending: Awaitable[H]) -> PendingSandbox[H]:
    """Async ``AsyncSandbox.create`` / ``connect``: awaitable, and an async context manager.
    ``scripts/platform/unasync.py`` turns this name into :func:`ready_handle` in the sync twin."""
    return PendingSandbox(pending)
