"""Read a multipart form request back into its values and files, as a server parses it.

A test helper only: the standard library's MIME parser splits the form at the request's
own boundary, so a test asserts what a multipart reader (the gateway's
``ParseMultipartForm``) would see, not the bytes httpx happened to write.
"""

from __future__ import annotations

from email.message import Message
from email.parser import BytesParser
from email.policy import HTTP
from typing import Any

FORM_TYPE = "multipart/form-data; boundary="


def read_form(
    request: Any,
) -> tuple[dict[str, list[str]], dict[str, tuple[str, bytes, str]]]:
    """``(values, files)`` of a multipart request.

    ``values`` maps each form field to its values in order (a repeated field has
    several); ``files`` maps each file part to ``(filename, content, content_type)``.
    Fails unless the request is a multipart form.
    """
    content_type = request.headers["content-type"]
    assert content_type.startswith(FORM_TYPE), content_type
    raw = b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + request.content
    message = BytesParser(policy=HTTP).parsebytes(raw)
    assert message.is_multipart(), content_type
    values: dict[str, list[str]] = {}
    files: dict[str, tuple[str, bytes, str]] = {}
    for part in message.iter_parts():
        assert isinstance(part, Message)
        name = part.get_param("name", header="content-disposition")
        assert isinstance(name, str), part
        payload = part.get_payload(decode=True)
        assert isinstance(payload, bytes), part
        filename = part.get_filename()
        if filename is None:
            values.setdefault(name, []).append(payload.decode("utf-8"))
        else:
            files[name] = (filename, payload, part.get_content_type())
    return values, files
