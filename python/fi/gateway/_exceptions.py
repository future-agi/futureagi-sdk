"""Gateway exceptions, retaining the released hierarchy and SDKException ancestry."""

from __future__ import annotations

from typing import Any

from fi._sdk_exception import SDKException
from fi.gateway._refusal_details import _MetadataDetails, _RefusalDetails
from fi.gateway._gateway_evidence import GatewayEvidence, _EvidenceDetails, capture_gateway_evidence

class AgentCCError(SDKException):
    """Base exception for all gateway SDK errors."""

    message: str
    dispatched = _EvidenceDetails.dispatched
    gateway_request_id = _EvidenceDetails.gateway_request_id
    client_request_id = _EvidenceDetails.client_request_id

    def __init__(self, message: str) -> None:
        # Preserve Exception.args and implicit exception context.
        Exception.__init__(self, message)
        self.message = message
        self.gateway_evidence = GatewayEvidence()

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"

    def get_message(self) -> str:
        return self.message

class APIConnectionError(AgentCCError):
    """Network errors; ``request_not_sent`` is True only with pre-send proof."""
    request_not_sent: bool = False
    # Transport translation may preserve the public class without permitting replay.
    _retryable: bool = True
    _status_error: APIStatusError | None = None

    def __init__(
        self, message: str, *, request: Any = None,
        gateway_evidence: GatewayEvidence | None = None,
    ) -> None:
        super().__init__(message)
        self.request = request
        if gateway_evidence is not None:
            self.gateway_evidence = gateway_evidence

class APITimeoutError(APIConnectionError):
    def __init__(
        self, message: str = "Request timed out", *, request: Any = None,
        gateway_evidence: GatewayEvidence | None = None,
    ) -> None:
        super().__init__(message, request=request, gateway_evidence=gateway_evidence)

class APIStatusError(AgentCCError):
    """HTTP error, preserving the decoded body even when it is not an object."""

    # Reuse descriptors without changing the released exception MRO or stored state.
    required_usd = _MetadataDetails.required_usd
    available_usd = _MetadataDetails.available_usd
    limit_source = _MetadataDetails.limit_source
    remedy_hint = _MetadataDetails.remedy_hint
    scope = _MetadataDetails.scope
    resets_at = _MetadataDetails.resets_at
    reason = _MetadataDetails.reason
    cap_scope = _MetadataDetails.cap_scope
    cap_ref = _MetadataDetails.cap_ref
    cap_kind = _MetadataDetails.cap_kind
    policy_revision = _MetadataDetails.policy_revision
    suggestions = _MetadataDetails.suggestions
    model_alias_requested = _MetadataDetails.model_alias_requested
    model = _MetadataDetails.model
    candidates = _MetadataDetails.candidates
    __reduce__ = _RefusalDetails.__reduce__

    @property
    def metadata(self) -> dict[str, Any]:
        """Gateway metadata as a new dict; empty when absent or malformed."""
        return _error_metadata(self.body)

    def __init__(
        self, message: str, *, status_code: int, type: str | None = None,
        code: str | None = None, param: str | None = None, response: Any = None,
        body: Any = None, request_id: str | None = None,
        gateway_evidence: GatewayEvidence | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.type = type
        self.code = code
        self.param = param
        self.response = response
        self.body = body
        self.gateway_evidence = gateway_evidence if gateway_evidence is not None else capture_gateway_evidence(response)
        # Explicit constructor IDs remain supported; wire IDs are validated only.
        self.request_id = self.gateway_request_id if response is not None else request_id

    @property
    def category(self) -> str:
        """Canonical refusal category; unknown or mismatched pairs are ``generic``."""
        from fi.gateway._retry_policy import refusal_guidance

        return refusal_guidance(self.status_code, self.code)[0]

    @property
    def remedy(self) -> str | None:
        """Canonical corrective action, or ``None`` when no action is prescribed."""
        from fi.gateway._retry_policy import (
            _UNKNOWN_DISPATCH_REMEDY, no_code_outcome_unknown, refusal_guidance,
        )

        if no_code_outcome_unknown(self.status_code, self.code, self.gateway_evidence):
            return _UNKNOWN_DISPATCH_REMEDY
        return refusal_guidance(self.status_code, self.code, getattr(self, "metadata", None))[1]

    def __str__(self) -> str:
        from fi.gateway._retry_policy import _REFUSALS, _UNKNOWN_DISPATCH_REMEDY

        text = f"Error code: {self.status_code} - {self.message}"
        canonical = isinstance(self.code, str) and (self.status_code, self.code) in _REFUSALS
        if (not canonical and self.gateway_evidence._request_id_present is True
                and self.dispatched == "unknown"):
            text += " " + _UNKNOWN_DISPATCH_REMEDY
        return text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"

    @classmethod
    def from_response(cls, response: Any) -> APIStatusError:
        status_code: int = response.status_code
        evidence = capture_gateway_evidence(response)
        body: Any = None
        error_data: dict[str, Any] = {}
        try:
            body = response.json()
            if isinstance(body, dict):
                from fi.gateway._retry_policy import _FLAT_CODES

                flat_code = body.get("code")
                flat = "error" not in body and isinstance(flat_code, str) and flat_code in _FLAT_CODES
                raw = body if flat else body.get("error", {})
                error_data = raw if isinstance(raw, dict) else ({"message": str(raw)} if raw else {})
        except Exception:
            pass
        message = error_data.get("message") or f"HTTP {status_code}"
        error_type = error_data.get("type")
        error_code = error_data.get("code")
        error_param = error_data.get("param")
        if error_code == "wrong_region":
            message = "Gateway request reached the wrong region; check the explicitly configured origin."
        request_id = evidence.gateway_request_id
        if status_code == 246:
            return GuardrailWarning._from_response(
                message=message, response=response, body=body, request_id=request_id,
                error_type=error_type, error_code=error_code, error_param=error_param,
                gateway_evidence=evidence,
            )
        # The class follows (status, error.code); see classify_refusal.
        from fi.gateway._retry_policy import classify_refusal

        exc_cls, _ = classify_refusal(status_code, error_code, _error_metadata(body))
        exc = exc_cls(
            message=message, status_code=status_code, type=error_type,
            code=error_code, param=error_param, response=response,
            body=body, request_id=request_id, gateway_evidence=evidence,
        )
        if isinstance(exc, RateLimitError) and hasattr(response, "headers"):
            exc._parse_ratelimit_headers(response.headers)
        if isinstance(exc, GuardrailBlockedError) and hasattr(response, "headers"):
            exc._parse_guardrail_headers(response.headers)
        return exc

class BadRequestError(APIStatusError):
    """400 — Invalid parameters, missing model, bad JSON."""

class AuthenticationError(APIStatusError):
    """401 — Invalid or missing API key."""

    @property
    def reason(self) -> Any:
        """The gateway's ``error.metadata.reason``, or ``None`` when absent."""
        return _error_metadata(self.body).get("reason")

class PermissionDeniedError(APIStatusError):
    """403 — Insufficient permissions."""

class FutureAGICreditsOffError(PermissionDeniedError):
    """403 — a Future AGI model was called while the organization's credits are off.

    Raised for ``error.code`` ``future_agi_credits_off``; never retried.
    Turn on Future AGI credits on the Gateway Models page, or add your own
    provider key on the Gateway Providers page.
    """

    @property
    def remedy(self) -> str:
        """The two ways to enable requests; the gateway's message is unchanged."""
        from fi.gateway._retry_policy import _CREDITS_OFF_REMEDY

        return _CREDITS_OFF_REMEDY


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
            HEADER_RATELIMIT_LIMIT, HEADER_RATELIMIT_REMAINING, HEADER_RATELIMIT_RESET,
        )

        def _int_or_none(val: str | None) -> int | None:
            try:
                return int(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        self.ratelimit_limit = _int_or_none(headers.get(HEADER_RATELIMIT_LIMIT))
        self.ratelimit_remaining = _int_or_none(headers.get(HEADER_RATELIMIT_REMAINING))
        self.ratelimit_reset = _int_or_none(headers.get(HEADER_RATELIMIT_RESET))


class InternalServerError(APIStatusError):
    """500 — Gateway internal error."""


class BadGatewayError(APIStatusError):
    """502 — Provider returned error."""


class ServiceUnavailableError(APIStatusError):
    """503 — All providers unavailable."""


class GatewayTimeoutError(APIStatusError):
    """504 — Provider timeout."""


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
            HEADER_RESPONSE_GUARDRAIL_ACTION, HEADER_RESPONSE_GUARDRAIL_CONFIDENCE,
            HEADER_RESPONSE_GUARDRAIL_MESSAGE, HEADER_RESPONSE_GUARDRAIL_NAME,
        )
        self.guardrail_name = headers.get(HEADER_RESPONSE_GUARDRAIL_NAME)
        self.guardrail_action = headers.get(HEADER_RESPONSE_GUARDRAIL_ACTION)
        self.guardrail_message = headers.get(HEADER_RESPONSE_GUARDRAIL_MESSAGE)
        raw = headers.get(HEADER_RESPONSE_GUARDRAIL_CONFIDENCE)
        if raw is not None:
            try:
                self.guardrail_confidence = float(raw)
            except (ValueError, TypeError):
                self.guardrail_confidence = None


class GuardrailWarning(APIStatusError):
    """246 — Guardrail fired with action='warn'; .completion contains the response."""

    guardrail_name: str | None
    guardrail_action: str | None
    guardrail_confidence: float | None
    guardrail_message: str | None

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
        cls, *, message: str, response: Any, body: Any, request_id: str | None,
        error_type: str | None, error_code: str | None, error_param: str | None,
        gateway_evidence: GatewayEvidence | None = None,
    ) -> GuardrailWarning:
        exc = cls(
            message=message, status_code=246, type=error_type, code=error_code,
            param=error_param, response=response, body=body,
            request_id=request_id, completion=body, gateway_evidence=gateway_evidence,
        )
        if hasattr(response, "headers"):
            exc._parse_guardrail_headers_warning(response.headers)
        return exc

    def _parse_guardrail_headers_warning(self, headers: Any) -> None:
        GuardrailBlockedError._parse_guardrail_headers(self, headers)


# --- Billing and budget refusals ---
#
# The gateway refuses a request it will not bill with the usual error body plus
# ``error.metadata``. Which class a refusal raises, and whether it is retried, is
# decided by ``classify_refusal`` (``_retry_policy.py``) from the status and
# ``error.code``.


def _error_metadata(body: Any) -> dict[str, Any]:
    """``error.metadata`` of a decoded error body as a new dict; ``{}`` if absent or not an object."""
    error = body.get("error") if isinstance(body, dict) else None
    metadata = error.get("metadata") if isinstance(error, dict) else None
    return dict(metadata) if isinstance(metadata, dict) else {}


def _rebuild_refusal(cls: type[APIStatusError], args: tuple[Any, ...], state: dict[str, Any]) -> Any:
    """Unpickle a refusal without calling ``__init__``, whose fields are keyword-only."""
    exc = cls.__new__(cls, *args)
    exc.__dict__.update(state)
    return exc


class InsufficientCreditsError(_RefusalDetails, APIStatusError):
    """402 — the managed credits cannot pay for the request.

    ``error.code`` ``managed_credits_exhausted`` (never retried) or
    ``managed_credits_insufficient`` (retried within the configured retries, after
    ``Retry-After``, only while other requests hold the credits: ``limit_source``
    ``"agentcc_in_flight"`` with ``remedy_hint`` ``"retry"``).
    """


class AgentBudgetExhaustedError(_RefusalDetails, APIStatusError):
    """402 — the agent's own budget is spent (``error.code`` ``agent_budget_exhausted``); never retried."""


class BudgetExceededError(_RefusalDetails, RateLimitError):
    """429 — a key or organisation budget is spent (``error.code`` ``budget_exceeded`` or
    ``org_budget_exceeded``); never retried.

    A RateLimitError, so ``except RateLimitError`` still catches it.
    """


class StreamError(AgentCCError):
    """Stream failure with structured gateway error fields and pickle support."""

    def __init__(
        self, message: str, *, type: str | None = None, code: str | None = None,
        param: str | None = None, body: Any = None, request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.type = type
        self.code = code
        self.param = param
        self.body = body
        self.request_id = request_id

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), self.args, dict(vars(self)))


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
