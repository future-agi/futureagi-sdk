"""The multipart request of an audio upload (``/v1/audio/transcriptions``, ``/translations``).

The gateway reads these routes as a multipart form: the audio in the ``file`` part and
every other field as a form value, a list as repeated ``<name>[]`` values. agentcc 1.x
put ``file`` into a JSON body, so bytes and file objects failed to serialize before a
request was sent, and anything else reached the gateway as JSON, which it refuses
(``400 invalid_form``).
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


def upload_part(file: Any) -> Any:
    """The ``file`` part as httpx sends it.

    Bytes, a binary file object and a ``(filename, content[, content_type])`` tuple are
    sent as given; an ``os.PathLike`` path is read and sent under its file name (also
    as a tuple's content). In 0.x, a bare ``str`` is a deprecated file path; pass
    ``Path(...)`` instead. Strings containing NUL or newline are never read.

    Bytes, and a file object without a ``name``, go under the file name ``upload``;
    the provider may read the audio format from the name's extension, so pass a tuple
    or a path when it does.
    """
    if isinstance(file, str):
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


def form_fields(model: str, fields: dict[str, Any]) -> dict[str, Any]:
    """The form values: ``model``, then every given field (``NOT_GIVEN`` and ``None``
    are left out; a list field goes under its ``[]`` name)."""
    form: dict[str, Any] = {"model": model}
    for key, value in fields.items():
        if value is NOT_GIVEN or value is None:
            continue
        form[_LIST_FIELDS.get(key, key)] = value
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
) -> tuple[RequestOptions, dict[str, Any]]:
    """The request options and gateway parameters of one upload to *url*.

    *fields* are the form fields (the method's own, then its extra body and keyword
    arguments); *gateway* the gateway parameters, sent as headers by the transport.
    """
    part = upload_part(file)
    agentcc_params = collect_agentcc_params(**gateway)
    headers = build_extra_headers(
        extra_headers=extra_headers,
        properties=properties,
        user_id=user_id,
        request_id=request_id,
    )
    headers = merge_session_headers(client, headers, agentcc_params)
    options = RequestOptions(
        method="POST",
        url=url,
        headers=headers,
        timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        files={"file": part},
        form=form_fields(model, fields),
    )
    return options, agentcc_params
