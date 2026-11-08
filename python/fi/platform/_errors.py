"""One error hierarchy for every resource."""

from __future__ import annotations

import json
from typing import Any

import httpx

from fi.utils.errors import SDKException


class FutureAGIError(SDKException):
    """Base class for every error this SDK raises.

    It derives from the package's existing `SDKException`, so one `except` covers
    errors from both the legacy modules and `fi.Client`.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIConnectionError(FutureAGIError):
    """The request never got a response (DNS, TLS, timeout, connection reset)."""


class ResponseValidationError(FutureAGIError):
    """The response did not match the API contract.

    Generated methods raise this with ``strict_responses=True``; managed-credit
    summaries always validate required fields so missing balances cannot look like zero.
    """

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


class WrongRegionError(PermissionDeniedError):
    """The exact 403 ``{"error": "wrong_region"}`` response; correction is manual.

    The original HTTP response remains available as ``response``, as on every
    released API error. Guidance and parsed diagnostics never use its prose.
    """

    def __init__(self, *, response: httpx.Response) -> None:
        super().__init__(
            "403 The selected regional base rejected this request (wrong_region). "
            "Manually select the intended regional base: US https://api.futureagi.com or "
            "EU https://api-eu.futureagi.com using base_url / FI_BASE_URL. "
            "The SDK does not discover residency and never probes, redirects or retries against another region.",
            response=response, body={"error": "wrong_region"},
        )
        self.code = "wrong_region"
        self.request_id = None


class PaymentRequiredError(APIError): ...  # feature not on the organization's plan
class NotFoundError(APIError): ...
class ConflictError(APIError): ...
class UnprocessableEntityError(APIError): ...
class RateLimitError(APIError): ...
class InternalServerError(APIError): ...


class BillingUnavailableError(InternalServerError):
    """The managed-credit ledger could not be read; this is not a zero balance."""


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
    # Match the lane's raw envelope, not its more permissive general code parser.
    if response.status_code == 403 and isinstance(body, dict) and body.get("error") == "wrong_region":
        return WrongRegionError(response=response)
    message = None
    if isinstance(body, dict):
        message = body.get("message") or body.get("error") or body.get("detail")
        if message is not None and not isinstance(message, str):
            message = json.dumps(message, default=str)  # DRF field errors: {"field": ["..."]}
    if not isinstance(message, str):
        message = f"HTTP {response.status_code}"
    cls = _BY_STATUS.get(response.status_code) or (InternalServerError if response.status_code >= 500 else APIError)
    if response.status_code == 503 and isinstance(body, dict) and body.get("code") == "billing_unavailable":
        cls = BillingUnavailableError
    return cls(f"{response.status_code} {message}", response=response, body=body)
