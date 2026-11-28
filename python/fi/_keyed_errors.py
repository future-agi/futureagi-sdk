"""The errors a request that carries the API keys raises for a redirect and for a proxied plain-http send.

``fi.errors``, ``fi.utils.errors`` and ``fi`` export both classes; the codes are the ones futureagi 0.7.1 publishes.
"""

from __future__ import annotations

from typing import Optional

from fi.errors import ConfigurationError, FutureAGIError


class KeyedRedirectRefusedError(FutureAGIError):
    """A request that carries the API keys was answered with a redirect. Such a request is sent with
    redirects off, so the keys go to the configured host only; ``target_host`` names the redirect's host
    (not the full URL). Also exported from ``fi.utils.errors`` and ``fi``."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        target_host: Optional[str] = None,
        request_id: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.target_host = target_host
        self.request_id = request_id
        self.operation = operation
        super().__init__(message)

    def get_message(self) -> str:
        return "A request carrying the API keys was answered with a redirect; it was not followed."

    def get_error_code(self) -> str:
        return "KEYED_REDIRECT_REFUSED"


UnexpectedRedirectError = KeyedRedirectRefusedError
"""The name this line used before futureagi 0.7.1 published the class: the same class, with the same code."""


class KeyedProxyRefusedError(ConfigurationError):
    """A request that carries the API keys would be sent over plain http through a proxy, and it was not sent.
    Also a ``ConfigurationError``; its ``code`` is ``KEYED_PROXY_REFUSED``. Also exported from ``fi.utils.errors`` and ``fi``."""

    def __init__(self, message: Optional[str] = None, *, operation: Optional[str] = None) -> None:
        super().__init__(message or self.get_message(), code="KEYED_PROXY_REFUSED", operation=operation)

    def get_message(self) -> str:
        return (
            "A request carrying the API keys was not sent: the session routes it through a proxy. "
            "Use a session with trust_env=False and no proxies, or let the SDK build its own."
        )

    def get_error_code(self) -> str:
        return "KEYED_PROXY_REFUSED"


class InsecureHttpRefusedError(ConfigurationError):
    """A request that carries credentials would go over plain http to a Future AGI host, and it was not sent. No setting
    allows it. Also a ``ConfigurationError``; its ``code`` is ``INSECURE_HTTP_REFUSED``. ``host`` is the host the library
    connects to. Also exported from ``fi.utils.errors`` and ``fi``."""

    def __init__(self, host: str = "", *, message: Optional[str] = None, operation: Optional[str] = None) -> None:
        self.host = host
        super().__init__(message or self.get_message(), code="INSECURE_HTTP_REFUSED", operation=operation)

    def get_message(self) -> str:
        where = f" to {self.host}" if getattr(self, "host", "") else ""
        return f"A request carrying credentials was not sent over plain http{where}. Use https."

    def get_error_code(self) -> str:
        return "INSECURE_HTTP_REFUSED"


def plain_origin_refusal(error_class: type, message: str) -> Exception:
    """An error that is both ``error_class`` (a package's own error, built from ``message``) and a ``ConfigurationError``
    with code ``insecure_http_origin``, for a plain-http origin that is not loopback and has no opt-in."""

    class PlainOriginRefused(error_class, ConfigurationError):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            error_class.__init__(self, message)
            self.code, self.operation = "insecure_http_origin", None

        def get_error_code(self) -> str:
            return "insecure_http_origin"

    return PlainOriginRefused()
