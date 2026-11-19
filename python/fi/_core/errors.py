"""One status-to-class mapping for every namespace, core and platform.

:func:`api_error` reads the three platform error shapes, falling back to the status alone:

- gateway: ``{error: "<code>", reason, requestId, retryAfterSeconds?}``
- EE:      ``{code, message, detail, request_id, error: {code, message, detail}}``
- Hub:     ``{error: {code, message, fix}}``

FA Django bodies (``{"detail": "..."}``) are in none of them, so a core namespace's error is
classified by status, which is the same class a platform namespace gets for that status. A known
``code`` in a matching status family picks a narrower class (``idempotency_key_in_progress`` is
:class:`~fi.errors.IdempotencyKeyInProgressError`, a ``ConflictError``); an unknown code keeps its
string and the status picks the class. A string is read as a code only when it looks like one
(``snake_case``), so a Django ``{"error": "Some sentence"}`` is never mistaken for a code.

Also here: the transport-error wording ``fi.errors.TransportError`` uses, and
:func:`connection_error`, which turns an httpx failure into ``APIConnectionError`` /
``APITimeoutError``. Standard library only; httpx is never imported.
"""

from __future__ import annotations

import email.utils
import re
import time
from typing import Any, Mapping, Optional

from fi import errors as e

_CODE = re.compile(r"^(?:[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*|[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)$")
_MAX_MESSAGE = 500

CODE_CLASSES: dict[str, type[e.FutureAGIAPIError]] = {
    "LICENSE_MISSING": e.LicenseRequiredError,
    "product_not_admitted": e.ProductNotAvailableError,
    "idempotency_key_in_progress": e.IdempotencyKeyInProgressError,
    "idempotency_key_reused": e.IdempotencyKeyReusedError,
}
STATUS_CLASSES: dict[int, type[e.FutureAGIAPIError]] = {
    400: e.BadRequestError,
    401: e.AuthenticationError,
    402: e.PaymentRequiredError,
    403: e.PermissionDeniedError,
    404: e.NotFoundError,
    409: e.ConflictError,
    413: e.PayloadTooLargeError,
    422: e.UnprocessableEntityError,
    429: e.RateLimitError,
}


class WrongRegionError(e.PermissionDeniedError):
    """403 ``{"error": "wrong_region"}``: explicitly select the intended regional base.

    This does not identify a workspace's residency or authorize automatic fallback. Public as
    ``fi.errors.WrongRegionError`` (lazy re-export), so ``fi.errors`` still loads no platform module.
    """

    def get_error_code(self) -> str:
        return "WRONG_REGION"


# Same meaning as the TypeScript guidance; only the option names differ.
WRONG_REGION_GUIDANCE = (
    "The selected regional base rejected this request (wrong_region). Manually select the intended "
    "regional base: US https://api.futureagi.com or EU https://api-eu.futureagi.com using base_url / "
    "FI_BASE_URL, or explicitly configure platform_base_url / FI_PLATFORM_BASE_URL with the required "
    "platform path. The SDK does not discover residency and never probes, redirects or retries against "
    "another region."
)


def error_class_for(status: int, code: Optional[str] = None, family: Optional[str] = None) -> type[e.FutureAGIAPIError]:
    """The class for a status (and the server's code): a known code wins only inside its own
    status family; 5xx is ``ServerError``; any other 4xx without a class is the base class."""
    base = STATUS_CLASSES.get(status) or (e.ServerError if status >= 500 else e.FutureAGIAPIError)
    if code is not None:
        by_code = CODE_CLASSES.get(code)
        if base is not e.FutureAGIAPIError and by_code is not None and issubclass(by_code, base):
            return by_code
    if status == 409 and family == "sandboxes" and base is e.ConflictError and code in (None, "conflict", "http_409"):
        return e.SandboxStateError
    return base


def parse_retry_after(value: Any, now: Optional[float] = None) -> Optional[float]:
    """``Retry-After`` (seconds, or an HTTP date) in seconds; None when absent or unreadable."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value >= 0 else None
    text = str(value).strip()
    if not text:
        return None
    try:
        seconds = float(text)
    except ValueError:
        pass
    else:
        return seconds if 0 <= seconds < float("inf") else None
    try:
        at = email.utils.parsedate_to_datetime(text).timestamp()
    except (TypeError, ValueError, IndexError):
        return None
    return max(0.0, at - (time.time() if now is None else now))


def _code(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and len(value) <= 64 and _CODE.match(value) else None


def _text(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    one = re.sub(r"\s+", " ", value).strip()
    return one[:_MAX_MESSAGE] + "..." if len(one) > _MAX_MESSAGE else one


def read_error_shape(body: Any) -> dict[str, Any]:
    """The code, message, request ids and retry hint from one of the three shapes; ``{}`` otherwise."""
    if not isinstance(body, Mapping):
        return {}
    # FA may keep the structured error inside result, alongside status=False.
    if "status" in body and isinstance(body.get("result"), Mapping):
        body = {**body["result"], **body}
    nested = body.get("error") if isinstance(body.get("error"), Mapping) else {}
    code = _code(body.get("error_code")) or _code(body.get("code")) or _code(body.get("error")) or _code(nested.get("code"))
    if code is None:
        return {}
    detail = body.get("detail", nested.get("detail"))
    retry = parse_retry_after(body.get("retryAfterSeconds"))
    if retry is None and isinstance(detail, Mapping):
        retry = parse_retry_after(detail.get("retryAfterSeconds"))
    # FA's top-level detail is a sentence; the feature lives in error.detail.
    feature_detail = detail if isinstance(detail, Mapping) else nested.get("detail")
    fields = {
        "code": code,
        "feature": _text(feature_detail.get("feature")) if isinstance(feature_detail, Mapping) else None,
        "message": _text(body.get("message")) or _text(nested.get("message")),
        "hint": _text(nested.get("fix")) or _text(body.get("fix")),
        "reason": _text(body.get("reason")),
        "request_id": body.get("requestId") if isinstance(body.get("requestId"), str) else None,
        "upstream_request_id": body.get("request_id") if isinstance(body.get("request_id"), str) else None,
        "retry_after": retry,
    }
    return {k: v for k, v in fields.items() if v is not None}


def is_platform_error(body: Any) -> bool:
    """Whether a decoded body carries a Console/EE, gateway or Hub error envelope.

    OmegaEeError in the pinned platform OpenAPI accepts a nonempty string ``code``
    or legacy ``error`` (string or OmegaNestedError). Do not require today's code
    regex or a known code: a newer EE resource error must remain a NotFoundError.
    Keep the additional legacy shapes already understood by read_error_shape too.
    Call before scrubbing: a credential can coincidentally equal a code or field name.
    """
    if read_error_shape(body):
        return True
    if not isinstance(body, Mapping):
        return False
    code, error = body.get("code"), body.get("error")
    return (
        (isinstance(code, str) and bool(code))
        or isinstance(error, str)
        or (
            isinstance(error, Mapping)
            and isinstance(error.get("code"), str)
            and bool(error["code"])
            and isinstance(error.get("message"), str)
        )
    )


def _header(headers: Optional[Mapping[str, str]], name: str) -> Optional[str]:
    if headers is None:
        return None
    value = headers.get(name)
    if value is None:
        value = headers.get(name.lower())
    if value is None and not hasattr(headers, "get_list"):  # a plain dict with other casing
        for key, item in headers.items():
            if str(key).lower() == name.lower():
                return str(item)
    return value


def api_error(
    status_code: int,
    payload: Any,
    headers: Optional[Mapping[str, str]] = None,
    *,
    operation: Optional[str] = None,
    family: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    body: Any = None,
    console_unavailable_message: Optional[str] = None,
    regional: Optional[bool] = None,
) -> e.FutureAGIAPIError:
    """The :class:`~fi.errors.FutureAGIAPIError` subclass for a response, with every field read.

    Core namespaces pass the parsed body; the platform executor passes the redacted body as
    ``payload``, the scrubbed but unredacted one as ``body`` (the shape is read from it: a field
    named ``code`` is secret-looking to the redactor), and its ``operation`` (which also words the
    message: ``runs.get failed with status 404 (not_found)``). The platform executor also passes
    ``regional``, read from the exact envelope before privacy scrubbing could rewrite it."""
    status = int(status_code)
    source = payload if body is None else body
    # Only the frozen top-level string envelope at 403 is regional authority. Nested codes,
    # result envelopes and other statuses keep ordinary semantics; an explicit False never promotes.
    exact = isinstance(source, Mapping) and source.get("error") == "wrong_region"
    if status == 403 and (exact if regional is None else regional):
        # Nothing response-supplied (prose, destinations, request/receipt IDs, Retry-After) is kept.
        return WrongRegionError(status, {"error": "wrong_region"}, code="wrong_region", message=WRONG_REGION_GUIDANCE,
                                idempotency_key=idempotency_key, operation=operation)
    shape = read_error_shape(source)
    code = shape.get("code")
    cls = error_class_for(status, code, family)
    retry = parse_retry_after(_header(headers, "Retry-After"))
    if retry is None:
        retry = shape.get("retry_after")
    request_id = shape.get("request_id") or _header(headers, "X-Request-Id")
    message = None
    if operation is not None:
        said = shape.get("message") or shape.get("reason")
        message = f"{operation} failed with status {status} ({code or f'http_{status}'})" + (
            f": {said}" if said else ""
        )
        if shape.get("hint"):
            message += f". {shape['hint']}"
    if cls is e.LicenseRequiredError:
        subject = f"Feature '{shape['feature']}'" if shape.get("feature") else "This feature"
        message = (f"{operation} failed with status 402: " if operation else "") + (
            f"{subject} needs an Enterprise licence on this server (LICENSE_MISSING). "
            "Ask the server administrator to configure a licence that includes this feature."
        )
    # Only the Console executor can establish that the raw response lacks its envelope.
    if status == 404 and console_unavailable_message is not None:
        cls = e.ConsoleUnavailableError
        message = console_unavailable_message
    return cls(
        status,
        payload,
        retry_after=retry,
        request_id=request_id,
        code=code,
        message=message,
        idempotency_key=idempotency_key,
        operation=operation,
        upstream_request_id=shape.get("upstream_request_id") or _header(headers, "X-Upstream-Request-Id"),
        receipt_id=_header(headers, "X-Omega-Receipt-Id"),
    )


def transport_failure_kind(exc: BaseException) -> str:
    """``"connect"``, ``"timeout"`` or ``"connection"`` for a transport error, read from its class
    names (httpx is not imported here)."""
    names = {klass.__name__ for klass in type(exc).__mro__}
    if names & {"ConnectError", "ConnectTimeout", "ConnectionRefusedError", "gaierror"}:
        return "connect"  # nothing was sent
    if names & {"TimeoutException", "TimeoutError"}:
        return "timeout"  # ReadTimeout, WriteTimeout, PoolTimeout: connected, no answer in time
    if names & {"NetworkError", "ProtocolError", "ConnectionResetError", "BrokenPipeError"}:
        return "connection"  # ReadError, WriteError, RemoteProtocolError, a reset
    return "connect"


def setting_for(exc: BaseException) -> str:
    """The setting that names the server a failed request went to."""
    try:
        path = str(exc.request.url.path)  # type: ignore[attr-defined]
    except Exception:
        path = ""
    from fi._credentials import BASE_URL_ENV, PLATFORM_BASE_URL_ENV, PLATFORM_PATH

    if path.startswith(PLATFORM_PATH):
        return f"{PLATFORM_BASE_URL_ENV} (or {BASE_URL_ENV}, which it derives from)"
    return BASE_URL_ENV


def describe_transport_error(exc: BaseException, base_url: Optional[str] = None) -> tuple[str, str]:
    """``(origin, reason)`` for a connection error: the request's ``scheme://host:port`` when the
    exception carries one (httpx does), else ``base_url``, else ``"the server"``."""
    url = base_url
    if url is None:
        try:
            req_url = exc.request.url  # type: ignore[attr-defined]
            url = f"{req_url.scheme}://{req_url.netloc.decode('ascii', 'replace')}"
        except Exception:
            url = "the server"
    reason = str(exc).strip() or type(exc).__name__
    return str(url).rstrip("/"), reason


def transport_error(cls: type, exc: BaseException, base_url: Optional[str], setting: Optional[str]) -> Any:
    """``TransportError.from_exception``'s body: one line naming the server, why, and what to check."""
    url, reason = describe_transport_error(exc, base_url)
    kind = transport_failure_kind(exc)
    if kind == "timeout":
        message = f"{url} did not answer in time ({reason}); the server may be busy, retry later"
    elif kind == "connection":
        message = f"the connection to {url} broke before a response ({reason}); retry"
    else:
        message = f"cannot reach {url} ({reason}); check {setting or setting_for(exc)}"
    err = cls(message, exc)
    err.base_url = url
    err.reason = reason
    err.kind = kind
    return err


def connection_error(
    exc: BaseException,
    *,
    operation: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    base_url: Optional[str] = None,
    setting: Optional[str] = None,
    classes: tuple[type[e.APIConnectionError], type[e.APITimeoutError]] = (e.APIConnectionError, e.APITimeoutError),
) -> e.APIConnectionError:
    """An httpx failure (after the transport's retries) as ``APITimeoutError`` (any timeout,
    including a connect timeout) or ``APIConnectionError``. ``possibly_applied`` is false only when
    nothing was sent (refused, DNS, a connect timeout). ``classes`` swaps in subclasses (the core
    namespaces' hybrids in ``fi._core.core_http``)."""
    kind = transport_failure_kind(exc)
    timed_out = bool({k.__name__ for k in type(exc).__mro__} & {"TimeoutException", "TimeoutError"})
    cls = classes[1] if timed_out else classes[0]
    err = cls.from_exception(exc, base_url, setting=setting)
    assert isinstance(err, e.APIConnectionError)
    err.possibly_applied = kind != "connect"
    err.idempotency_key = idempotency_key
    err.operation = operation
    if operation:
        err.custom_message = f"{operation}: {err.custom_message}"
        err.args = (err.custom_message,)
    return err
