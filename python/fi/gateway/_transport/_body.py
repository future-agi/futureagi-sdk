"""Released JSON and multipart send arguments, without retaining header aliases."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fi.gateway._transport._request import _uses_form

if TYPE_CHECKING:
    from fi.gateway._transport._base import RequestOptions


def send_arguments(options: RequestOptions, headers: dict[str, str]) -> dict[str, Any]:
    """The body arguments of one send: ``json=`` or, with ``files``, the multipart
    ``files=`` and ``data=``.

    A multipart send drops the JSON ``Content-Type`` from *headers* (any spelling), so
    httpx sets the form's own with its boundary.
    """
    try:
        if not _uses_form(options):
            return {"json": options.body}
        for name in [k for k in headers if k.lower() == "content-type"]:
            del headers[name]
        data = options.form
        if data is None:
            import json

            # Published multipart descriptors retain their unencoded body for callbacks.
            data = {
                key: value if isinstance(value, str) else json.dumps(value)
                if isinstance(value, (list, dict)) else str(value)
                for key, value in (options.body or {}).items()
            }
        return {"files": options.files, "data": data}
    finally:
        headers = None
