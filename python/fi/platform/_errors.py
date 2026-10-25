"""One error hierarchy for every resource."""

from __future__ import annotations

from typing import Any

import httpx


class FutureAGIError(Exception):
    """Base class for every error this SDK raises."""


class APIConnectionError(FutureAGIError):
    """The request never got a response (DNS, TLS, timeout, connection reset)."""


class ResponseValidationError(FutureAGIError):
    """The response did not match the API contract (raised only with `strict_responses=True`)."""

    def __init__(self, op_id: str, error: Exception, data: Any) -> None:
        super().__init__(f"{op_id}: response does not match the contract: {error}")
        self.op_id = op_id
        self.data = data


class ResponseShapeWarning(UserWarning):
    """The response did not match the contract; the raw JSON was returned instead of a model."""


class APIError(FutureAGIError):
    """The API answered with an error status.

    `type`, `code` and `detail` come from the backend's error envelope
    (`{status: false, type, code, detail, ...}`) when it is present.
    """

    status_code: int

    def __init__(self, message: str, *, response: httpx.Response, body: Any) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code
        self.body = body
        envelope = body if isinstance(body, dict) else {}
        self.type: str | None = envelope.get("type")
        self.code: str | None = envelope.get("code")
        self.detail: Any = envelope.get("detail")
        self.request_id: str | None = response.headers.get("x-request-id")


class BadRequestError(APIError): ...
class AuthenticationError(APIError): ...
class PermissionDeniedError(APIError): ...
class PaymentRequiredError(APIError): ...  # feature not on the organization's plan
class NotFoundError(APIError): ...
class ConflictError(APIError): ...
class UnprocessableEntityError(APIError): ...
class RateLimitError(APIError): ...
class InternalServerError(APIError): ...


_BY_STATUS: dict[int, type[APIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def error_from_response(response: httpx.Response) -> APIError:
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text
    message = None
    if isinstance(body, dict):
        message = body.get("message") or body.get("error") or body.get("detail")
    if not isinstance(message, str):
        message = f"HTTP {response.status_code}"
    cls = _BY_STATUS.get(response.status_code) or (InternalServerError if response.status_code >= 500 else APIError)
    return cls(f"{response.status_code} {message}", response=response, body=body)
