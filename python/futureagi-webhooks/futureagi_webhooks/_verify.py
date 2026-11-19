"""Verify Future AGI webhook requests (Standard Webhooks v1). Standard library only.

Every request Future AGI sends to a webhook endpoint carries three headers:

- ``webhook-id``: the event id (``evt_...``), the same on every retry and redelivery;
- ``webhook-timestamp``: Unix seconds of this attempt;
- ``webhook-signature``: ``v1,<base64>``, or two space-separated entries during a secret rotation.

The signature is ``base64(HMAC-SHA256(key, "<webhook-id>.<webhook-timestamp>.<raw body>"))``, where ``key`` is the
base64-decoded part of the endpoint's ``whsec_...`` secret. A request is genuine when any ``v1`` entry matches and the
timestamp is within ``tolerance_s`` (300 s) of now, in either direction.

Use it in a receiver::

    from fi.webhooks import verify, WebhookVerificationError

    try:
        event = verify(body=request.body, headers=request.headers, secret=os.environ["FI_WEBHOOK_SECRET"])
    except WebhookVerificationError:
        return HttpResponse(status=400)
    if event.get("test"):
        return HttpResponse(status=200)

Verify the **raw** request body (Django ``request.body``, Flask ``request.get_data()``, FastAPI ``await
request.body()``). A body that was parsed and serialized again does not verify.

This module imports nothing outside the Python standard library, so the small ``futureagi-webhooks`` distribution
ships it unchanged for receivers that do not want the whole SDK. Any Standard Webhooks library verifies the same
requests.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import time
from typing import Any, Iterable, Mapping, Optional, Tuple, Union

__all__ = [
    "SECRET_PREFIX",
    "TOLERANCE_S",
    "VERIFY_RESULTS",
    "WebhookSecretError",
    "WebhookVerificationError",
    "secret_key",
    "sign",
    "signature_header",
    "verify",
    "verify_result",
]

SECRET_PREFIX = "whsec_"
TOLERANCE_S = 300
KEY_BYTES_MIN = 24
KEY_BYTES_MAX = 64
SIGNATURE_VERSION = "v1"

VERIFY_RESULTS = (
    "ok",
    "missing_headers",
    "invalid_timestamp",
    "timestamp_too_old",
    "timestamp_too_new",
    "no_matching_signature",
)
_REQUIRED = ("webhook-id", "webhook-timestamp", "webhook-signature")
_TIMESTAMP = re.compile(r"[0-9]{1,12}")

Body = Union[bytes, bytearray, memoryview, str]
Headers = Union[Mapping[Any, Any], Iterable[Tuple[Any, Any]]]

_MESSAGES = {
    "missing_headers": "the request lacks the {missing} header(s); is this a Future AGI webhook request?",
    "invalid_timestamp": "webhook-timestamp is not a Unix time in whole seconds",
    "timestamp_too_old": "webhook-timestamp is more than {tolerance} s in the past (a replayed request, or this "
    "server's clock is wrong)",
    "timestamp_too_new": "webhook-timestamp is more than {tolerance} s in the future (this server's clock is wrong)",
    "no_matching_signature": "no v1 signature matches this secret and body. Verify the raw request body, not "
    "re-serialized JSON, with the endpoint's current secret",
    "invalid_body": "the signed body is not a JSON object",
}


class WebhookVerificationError(ValueError):
    """The request is not a genuine, current Future AGI webhook request: answer it with a 4xx.

    ``reason`` is one of ``missing_headers``, ``invalid_timestamp``, ``timestamp_too_old``, ``timestamp_too_new``,
    ``no_matching_signature`` (the conformance ids) or ``invalid_body`` (the signature matched, but the body is not a
    JSON object; one that starts with a UTF-8 BOM is not, here and in TypeScript)."""

    def __init__(self, reason: str, message: Optional[str] = None) -> None:
        self.reason = reason
        super().__init__(message or _MESSAGES.get(reason, reason))


class WebhookSecretError(ValueError):
    """The secret is not ``whsec_`` followed by padded standard base64 of 24 to 64 bytes.

    This is a configuration error on the receiver, not a bad request: let it surface as a 5xx, so Future AGI keeps
    retrying the delivery until the secret is fixed. ``reason`` is ``missing_prefix``, ``not_base64`` or
    ``bad_length``."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        text = {
            "missing_prefix": "the webhook secret must start with 'whsec_' (copy it whole from Future AGI)",
            "not_base64": "the webhook secret is not 'whsec_' followed by padded standard base64",
            "bad_length": "the webhook secret must decode to 24-64 bytes",
        }.get(reason, reason)
        super().__init__(text)


def secret_key(secret: str) -> bytes:
    """The HMAC key of a ``whsec_`` secret: the decoded bytes after the prefix (24-64 bytes)."""
    if not isinstance(secret, str) or not secret.startswith(SECRET_PREFIX):
        raise WebhookSecretError("missing_prefix")
    raw = secret[len(SECRET_PREFIX) :]
    try:
        key = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        raise WebhookSecretError("not_base64") from None
    if base64.b64encode(key).decode("ascii") != raw:
        raise WebhookSecretError("not_base64")
    if not KEY_BYTES_MIN <= len(key) <= KEY_BYTES_MAX:
        raise WebhookSecretError("bad_length")
    return key


def _as_bytes(body: Body) -> bytes:
    if isinstance(body, bytes):
        return body
    if isinstance(body, (bytearray, memoryview)):
        return bytes(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    raise TypeError(f"body must be the raw request body (bytes or str), not {type(body).__name__}")


def _signed_content(msg_id: str, timestamp: int, body: bytes) -> bytes:
    if "." in msg_id:
        raise ValueError("webhook-id must not contain '.'")
    return msg_id.encode("ascii") + b"." + str(int(timestamp)).encode("ascii") + b"." + body


def sign(secret: str, msg_id: str, timestamp: int, body: Body) -> str:
    """``base64(HMAC-SHA256(key, "<msg_id>.<timestamp>.<body>"))``: the value after ``v1,``.

    Useful to build signed requests in a receiver's own tests."""
    mac = hmac.new(secret_key(secret), _signed_content(msg_id, timestamp, _as_bytes(body)), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode("ascii")


def signature_header(secrets_newest_first: Iterable[str], msg_id: str, timestamp: int, body: Body) -> str:
    """The ``webhook-signature`` value: ``v1,<sig>`` per secret, newest first, space-separated."""
    items = [f"{SIGNATURE_VERSION}," + sign(s, msg_id, timestamp, body) for s in secrets_newest_first]
    if not items:
        raise ValueError("no signing secret")
    return " ".join(items)


def _text(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("latin-1")
    return str(value)


def _lower_headers(headers: Headers) -> dict:
    """Header names lower-cased; the first value of a repeated name wins. Accepts any mapping (Django
    ``request.headers``, Flask/Werkzeug, Starlette), a list of pairs (ASGI raw headers, bytes included) and a WSGI
    environ or Django ``request.META`` (``HTTP_WEBHOOK_ID``)."""
    items = headers.items() if hasattr(headers, "items") else headers
    out: dict = {}
    environ: dict = {}
    for name, value in items:
        key = _text(name)
        low = key.lower()
        if key.startswith("HTTP_"):
            environ.setdefault(key[5:].replace("_", "-").lower(), _text(value))
        out.setdefault(low, _text(value))
    for name, value in environ.items():
        out.setdefault(name, value)
    return out


def verify_result(
    secret: str,
    headers: Headers,
    body: Body,
    *,
    now: Optional[int] = None,
    tolerance_s: int = TOLERANCE_S,
) -> str:
    """``"ok"`` or the reason id (:data:`VERIFY_RESULTS`), the shape of the language-neutral conformance vectors.

    A secret that is not a valid ``whsec_`` secret matches nothing (``no_matching_signature``). Comparison is
    constant time, and every ``v1`` entry is compared."""
    h = _lower_headers(headers)
    if not all(name in h for name in _REQUIRED):
        return "missing_headers"
    ts = h["webhook-timestamp"]
    if not _TIMESTAMP.fullmatch(ts):
        return "invalid_timestamp"
    t = int(ts)
    current = int(time.time()) if now is None else int(now)
    if current - t > tolerance_s:
        return "timestamp_too_old"
    if t - current > tolerance_s:
        return "timestamp_too_new"
    try:
        expected = sign(secret, h["webhook-id"], t, body).encode("ascii")
    except (ValueError, UnicodeEncodeError):
        return "no_matching_signature"
    matched = False
    for item in h["webhook-signature"].split(" "):
        version, _, value = item.partition(",")
        if version == SIGNATURE_VERSION and hmac.compare_digest(value.encode("utf-8", "replace"), expected):
            matched = True
    return "ok" if matched else "no_matching_signature"


def verify(
    body: Body,
    headers: Headers,
    secret: str,
    *,
    tolerance_s: int = TOLERANCE_S,
    now: Optional[int] = None,
) -> dict:
    """Check a request and return its event (the parsed JSON body, ``test`` included).

    Raises :class:`WebhookVerificationError` (answer 4xx) for a request that is not genuine or not current, and
    :class:`WebhookSecretError` (let it be a 5xx) when ``secret`` itself is malformed. The event's ``id`` is the
    ``webhook-id``: dedupe on it, since delivery is at least once."""
    secret_key(secret)  # a malformed secret is the receiver's configuration error, not a bad request
    raw = _as_bytes(body)
    result = verify_result(secret, headers, raw, now=now, tolerance_s=tolerance_s)
    if result != "ok":
        missing = ", ".join(n for n in _REQUIRED if n not in _lower_headers(headers))
        raise WebhookVerificationError(
            result, _MESSAGES[result].format(missing=missing or "webhook-*", tolerance=tolerance_s)
        )
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise WebhookVerificationError("invalid_body") from None
    if not isinstance(event, dict):
        raise WebhookVerificationError("invalid_body")
    return event
