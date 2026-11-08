"""The public error tree: ``from fi.errors import NotFoundError``.
Every class is an ``SDKException`` (also ``FutureAGIError``); status classes derive from ``FutureAGIAPIError``:
``BadRequestError`` 400; ``AuthenticationError`` 401 / ``PermissionDeniedError`` 403 → ``WrongRegionError`` (also ``AuthError``);
``PaymentRequiredError`` 402 → ``LicenseRequiredError`` (only ``LICENSE_MISSING``); ``NotFoundError`` 404 →
``ProductNotAvailableError`` / ``ConsoleUnavailableError`` (complete Console response without an API error envelope);
``ConflictError`` 409 → ``IdempotencyKeyInProgressError`` / ``SandboxStateError``; ``PayloadTooLargeError`` 413;
``UnprocessableEntityError`` 422 → ``IdempotencyKeyReusedError``; ``RateLimitError`` 429; ``ServerError`` 5xx.
Other branches: ``AuthError`` → ``CredentialsMissingError`` → ``MissingAuthError``; ``TransportError`` → ``APIConnectionError`` → ``APITimeoutError``;
``ConfigurationError`` → ``HostNotAllowedError`` / ``MixedCredentialsError`` / ``PlatformNotConfiguredError`` / ``ConfigurationValueError``;
``UnexpectedRedirectError``; ``StreamInterruptedError``; ``MissingExtraError``. Status families are shared across namespaces.
``get_error_code()`` is stable; ``code`` is the server's machine code or ``http_<status>``. The dataset-only legacy classes
``fi.utils.errors.RateLimitError`` / ``ServerError`` subclass these while SDK-owned; ``fi.utils`` is another distribution's overwrite path.
Catch missing keys with ``fi.errors.AuthError``, not ``fi.utils.errors.MissingAuthError``. Only ``fi._sdk_exception`` is
imported at load time; HTTP 402 classes, ``WrongRegionError``, credential errors and helpers are re-exported lazily (PEP 562)."""

from __future__ import annotations

from typing import Any, Optional

from fi._sdk_exception import SDKException

FutureAGIError = SDKException
"""The root of the tree. ``SDKException`` and ``FutureAGIError`` are the same class."""


class FutureAGIAPIError(FutureAGIError):
    """The server answered with an HTTP error status (``status_code``; the parsed body is ``payload``).

    ``code`` is the server's machine code (``idempotency_key_in_progress``) or ``http_<status>``;
    ``request_id`` the server's id for the call (quote it to support); ``idempotency_key`` the key
    the call sent, when it sent one; ``retry_after`` the server's hint in seconds. On a platform
    namespace ``payload`` is the error body with secret-named fields redacted."""

    def __init__(
        self,
        status_code: int,
        payload: Any,
        *,
        retry_after: Optional[float] = None,
        request_id: Optional[str] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        operation: Optional[str] = None,
        upstream_request_id: Optional[str] = None,
        receipt_id: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.retry_after = retry_after
        self.request_id = request_id
        self.code = code or f"http_{status_code}"
        self.idempotency_key = idempotency_key
        self.operation = operation
        self.upstream_request_id = upstream_request_id
        self.receipt_id = receipt_id
        text = message or f"Future AGI API request failed with status {status_code}: {payload}"
        if request_id and request_id not in text:
            text += f" (request id {request_id})"
        super().__init__(message=text)

    @property
    def status(self) -> int:
        """The HTTP status (the same value as ``status_code``)."""
        return self.status_code

    def get_error_code(self) -> str:
        return "FUTURE_AGI_API_ERROR"

    _RECORD = (
        "status_code", "code", "request_id", "upstream_request_id", "receipt_id", "idempotency_key", "retry_after", "operation",
    )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe record for logs and ``--json`` output: never the payload or a credential."""
        fields = {name: getattr(self, name) for name in self._RECORD if getattr(self, name) is not None}
        return {"name": type(self).__name__, "error_code": self.get_error_code(), "message": str(self), **fields}


class AuthError(FutureAGIError):
    """Missing or rejected credentials: no keys could be resolved, or the server refused them."""

    def get_error_code(self) -> str:
        return "AUTH_ERROR"


class BadRequestError(FutureAGIAPIError):
    """400: the server refused the request as malformed (validation, a bad target)."""

    def get_error_code(self) -> str:
        return "BAD_REQUEST"


class AuthenticationError(FutureAGIAPIError, AuthError):
    """401: the server did not accept the keys."""

    def get_error_code(self) -> str:
        return "AUTHENTICATION_FAILED"


class PermissionDeniedError(FutureAGIAPIError, AuthError):
    """403: the keys are valid but may not do this."""

    def get_error_code(self) -> str:
        return "PERMISSION_DENIED"


class NotFoundError(FutureAGIAPIError):
    """404."""

    def get_error_code(self) -> str:
        return "NOT_FOUND"


class ConsoleUnavailableError(NotFoundError):
    """A completely read 404 without a Console API error envelope at the configured host.

    Hosted Future AGI does not support Console access through the SDK in this release.
    For self-hosted Enterprise, set ``FI_PLATFORM_BASE_URL`` to the Console API origin,
    or check the configured URL (including a saved login). Capped or interrupted bodies,
    even HTML, cannot establish unavailability. No preflight request is made; existing
    ``except NotFoundError`` still catches it."""

    def get_error_code(self) -> str:
        return "CONSOLE_UNAVAILABLE"


class ProductNotAvailableError(NotFoundError):
    """404 ``product_not_admitted``: the product is not enabled for this workspace."""

    def get_error_code(self) -> str:
        return "PRODUCT_NOT_AVAILABLE"


class ConflictError(FutureAGIAPIError):
    """409."""

    def get_error_code(self) -> str:
        return "CONFLICT"


class IdempotencyKeyInProgressError(ConflictError):
    """409 ``idempotency_key_in_progress``: the same key is still running on the server. The
    platform client waits and resends with the same key before raising this."""

    def get_error_code(self) -> str:
        return "IDEMPOTENCY_KEY_IN_PROGRESS"


class SandboxStateError(ConflictError):
    """409 for a verb the sandbox's current state does not allow."""

    def get_error_code(self) -> str:
        return "SANDBOX_STATE"


class PayloadTooLargeError(FutureAGIAPIError):
    """413, or a refusal before anything was sent (``local=True``, with ``limit_bytes``)."""

    def __init__(
        self,
        status_code: int = 413,
        payload: Any = None,
        *,
        limit_bytes: Optional[int] = None,
        local: bool = False,
        **kw: Any,
    ) -> None:
        self.limit_bytes = limit_bytes
        self.local = local
        super().__init__(status_code, payload, **kw)

    def get_error_code(self) -> str:
        return "PAYLOAD_TOO_LARGE"


class UnprocessableEntityError(FutureAGIAPIError):
    """422."""

    def get_error_code(self) -> str:
        return "UNPROCESSABLE_ENTITY"


class IdempotencyKeyReusedError(UnprocessableEntityError):
    """422 ``idempotency_key_reused``: the same key was sent earlier with a different body."""

    def get_error_code(self) -> str:
        return "IDEMPOTENCY_KEY_REUSED"


class RateLimitError(FutureAGIAPIError):
    """429 after the transport's own retries; ``retry_after`` is the server's hint in seconds."""

    def get_error_code(self) -> str:
        return "RATE_LIMITED"


class ServerError(FutureAGIAPIError):
    """A 5xx status after the transport's own retries."""

    def get_error_code(self) -> str:
        return "SERVER_ERROR"


class TransportError(FutureAGIError):
    """No HTTP response came back. ``base_url`` and ``reason`` say which server and why; ``kind``
    is ``"connect"`` (refused, DNS, connect timeout: nothing was sent), ``"timeout"`` (connected,
    but no answer in time) or ``"connection"`` (the connection broke after the request left)."""

    base_url: str = ""
    reason: str = ""
    kind: str = "connect"

    def get_error_code(self) -> str:
        return "SERVER_UNREACHABLE"

    @classmethod
    def from_exception(
        cls, exc: BaseException, base_url: Optional[str] = None, *, setting: Optional[str] = None
    ) -> "TransportError":
        """Wrap an ``httpx.TransportError`` (or any connection error) without importing httpx.

        ``setting`` names what configures the server (``FI_BASE_URL``, ``FI_PLATFORM_BASE_URL``);
        without it, a request to the platform path names both, any other names ``FI_BASE_URL``."""
        from fi._core.errors import transport_error

        return transport_error(cls, exc, base_url, setting)


class APIConnectionError(TransportError):
    """The request got no HTTP response after the transport's own retries.

    ``possibly_applied`` is true when the request may have reached the server (the connection broke
    after sending, or a timeout after connecting), so a mutation may have run; ``idempotency_key``
    is the key it sent, when it sent one, so a caller can repeat it safely."""

    possibly_applied: bool = False
    idempotency_key: Optional[str] = None
    operation: Optional[str] = None

    def get_error_code(self) -> str:
        return "SERVER_UNREACHABLE" if self.kind == "connect" else "CONNECTION_LOST"


class APITimeoutError(APIConnectionError):
    """No answer in time: the request timeout, a stream's idle timeout, or a waiter's deadline."""

    kind = "timeout"

    def get_error_code(self) -> str:
        return "TIMEOUT"


class ConfigurationError(FutureAGIError):
    """The client refused before sending anything: a bad option or argument. ``code`` says which."""

    def __init__(self, message: str, *, code: str = "invalid_option", operation: Optional[str] = None) -> None:
        self.code = code
        self.operation = operation
        super().__init__(message)

    def get_error_code(self) -> str:
        return "CONFIGURATION_ERROR"


class ConfigurationValueError(ConfigurationError, ValueError):
    """A locally invalid value, also catchable by existing ``except ValueError`` handlers."""


class HostNotAllowedError(ConfigurationError):
    """The keys would go to a platform origin outside the Future AGI zone (or over plain http to a
    host that is not loopback), from a different source than the keys. Pass
    ``allow_custom_platform_url=True`` (or set ``FI_ALLOW_CUSTOM_PLATFORM_URL=1``) to allow it."""

    def get_error_code(self) -> str:
        return "HOST_NOT_ALLOWED"


class MixedCredentialsError(ConfigurationError):
    """A self-host Bearer token (``FI_PLATFORM_TOKEN``) together with an explicit key pair: the
    client cannot tell which identity to use. Pass one or the other."""

    def get_error_code(self) -> str:
        return "MIXED_CREDENTIALS"


class PlatformNotConfiguredError(ConfigurationError):
    """The platform origin is not usable (not an absolute http(s) URL, or it carries a user name,
    a query or a fragment), or the platform namespace has no such operation."""

    def get_error_code(self) -> str:
        return "PLATFORM_NOT_CONFIGURED"


class UnexpectedRedirectError(FutureAGIError):
    """A 3xx answer. Platform calls never follow redirects, so the keys never reach another
    origin; ``target_host`` names the redirect's host (never the full URL)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        target_host: Optional[str] = None,
        request_id: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.target_host = target_host
        self.request_id = request_id
        self.operation = operation
        super().__init__(message)

    def get_error_code(self) -> str:
        return "UNEXPECTED_REDIRECT"


class StreamInterruptedError(FutureAGIError):
    """A resumable stream spent its reconnect budget. Resume from ``last_sequence``
    (``Last-Event-ID``) with a new call."""

    def __init__(self, message: str, *, last_sequence: Optional[str] = None, operation: Optional[str] = None) -> None:
        self.last_sequence = last_sequence
        self.operation = operation
        super().__init__(message)

    def get_error_code(self) -> str:
        return "STREAM_INTERRUPTED"


class MissingExtraError(FutureAGIError):
    """An optional dependency is not installed. ``install_hint`` is the line that fixes it, and is
    set only with ``extra=`` (``pip install "futureagi[extra]"``). With ``module=`` alone the
    message names the module and gives no command: an import name is not a distribution name
    (``yaml`` is PyYAML, ``cv2`` is opencv-python), and guessing one invites typosquats (S2)."""

    def __init__(
        self,
        message: Optional[str] = None,
        cause: Optional[Exception] = None,
        *,
        extra: Optional[str] = None,
        module: Optional[str] = None,
        distribution: str = "futureagi",
    ) -> None:
        self.extra = extra
        self.module = module
        self.install_hint: Optional[str] = f'pip install "{distribution}[{extra}]"' if extra else None
        super().__init__(message, cause)

    def get_message(self) -> str:
        if self.install_hint:
            return f"{self.module or 'an optional dependency'} is not installed. Run: {self.install_hint}"
        if self.module:
            top = self.module.split(".")[0]
            return f"{self.module} is not installed. Install the package that provides the {top!r} module."
        return "an optional dependency is not installed."

    def get_error_code(self) -> str:
        return "MISSING_EXTRA"


_LAZY = {
    "PaymentRequiredError": "fi._license_errors",
    "LicenseRequiredError": "fi._license_errors",
    "CredentialsMissingError": "fi._credentials",
    "MissingAuthError": "fi._credentials",
    "api_error": "fi._core.errors",
    "describe_transport_error": "fi._core.errors",
    "transport_failure_kind": "fi._core.errors",
    "WrongRegionError": "fi._core.errors",
}
# fmt: off
__all__ = [  # noqa: F822 (lazy names, PEP 562); grouped as the tree is
    "FutureAGIError", "SDKException", "FutureAGIAPIError", "AuthError", "BadRequestError",
    "AuthenticationError", "PaymentRequiredError", "LicenseRequiredError",
    "PermissionDeniedError", "WrongRegionError", "NotFoundError", "ConsoleUnavailableError", "ProductNotAvailableError",
    "ConflictError", "IdempotencyKeyInProgressError", "SandboxStateError", "PayloadTooLargeError",
    "UnprocessableEntityError", "IdempotencyKeyReusedError", "RateLimitError", "ServerError",
    "TransportError", "APIConnectionError", "APITimeoutError", "ConfigurationError",
    "ConfigurationValueError", "HostNotAllowedError", "MixedCredentialsError", "PlatformNotConfiguredError",
    "UnexpectedRedirectError", "StreamInterruptedError", "MissingExtraError",
    "CredentialsMissingError", "MissingAuthError", "api_error", "describe_transport_error", "transport_failure_kind",
]
# fmt: on


def __getattr__(name: str) -> Any:
    module_name = _LAZY.get(name)
    if module_name is None:
        raise AttributeError(f"module 'fi.errors' has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY))
