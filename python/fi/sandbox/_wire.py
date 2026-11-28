"""Helpers both modes share: the no-retry count, upload bodies, the download limit, files paths
(relative to /workspace), the scrubber for a stream's failure text, If-Match values, records,
and what ``create`` / ``connect`` return in each mode."""

from __future__ import annotations

import os
import re
from typing import (
    IO,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Mapping,
    Optional,
    TypeVar,
    Union,
)

from fi._core.platform_base import _values
from fi._core.redact import request_secret_values, scrub_value
from fi._core.request import BODY_LIMITS
from fi._core.transport import MAX_ERROR_BODY
from fi._extra_headers import ExtraHeadersError

from .errors import ConfigurationError, PayloadTooLargeError, SandboxError
from .types import NetworkPolicyInfo

#: ``retries=`` for a call that must not be sent twice.
NO_RETRY = 0
UploadBody = Union[bytes, bytearray, memoryview, str, "os.PathLike[str]", IO[bytes]]
#: The most bytes a download keeps unless ``max_bytes=`` says otherwise: the upload limit.
DOWNLOAD_LIMIT = BODY_LIMITS["bundle"]
DOWNLOAD = "sandboxes.files.download"
#: The folder every files path is relative to: the files routes' root. Built from its name, as in
#: TypeScript, so no module spells an API path.
_WORKSPACE_NAME = "workspace"
WORKSPACE = f"/{_WORKSPACE_NAME}"
#: The longest files path the files API takes, in characters (after the /workspace prefix).
MAX_PATH_CHARS = 4096
#: How much of a refused path its error shows, in characters.
_SHOWN_CHARS = 200
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class DownloadBudget:
    """What one download may keep: ``limit`` bytes (None: :data:`DOWNLOAD_LIMIT`). Built
    before the request is sent, so a bad limit sends nothing; a ``Content-Length`` over it is
    refused before a byte is read, and a body that grows past it as it arrives, so nothing past
    the limit is ever kept (``download_to`` then removes its partial file)."""

    def __init__(self, limit: Any = None) -> None:
        limit = DOWNLOAD_LIMIT if limit is None else limit
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ConfigurationError(
                f"{DOWNLOAD}: max_bytes must be a whole number of bytes above 0",
                code="invalid_option",
                operation=DOWNLOAD,
            )
        self.limit, self.size = limit, 0

    def start(self, response: Any, core: Any, name: str, request: Any) -> None:
        """Refuse a response whose ``Content-Length`` is over the limit, or that is encoded (a
        download asks for identity, so the limit counts the bytes received), before reading it."""
        declared = response.headers.get("content-length", "").strip()
        if declared.isdigit() and int(declared) > self.limit:
            raise self._over()
        encoding = response.headers.get("content-encoding", "").strip()
        if encoding.lower() not in ("", "identity"):
            said = failure_text(core, name, request, None)(encoding)
            text = f"{name}: refused Content-Encoding {said!r}; downloads ask for identity"
            raise SandboxError(text, code="download_encoded", operation=name)

    def take(self, chunk: bytes) -> bytes:
        """``chunk``, or the refusal once the bytes so far are over the limit."""
        self.size += len(chunk)
        if self.size > self.limit:
            raise self._over()
        return chunk

    def _over(self) -> PayloadTooLargeError:
        error = PayloadTooLargeError(
            413,
            None,
            code="download_too_large",
            operation=DOWNLOAD,
            message=f"{DOWNLOAD}: the file is larger than the download limit of {self.limit} "
            "bytes, so it was not kept; pass a larger max_bytes= to sbx.files.download or "
            "sbx.files.download_to",
        )
        error.limit_bytes, error.local = self.limit, True
        return error


def failure_text(core: Any, name: str, request: Any, body: Any) -> Callable[[str], str]:
    """What the server's failure text in a stream passes through, as the HTTP error path treats
    an error body: the executor's error scrubber over every secret the request carried (the
    origin's, the extra headers' values, the request's secret fields such as ``commands.run``'s
    ``env``), then the error-body length cap."""
    shared = core.shared
    try:
        extra = {} if shared.extra_headers is None else shared.extra_headers.for_url(request.url)
    except ExtraHeadersError:  # changed since it was sent: scrub every value the request carried
        extra = dict(request.headers)
    marked = core.operation(name).secret_fields
    secrets = [*shared.origin().secrets, *_values(extra), *request_secret_values(body, marked)]
    scrub = shared.error_scrubber or scrub_value

    def private(text: str) -> str:
        clean = scrub(text, secrets)
        clean = clean if isinstance(clean, str) else str(clean)
        return clean.encode("utf-8")[:MAX_ERROR_BODY].decode("utf-8", "replace")

    return private


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


def files_path(
    path: Any, operation: str, *, root: bool = False, name: str = "path"
) -> Optional[str]:
    """``path`` as the files routes take it: relative to /workspace. A relative path is sent as
    it is and an absolute one under /workspace without that prefix (/workspace/src/a.py as
    ``src/a.py``); repeated and trailing slashes are dropped. /workspace itself (with or without
    a trailing slash), ``"."`` and ``""`` are its root, which only a listing takes (``root=True``:
    None, so no path is sent). A path outside /workspace, a ``.`` or ``..`` segment anywhere
    (/workspace/. included; nothing is folded), a backslash, a NUL or another control character,
    or a path over :data:`MAX_PATH_CHARS` raises ``ConfigurationError`` (``invalid_path``) before
    any request; its text shows the path as given, cut to 200 characters. A path outside
    /workspace also gets ``detail={"reason": "outside_workspace"}``, whatever else it has."""
    text = os.fspath(path) if isinstance(path, os.PathLike) else path
    if text is None and root:  # no path at all: the root
        return None
    if not isinstance(text, str):
        raise _bad_path(operation, f"{name} must be text, not {type(path).__name__}")
    parts, absolute = [part for part in text.split("/") if part], text.startswith("/")
    outside = absolute and parts[:1] != [_WORKSPACE_NAME]
    if "\\" in text or _CONTROL.search(text):
        problem = "has a backslash, a NUL or another control character"
    elif outside:
        problem = f"is outside {WORKSPACE}"
    else:
        if absolute:
            parts = parts[1:]
        elif parts == ["."]:  # "." is the root; after /workspace it is a "." segment
            parts = []
        relative = "/".join(parts)
        if "." in parts or ".." in parts:
            problem = 'has a "." or ".." segment'
        elif len(relative) > MAX_PATH_CHARS:
            problem = (
                f"is {len(relative)} characters long; the files API takes at most "
                f"{MAX_PATH_CHARS}"
            )
        elif parts or root:
            return relative or None
        else:
            problem = f"is {WORKSPACE} itself, and this call needs a file or folder under it"
    shown = text if len(text) <= _SHOWN_CHARS else text[:_SHOWN_CHARS] + "..."
    raise _bad_path(operation, f"{name} {shown!r} {problem}", outside=outside)


def _bad_path(operation: str, problem: str, *, outside: bool = False) -> ConfigurationError:
    error = ConfigurationError(
        f"{operation}: {problem}; sandbox paths are relative to {WORKSPACE} (src/app.py, or "
        f"{WORKSPACE}/src/app.py, is the file {WORKSPACE}/src/app.py)",
        code="invalid_path",
        operation=operation,
    )
    error.detail = {"reason": "outside_workspace"} if outside else None
    return error


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
