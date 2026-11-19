"""One request from an operation and its arguments (ported from the Omega runtime's
``request_build.py``): the path from the generated template with every parameter
encoded, only the query keys the contract declares, and the body with its size limit checked
before anything is sent. Standard library only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.parse import quote, urlencode

from fi._core.policy import OperationSpec
from fi.errors import ConfigurationError, PayloadTooLargeError

#: Body limits checked before any network call (the gateway's body classes).
BODY_LIMITS = {"json": 1024 * 1024, "bundle": 64 * 1024 * 1024}


def _segment(value: str, name: str, op: OperationSpec) -> str:
    if value in ("", ".", ".."):
        raise ConfigurationError(
            f'{op.name}: path parameter {name} must not be empty, "." or ".."',
            code="invalid_path_param",
            operation=op.name,
        )
    return quote(value, safe="")


def build_path(op: OperationSpec, params: Optional[Mapping[str, Any]] = None) -> str:
    """The request path with every parameter percent-encoded. Raises on a missing, unknown, empty,
    ``.`` or ``..`` parameter, so a value can never climb out of its path segment."""
    params = params or {}
    path = op.path
    for name in op.path_params:
        if name not in params or params[name] is None:
            raise ConfigurationError(
                f"{op.name}: missing path parameter {name}", code="missing_path_param", operation=op.name
            )
        value = str(params[name])
        if name in op.multi_segment:
            encoded = "/".join(_segment(part, name, op) for part in value.lstrip("/").split("/"))
        else:
            encoded = _segment(value, name, op)
        path = path.replace("{" + name + "}", encoded, 1)
    unknown = sorted(set(params) - set(op.path_params))
    if unknown:
        raise ConfigurationError(
            f"{op.name} has no path parameter {unknown[0]}", code="unknown_path_param", operation=op.name
        )
    return path


def _query_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_query(op: OperationSpec, query: Optional[Mapping[str, Any]] = None) -> list[tuple[str, str]]:
    """The query pairs, sorted. ``None`` values are dropped; an undeclared key is refused, so it is
    never sent (a list value repeats the key)."""
    pairs: list[tuple[str, str]] = []
    for key in sorted(query or {}):
        value = (query or {})[key]
        if value is None:
            continue
        if key not in op.query:
            raise ConfigurationError(
                f"{op.name} does not declare the query key {key}, so it is not sent",
                code="undeclared_query_key",
                operation=op.name,
            )
        if isinstance(value, (list, tuple)):
            pairs.extend((key, _query_text(item)) for item in value)
        else:
            pairs.append((key, _query_text(value)))
    return pairs


def query_string(pairs: list[tuple[str, str]]) -> str:
    return "?" + urlencode(pairs) if pairs else ""


@dataclass(frozen=True)
class EncodedBody:
    """The encoded body and its media type, after the size check."""

    content: Optional[bytes]
    content_type: Optional[str]
    size: int


def build_body(op: OperationSpec, body: Any) -> EncodedBody:
    """JSON (or raw bytes for a bundle route), refused locally past its limit with
    ``PayloadTooLargeError(local=True)``."""
    if body is None:
        return EncodedBody(None, None, 0)
    if op.body == "none":
        raise ConfigurationError(f"{op.name} takes no request body", code="unexpected_body", operation=op.name)
    limit = BODY_LIMITS[op.body]
    if isinstance(body, (bytes, bytearray, memoryview)):
        content, content_type = bytes(body), op.content_type or "application/octet-stream"
    else:
        try:
            content = json.dumps(body, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise ConfigurationError(
                f"{op.name}: the request body is not JSON ({type(error).__name__})",
                code="invalid_body",
                operation=op.name,
            ) from None
        content_type = "application/json"
    if len(content) > limit:
        raise PayloadTooLargeError(
            413,
            None,
            limit_bytes=limit,
            local=True,
            code="payload_too_large",
            operation=op.name,
            message=f"{op.name}: the request body is {len(content)} bytes; the limit is {limit} bytes (nothing was sent)",
        )
    return EncodedBody(content, content_type, len(content))
