"""The sandbox error tree: ``from fi.sandbox import NotFoundError``.

Every class is a :class:`SandboxError` (itself an ``fi.errors.FutureAGIError``), and each HTTP class
also subclasses the ``fi.errors`` class for its status, so an existing ``except
fi.errors.NotFoundError`` still catches a missing sandbox. By status: 401 ``AuthenticationError``,
403 ``PermissionDeniedError``, 404 ``NotFoundError``, 409 ``ConflictError`` (``detail.state``
``hibernated``: ``SandboxHibernatedError``, also ``fi.errors.SandboxStateError``; ``quota_exceeded``:
``QuotaExceededError``), 412 ``ConflictError`` (a stale network-policy ``If-Match``, code
``network_policy_revision_mismatch``, never retried), 400 / 422 / 428 ``ValidationError`` (428: no
``If-Match``), 413 ``PayloadTooLargeError`` (also a body refused before sending), 429
``RateLimitError``, 502 ``ProviderError``, 503 ``UnavailableError``, 507 ``InsufficientStorageError``
(the 5xx ones are also ``fi.errors.ServerError``), any other status ``SandboxAPIError``. No response:
``ConnectionError`` / ``ConnectionTimeoutError`` (``fi.errors.APIConnectionError``). Exec streams:
``CommandIncompleteError`` (no ``exit`` frame) and ``CommandFailedError`` (an ``error`` frame).
Refused before sending: ``ConfigurationError`` (also ``fi.errors.ConfigurationError``).

Every error carries ``status``, ``code``, ``message``, ``detail``, ``request_id`` and
``retry_after_seconds`` (from ``Retry-After`` or ``detail.retryAfterSeconds``), read from any of the
gateway, EE and Hub error shapes. No error text ever holds a key: the platform executor scrubs them
before an error is built, and nothing here reads a credential. Two transport guards keep their own
``fi.errors`` class: ``UnexpectedRedirectError`` (a 3xx is never followed, and on a sandbox call it
never names where it pointed) and the regional ``WrongRegionError`` (a 403 ``wrong_region`` with
fixed guidance).
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple, Type

from fi import errors as e

from ._state import each_detail, put_back

#: The executor's errors that become sandbox errors (anything else passes through unchanged).
CORE_ERRORS: Tuple[Type[BaseException], ...] = (
    e.FutureAGIAPIError,
    e.APIConnectionError,
    e.ConfigurationError,
    e.UnexpectedRedirectError,
)

#: Operations that only read: a transport failure on one of them never leaves work half done.
_READS = frozenset(
    {
        "sandboxes.list",
        "sandboxes.getInfo",
        "sandboxes.settings.get",
        "sandboxes.networkPolicy.get",
        "sandboxes.files.list",
        "sandboxes.files.read",
        "sandboxes.files.download",
        "sandboxes.snapshots.list",
        "sandboxes.activity.list",
    }
)


class SandboxError(e.FutureAGIError):
    """The base of every sandbox error. ``status`` is None when no HTTP answer came back."""

    code: Optional[str] = None
    detail: Any = None
    request_id: Optional[str] = None
    retry_after_seconds: Optional[float] = None
    operation: Optional[str] = None

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        detail: Any = None,
        request_id: Optional[str] = None,
        retry_after_seconds: Optional[float] = None,
        operation: Optional[str] = None,
    ) -> None:
        e.FutureAGIError.__init__(self, message)
        self.code = code
        self.detail = detail
        self.request_id = request_id
        self.retry_after_seconds = retry_after_seconds
        self.operation = operation

    @property
    def status(self) -> Optional[int]:
        """The HTTP status, or None for an error raised before or without a response."""
        return getattr(self, "status_code", None)

    @property
    def message(self) -> str:
        return str(self)

    #: What ``get_error_code()`` returns for this class.
    _error_code = "SANDBOX_ERROR"

    def get_error_code(self) -> str:
        return self._error_code


class SandboxAPIError(SandboxError, e.FutureAGIAPIError):
    """The server answered with an error status no narrower class covers."""

    def __init__(
        self, status_code: int, payload: Any = None, *, detail: Any = None, **kw: Any
    ) -> None:
        e.FutureAGIAPIError.__init__(self, status_code, payload, **kw)
        self.detail = detail
        self.retry_after_seconds = self.retry_after

    _error_code = "SANDBOX_API_ERROR"


class AuthenticationError(SandboxAPIError, e.AuthenticationError):
    """401: the server did not accept the API key pair or the Bearer token."""

    _error_code = "AUTHENTICATION_FAILED"


class PermissionDeniedError(SandboxAPIError, e.PermissionDeniedError):
    """403: the credential is valid but may not do this."""

    _error_code = "PERMISSION_DENIED"


class NotFoundError(SandboxAPIError, e.NotFoundError):
    """404: no such sandbox, file, snapshot or command in this workspace."""

    _error_code = "NOT_FOUND"


class ConflictError(SandboxAPIError, e.ConflictError):
    """409: the sandbox's state does not allow this now."""

    _error_code = "CONFLICT"


class SandboxHibernatedError(ConflictError, e.SandboxStateError):
    """409 on a hibernated sandbox. Nothing resumes it for you: call ``resume()`` first."""

    _error_code = "SANDBOX_HIBERNATED"


class QuotaExceededError(ConflictError):
    """409 ``quota_exceeded``: the workspace is at its active-sandbox limit."""

    _error_code = "QUOTA_EXCEEDED"


class ValidationError(SandboxAPIError, e.BadRequestError, e.UnprocessableEntityError):
    """400 or 422: the server refused the arguments."""

    _error_code = "VALIDATION_FAILED"


class PayloadTooLargeError(SandboxAPIError, e.PayloadTooLargeError):
    """413, or an upload or download over its limit (``local=True``, ``limit_bytes``)."""

    _error_code = "PAYLOAD_TOO_LARGE"


class RateLimitError(SandboxAPIError, e.RateLimitError):
    """429: slow down; ``retry_after_seconds`` is the server's hint."""

    _error_code = "RATE_LIMITED"


class ProviderError(SandboxAPIError, e.ServerError):
    """502: the sandbox provider failed."""

    _error_code = "PROVIDER_ERROR"


class UnavailableError(SandboxAPIError, e.ServerError):
    """503: sandboxes are unavailable right now."""

    _error_code = "UNAVAILABLE"


class InsufficientStorageError(SandboxAPIError, e.ServerError):
    """507: the host has no room for this sandbox or file."""

    _error_code = "INSUFFICIENT_STORAGE"


class ConnectionError(SandboxError, e.APIConnectionError):  # noqa: A001 (the contract's name)
    """No HTTP response came back. For a call that changes something, completion is unknown:
    ``possibly_applied`` says whether the request may have reached the server."""

    def get_error_code(self) -> str:
        return "SERVER_UNREACHABLE" if self.kind == "connect" else "CONNECTION_LOST"


class ConnectionTimeoutError(ConnectionError, e.APITimeoutError):
    """No answer in time (the request timeout, or a stream's idle timeout)."""

    def get_error_code(self) -> str:
        return "TIMEOUT"


class _CommandError(SandboxError):
    def __init__(
        self,
        message: str,
        *,
        exec_id: Optional[str] = None,
        stdout: str = "",
        stderr: str = "",
        operation: Optional[str] = "sandboxes.commands.run",
    ) -> None:
        super().__init__(message, operation=operation)
        self.exec_id = exec_id
        self.stdout = stdout
        self.stderr = stderr


class CommandIncompleteError(_CommandError):
    """The command's stream ended without an ``exit`` frame: whether it finished is unknown.
    ``stdout``/``stderr`` hold what arrived; the command is never run again for you."""

    _error_code = "COMMAND_INCOMPLETE"


class CommandFailedError(_CommandError):
    """The server sent an ``error`` frame: it failed after the command started."""

    _error_code = "COMMAND_FAILED"


class ConfigurationError(SandboxError, e.ConfigurationError):
    """Refused before anything was sent: no base URL, no credential, both credential modes, or a
    bad argument. ``code`` says which."""

    def __init__(
        self, message: str, *, code: str = "invalid_option", operation: Optional[str] = None
    ) -> None:
        e.ConfigurationError.__init__(self, message, code=code, operation=operation)

    _error_code = "CONFIGURATION_ERROR"


def _detail(payload: Any) -> Any:
    if not isinstance(payload, Mapping):
        return None
    detail = payload.get("detail")
    nested = payload.get("error")
    if detail is None and isinstance(nested, Mapping):
        detail = nested.get("detail")
    return detail


def _status_class(status: int, code: Optional[str], detail: Any) -> Type[SandboxAPIError]:
    if status == 409:
        if isinstance(detail, Mapping) and detail.get("state") == "hibernated":
            return SandboxHibernatedError
        return QuotaExceededError if code == "quota_exceeded" else ConflictError
    return {
        400: ValidationError, 422: ValidationError, 428: ValidationError, 412: ConflictError,
        401: AuthenticationError, 403: PermissionDeniedError, 404: NotFoundError,
        413: PayloadTooLargeError, 429: RateLimitError, 502: ProviderError,
        503: UnavailableError, 507: InsufficientStorageError,
    }.get(status, SandboxAPIError)


def _from_status(error: e.FutureAGIAPIError) -> SandboxAPIError:
    payload = each_detail(error.payload, put_back)
    detail = _detail(payload)
    code = None if error.code == f"http_{error.status_code}" else error.code
    cls = _status_class(error.status_code, code, detail)
    out = cls(
        error.status_code,
        payload,
        detail=detail,
        retry_after=error.retry_after,
        request_id=error.request_id or error.upstream_request_id,
        code=error.code,
        message=str(error),
        idempotency_key=error.idempotency_key,
        operation=error.operation,
        upstream_request_id=error.upstream_request_id,
        receipt_id=error.receipt_id,
    )
    if isinstance(error, e.PayloadTooLargeError):
        out.limit_bytes, out.local = error.limit_bytes, error.local
    return out


#: What to look at before repeating a call that may have run, by operation.
_CHECKS = {
    "sandboxes.create": "list the sandboxes",
    "sandboxes.snapshots.restore": "list the sandboxes",
    "sandboxes.snapshots.create": "list the snapshots",
    "sandboxes.commands.run": "look at the sandbox's files or activity",
}
#: The executor's closing advice, which is wrong when the call may have run.
_RETRY_TAILS = ("; the server may be busy, retry later", "; retry")


def _from_connection(
    error: e.APIConnectionError, operation: Optional[str], setting: Optional[str]
) -> ConnectionError:
    name = error.operation or operation
    timeout = isinstance(error, e.APITimeoutError)
    cls = ConnectionTimeoutError if timeout else ConnectionError
    text = str(error)
    if setting:  # the executor names its own setting; say what configures this path
        text = text.replace("check FI_PLATFORM_BASE_URL", f"check {setting}")
    if error.possibly_applied and name not in _READS:
        text = next((text[: -len(t)] for t in _RETRY_TAILS if text.endswith(t)), text)
        check = _CHECKS.get(name or "", "read the sandbox (or the path) again")
        text += f"; completion is unknown: {name or 'the call'} may have run, so {check} "
        text += "before repeating it"
    out = cls(text)
    for field in ("base_url", "reason", "kind", "possibly_applied", "idempotency_key"):
        setattr(out, field, getattr(error, field))
    out.operation = name
    return out


def stream_failure(operation: str, error: BaseException) -> ConnectionError:
    """A response body that stopped arriving: the idle timeout, or a dropped connection."""
    from fi._core.errors import transport_failure_kind

    timed_out = transport_failure_kind(error) == "timeout"
    what = "the connection was lost"
    if timed_out:
        what = "no data within the stream's idle timeout"
    text = f"{operation}: {what} ({type(error).__name__})"
    if operation not in _READS:
        text += "; completion is unknown"
    out = (ConnectionTimeoutError if timed_out else ConnectionError)(text)
    out.kind = "timeout" if timed_out else "connection"
    out.possibly_applied, out.operation = True, operation
    out.reason = type(error).__name__
    return out


def translate(
    error: BaseException, operation: Optional[str] = None, setting: Optional[str] = None
) -> BaseException:
    """The sandbox class for an ``fi.errors`` error raised by the platform executor; any other
    exception is returned unchanged. ``setting`` is what configures the origin on this path
    (``OMEGA_BASE_URL``, or the client's ``platform_base_url``), named in a connection error."""
    from fi._core.errors import WrongRegionError

    if isinstance(error, (SandboxError, WrongRegionError)):
        return error
    if isinstance(error, e.UnexpectedRedirectError) and error.target_host is not None:
        return e.UnexpectedRedirectError(  # the target host could be private: never named
            f"{error.operation or 'a sandbox call'}: the server answered {error.status_code} and "
            "sandbox calls never follow a redirect",
            status_code=error.status_code,
            request_id=error.request_id,
            operation=error.operation,
        )
    if isinstance(error, e.FutureAGIAPIError):
        return _from_status(error)
    if isinstance(error, e.APIConnectionError):
        return _from_connection(error, operation, setting)
    if isinstance(error, e.ConfigurationError):
        name = error.operation or operation
        return ConfigurationError(str(error), code=error.code, operation=name)
    return error


__all__ = [
    "SandboxError",
    "SandboxAPIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "SandboxHibernatedError",
    "QuotaExceededError",
    "ValidationError",
    "PayloadTooLargeError",
    "RateLimitError",
    "ProviderError",
    "UnavailableError",
    "InsufficientStorageError",
    "ConnectionError",
    "ConnectionTimeoutError",
    "CommandIncompleteError",
    "CommandFailedError",
    "ConfigurationError",
    "CORE_ERRORS",
    "stream_failure",
    "translate",
]
