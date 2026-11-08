"""Per-exception-type retry policy configuration, and the billing refusal decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
import re

from fi.gateway._constants import RETRYABLE_STATUS_CODES

from fi.gateway import _exceptions as _errors
from fi.gateway._refusal_contract import _REFUSALS, _CREDITS_OFF_REMEDY

# Only these released flat-body codes are unambiguous gateway compatibility cases.
_FLAT_CODES = frozenset({
    "managed_credits_exhausted", "managed_credits_insufficient", "agent_budget_exhausted",
    "budget_exceeded", "org_budget_exceeded", "managed_spend_velocity",
    "rate_limit_exceeded", "managed_billing_unavailable",
})
# The one refusal that may pass: credits are short only while other requests hold them.
_IN_FLIGHT = {"limit_source": "agentcc_in_flight", "remedy_hint": "retry"}
_RETRIED_IN_FLIGHT = (402, "managed_credits_insufficient")
_UNKNOWN_DISPATCH_REMEDY = (
    "The gateway did not confirm whether the request was applied; "
    "check whether it was applied before sending it again."
)


def no_code_outcome_unknown(status_code: int, code: object, headers: object) -> bool:
    """A no-code status fallback may replay only before gateway dispatch.

    Header presence, not body fields or a locally supplied request ID, establishes
    that the response reached the gateway. Only an explicit false dispatch header
    clears an ambiguous outcome; malformed or conflicting values fail closed.
    Coded refusals retain their contract-specific decisions.
    """
    if code is not None or status_code not in RETRYABLE_STATUS_CODES:
        return False
    from fi.gateway._gateway_evidence import GatewayEvidence, parse_gateway_evidence

    evidence = headers if isinstance(headers, GatewayEvidence) else parse_gateway_evidence(headers)
    return evidence._request_id_present is not False and evidence.dispatched is not False


def classify_refusal(
    status_code: int, code: object, metadata: object = None
) -> tuple[type[_errors.APIStatusError], bool | None]:
    """The exception class for an error response, and whether to retry it.

    Decides on ``(status_code, error.code)``, never ``error.type``; ``metadata`` is the
    body's ``error.metadata``. ``retry`` is ``False`` (never, whatever the retry
    settings), ``True`` (only after a positive Retry-After, within the configured
    status retry limit; 402 and 409 use the 429-equivalent limit), or ``None``
    (standard status retry). An unknown or mismatched pair keeps the
    status's class but is never retried. A missing/null code defers to status retry
    subject to the transport's no-code dispatch-header gate; an empty or malformed
    non-null code also fails closed.
    """
    entry = _REFUSALS.get((status_code, code)) if isinstance(code, str) else None
    if entry is None:
        cls = _errors._STATUS_CODE_MAP.get(status_code, _errors.APIStatusError)
        return cls, None if code is None else False
    retry = True if _is_in_flight(status_code, code, metadata) else entry.retry
    meta = metadata if isinstance(metadata, dict) else {}
    if (status_code, code) == (429, "managed_spend_velocity"):
        # A reason-bearing cap refusal must not become a replayable window refusal.
        retry = meta.get("remedy_hint") == "retry" and "reason" not in meta
    # All documented budget-state producers allow bounded backoff. The contract
    # has no persistent/transient wire flag; do not infer one from type or prose.
    return entry.exception, retry


def positive_retry_after(headers: object) -> float | None:
    """Read positive ASCII integer delta-seconds within the portable sleep range.

    Signs, fractions, exponents, dates and combined/duplicate fields cannot
    authorize a conditional refusal replay. Only HTTP SP/HTAB is outer whitespace.
    """
    if not isinstance(headers, Mapping):
        return None
    values = [value for name, value in headers.items() if name.lower() == "retry-after"]
    if len(values) != 1 or not isinstance(values[0], str):
        return None
    raw = values[0].strip(" \t")
    if re.fullmatch(r"[0-9]+", raw) is None:
        return None
    try:
        seconds = float(raw)
    except (ValueError, OverflowError):
        return None
    return seconds if math.isfinite(seconds) and 0 < seconds <= 2**31 - 1 else None


def _is_in_flight(status_code: int, code: object, metadata: object) -> bool:
    return (
        (status_code, code) == _RETRIED_IN_FLIGHT
        and isinstance(metadata, dict)
        and all(metadata.get(k) == v for k, v in _IN_FLIGHT.items())
    )


def refusal_guidance(status_code: int, code: object, metadata: object = None) -> tuple[str, str | None]:
    """Verbatim contract corrective action; unknown pairs remain generic."""
    entry = _REFUSALS.get((status_code, code)) if isinstance(code, str) else None
    if entry is None:
        return "generic", None
    return entry.category, entry.remedy


@dataclass
class RetryPolicy:
    """Per-exception-type retry configuration.

    Instead of a flat ``max_retries`` for all error types, this allows
    fine-grained control over how many retries each error category gets.

    Usage::

        from fi.gateway import RetryPolicy

        policy = RetryPolicy(RateLimitErrorRetries=5, TimeoutRetries=3)
        client = AgentCC(retry_policy=policy, api_key="sk-...", base_url="...")
    """

    RateLimitErrorRetries: int = 2
    TimeoutRetries: int = 2
    ConnectionErrorRetries: int = 2
    InternalServerErrorRetries: int = 1
    BadGatewayRetries: int = 1
    ServiceUnavailableRetries: int = 1
    GatewayTimeoutRetries: int = 1

    def get_retries_for_status(self, status_code: int) -> int:
        """Return the max retries for a given HTTP status code."""
        mapping = {
            429: self.RateLimitErrorRetries,
            500: self.InternalServerErrorRetries,
            502: self.BadGatewayRetries,
            503: self.ServiceUnavailableRetries,
            504: self.GatewayTimeoutRetries,
        }
        return mapping.get(status_code, 0)

    def get_retries_for_connection_error(self) -> int:
        """Return the max retries for connection errors."""
        return self.ConnectionErrorRetries

    def get_retries_for_timeout(self) -> int:
        """Return the max retries for timeout errors."""
        return self.TimeoutRetries
