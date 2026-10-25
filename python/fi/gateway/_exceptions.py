"""Exception hierarchy for the AgentCC SDK."""

from __future__ import annotations

from typing import Any


class AgentCCError(Exception):
    """Base exception for all AgentCC SDK errors."""

    message: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


# --- Connection errors ---


class APIConnectionError(AgentCCError):
    """Network-level errors: DNS failures, connection refused, etc."""

    request: Any  # httpx.Request | None

    def __init__(self, message: str, *, request: Any = None) -> None:
        super().__init__(message)
        self.request = request


class APITimeoutError(APIConnectionError):
    """Request timed out."""

    def __init__(self, message: str = "Request timed out", *, request: Any = None) -> None:
        super().__init__(message, request=request)


# --- HTTP status errors ---


class APIStatusError(AgentCCError):
    """Base for HTTP errors (non-2xx responses, excluding 246)."""

    status_code: int
    type: str | None
    code: str | None
    param: str | None
    response: Any  # httpx.Response
    body: dict[str, Any] | None
    request_id: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        type: str | None = None,
        code: str | None = None,
        param: str | None = None,
        response: Any = None,
        body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.type = type
        self.code = code
        self.param = param
        self.response = response
        self.body = body
        self.request_id = request_id

    def __str__(self) -> str:
        return f"Error code: {self.status_code} - {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"

    @classmethod
    def from_response(cls, response: Any) -> APIStatusError:
        """Parse an httpx.Response and return the correct exception subclass."""
        status_code: int = response.status_code
        body: dict[str, Any] | None = None
        error_data: dict[str, Any] = {}

        try:
            body = response.json()
            error_data = body.get("error", {}) if isinstance(body, dict) else {}
        except Exception:
            pass

        message = error_data.get("message") or f"HTTP {status_code}"
        error_type = error_data.get("type")
        error_code = error_data.get("code")
        error_param = error_data.get("param")
        request_id = response.headers.get("x-agentcc-request-id") if hasattr(response, "headers") else None

        # Special case: guardrail warning (246)
        if status_code == 246:
            return GuardrailWarning._from_response(
                message=message,
                response=response,
                body=body,
                request_id=request_id,
                error_type=error_type,
                error_code=error_code,
                error_param=error_param,
            )

        # Look up exception class
        exc_cls = _STATUS_CODE_MAP.get(status_code, APIStatusError)

        exc = exc_cls(
            message=message,
            status_code=status_code,
            type=error_type,
            code=error_code,
            param=error_param,
            response=response,
            body=body,
            request_id=request_id,
        )

        # Extra fields for specific exception types
        if isinstance(exc, RateLimitError) and hasattr(response, "headers"):
            exc._parse_ratelimit_headers(response.headers)

        if isinstance(exc, (GuardrailBlockedError,)) and hasattr(response, "headers"):
            exc._parse_guardrail_headers(response.headers)

        return exc


# --- 4xx errors ---


class BadRequestError(APIStatusError):
    """400 — Invalid parameters, missing model, bad JSON."""


class AuthenticationError(APIStatusError):
    """401 — Invalid or missing API key."""


class PermissionDeniedError(APIStatusError):
    """403 — Insufficient permissions."""


class NotFoundError(APIStatusError):
    """404 — Model or endpoint not found."""


class UnprocessableEntityError(APIStatusError):
    """422 — Valid JSON but semantic error."""


class RateLimitError(APIStatusError):
    """429 — Rate limit or budget exceeded."""

    ratelimit_limit: int | None
    ratelimit_remaining: int | None
    ratelimit_reset: int | None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ratelimit_limit = None
        self.ratelimit_remaining = None
        self.ratelimit_reset = None

    def _parse_ratelimit_headers(self, headers: Any) -> None:
        from fi.gateway._constants import (
            HEADER_RATELIMIT_LIMIT,
            HEADER_RATELIMIT_REMAINING,
            HEADER_RATELIMIT_RESET,
        )

        def _int_or_none(val: str | None) -> int | None:
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        self.ratelimit_limit = _int_or_none(headers.get(HEADER_RATELIMIT_LIMIT))
        self.ratelimit_remaining = _int_or_none(headers.get(HEADER_RATELIMIT_REMAINING))
        self.ratelimit_reset = _int_or_none(headers.get(HEADER_RATELIMIT_RESET))


# --- 5xx errors ---


class InternalServerError(APIStatusError):
    """500 — Gateway internal error."""


class BadGatewayError(APIStatusError):
    """502 — Provider returned error."""


class ServiceUnavailableError(APIStatusError):
    """503 — All providers unavailable."""


class GatewayTimeoutError(APIStatusError):
    """504 — Provider timeout."""


# --- Guardrail errors ---


class GuardrailBlockedError(APIStatusError):
    """446 — Guardrail blocked the request."""

    guardrail_name: str | None
    guardrail_action: str | None
    guardrail_confidence: float | None
    guardrail_message: str | None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.guardrail_name = None
        self.guardrail_action = None
        self.guardrail_confidence = None
        self.guardrail_message = None

    def _parse_guardrail_headers(self, headers: Any) -> None:
        from fi.gateway._constants import (
            HEADER_RESPONSE_GUARDRAIL_ACTION,
            HEADER_RESPONSE_GUARDRAIL_CONFIDENCE,
            HEADER_RESPONSE_GUARDRAIL_MESSAGE,
            HEADER_RESPONSE_GUARDRAIL_NAME,
        )

        self.guardrail_name = headers.get(HEADER_RESPONSE_GUARDRAIL_NAME)
        self.guardrail_action = headers.get(HEADER_RESPONSE_GUARDRAIL_ACTION)
        self.guardrail_message = headers.get(HEADER_RESPONSE_GUARDRAIL_MESSAGE)
        raw_confidence = headers.get(HEADER_RESPONSE_GUARDRAIL_CONFIDENCE)
        if raw_confidence is not None:
            try:
                self.guardrail_confidence = float(raw_confidence)
            except (ValueError, TypeError):
                self.guardrail_confidence = None


class GuardrailWarning(APIStatusError):
    """246 — Guardrail fired with action='warn'. Request succeeded.

    The response body contains a valid completion. Access it via .completion.
    """

    guardrail_name: str | None
    guardrail_action: str | None
    guardrail_confidence: float | None
    guardrail_message: str | None
    completion: Any  # ChatCompletion once types exist; raw dict for now

    def __init__(self, **kwargs: Any) -> None:
        completion = kwargs.pop("completion", None)
        super().__init__(**kwargs)
        self.completion = completion
        self.guardrail_name = None
        self.guardrail_action = None
        self.guardrail_confidence = None
        self.guardrail_message = None

    @classmethod
    def _from_response(
        cls,
        *,
        message: str,
        response: Any,
        body: dict[str, Any] | None,
        request_id: str | None,
        error_type: str | None,
        error_code: str | None,
        error_param: str | None,
    ) -> GuardrailWarning:
        exc = cls(
            message=message,
            status_code=246,
            type=error_type,
            code=error_code,
            param=error_param,
            response=response,
            body=body,
            request_id=request_id,
            completion=body,  # Raw body dict; typed parse happens at resource layer
        )

        if hasattr(response, "headers"):
            exc._parse_guardrail_headers_warning(response.headers)

        return exc

    def _parse_guardrail_headers_warning(self, headers: Any) -> None:
        from fi.gateway._constants import (
            HEADER_RESPONSE_GUARDRAIL_ACTION,
            HEADER_RESPONSE_GUARDRAIL_CONFIDENCE,
            HEADER_RESPONSE_GUARDRAIL_MESSAGE,
            HEADER_RESPONSE_GUARDRAIL_NAME,
        )

        self.guardrail_name = headers.get(HEADER_RESPONSE_GUARDRAIL_NAME)
        self.guardrail_action = headers.get(HEADER_RESPONSE_GUARDRAIL_ACTION)
        self.guardrail_message = headers.get(HEADER_RESPONSE_GUARDRAIL_MESSAGE)
        raw_confidence = headers.get(HEADER_RESPONSE_GUARDRAIL_CONFIDENCE)
        if raw_confidence is not None:
            try:
                self.guardrail_confidence = float(raw_confidence)
            except (ValueError, TypeError):
                self.guardrail_confidence = None


# --- Streaming error ---


class StreamError(AgentCCError):
    """Error during streaming: malformed SSE, unexpected connection drop."""


# --- Status code → exception class mapping ---

_STATUS_CODE_MAP: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    446: GuardrailBlockedError,
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}
