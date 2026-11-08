"""Multipart audio uploads with published string-content and field semantics.

Explicit PathLike inputs are additive. ``audio_upload_mode='normalized'`` opts
into string paths, omitted null fields and repeated bracket-named list fields.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers,
    collect_agentcc_params,
    merge_session_headers,
)
from fi.gateway._constants import NOT_GIVEN
from fi.gateway._transport._base import RequestOptions
from fi.gateway._utils import parse_timeout

#: Form fields the gateway reads as a list, under their ``[]`` name.
_LIST_FIELDS = {"timestamp_granularities": "timestamp_granularities[]"}

_FILE_TYPES = (
    "bytes, a file opened in binary mode, an os.PathLike path or a "
    "(filename, content[, content_type]) tuple"
)


def upload_part(file: Any, *, string_paths: bool = False) -> Any:
    """The ``file`` part as httpx sends it.

    Bytes, a binary file object and a ``(filename, content[, content_type])`` tuple are
    sent as given; an ``os.PathLike`` path is read and sent under its file name (also
    as a tuple's content). Bare strings are literal content, including NUL/newline.
    Only ``string_paths=True`` interprets strings as deprecated filesystem paths;
    those paths reject NUL and newline before any read.

    Bytes, and a file object without a ``name``, go under the file name ``upload``;
    the provider may read the audio format from the name's extension, so pass a tuple
    or a path when it does.
    """
    if string_paths and isinstance(file, str):
        import warnings

        if any(char in file for char in ("\x00", "\n", "\r")):
            raise TypeError("String audio paths must not contain NUL or newline characters")
        warnings.warn(
            "String audio paths are deprecated; pass pathlib.Path(...) instead. "
            "Bare strings will raise TypeError in 1.0.",
            DeprecationWarning, stacklevel=3,
        )
        file = Path(file)
    if isinstance(file, os.PathLike):
        path = Path(os.fspath(file))
        return (path.name, path.read_bytes())
    if isinstance(file, tuple) and len(file) >= 2 and isinstance(file[1], os.PathLike):
        return (file[0], Path(os.fspath(file[1])).read_bytes(), *file[2:])
    return file


def form_fields(
    model: str, fields: dict[str, Any], extra: dict[str, Any] | None = None,
    *, normalized: bool = False,
) -> dict[str, Any]:
    """Keep published names and explicit nulls.

    Only a method's own omitted parameters (``NOT_GIVEN`` in *fields*) are skipped;
    *extra* (its extra body and keyword arguments) is kept verbatim, as published.
    The transport applies published JSON/string conversion at send time. Explicit
    normalized mode instead drops every null or omitted value and uses repeated
    bracket-named list fields.
    """
    form: dict[str, Any] = {"model": model}
    if normalized:
        for key, value in {**fields, **(extra or {})}.items():
            if value is NOT_GIVEN or value is None:
                continue
            form[_LIST_FIELDS.get(key, key)] = value
        return form
    for key, value in fields.items():
        if value is not NOT_GIVEN:
            form[key] = value
    form.update(extra or {})
    return form


def upload_request(
    client: Any,
    url: str,
    *,
    file: Any,
    model: str,
    fields: dict[str, Any],
    gateway: dict[str, Any],
    properties: dict[str, str] | None,
    user_id: str | None,
    request_id: str | None,
    extra_headers: dict[str, str] | None,
    timeout: Any,
    extra: dict[str, Any] | None = None,
) -> tuple[RequestOptions, dict[str, Any]]:
    """The request options and gateway parameters of one upload to *url*.

    *fields* are the method's own form parameters; *extra* its extra body and keyword
    arguments, applied after them; *gateway* the gateway parameters, sent as headers
    by the transport.
    """
    normalized = getattr(client, "_audio_upload_mode", "published") == "normalized"
    part = upload_part(file, string_paths=normalized)
    body = form_fields(model, fields, extra, normalized=normalized)
    agentcc_params = collect_agentcc_params(**gateway)
    headers = build_extra_headers(
        extra_headers=extra_headers,
        properties=properties,
        user_id=user_id,
        request_id=request_id,
    )
    headers = merge_session_headers(client, headers, agentcc_params, defer=True)
    options = RequestOptions(
        method="POST",
        url=url,
        headers=headers,
        timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        files={"file": part},
        body=None if normalized else body,
        form=body if normalized else None,
    )
    return options, agentcc_params
