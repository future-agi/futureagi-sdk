"""Hand-written additions to `client.gateway`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

    class Datasets(DatasetsResource):
        def get_by_name(self, name: str):
            ...                                     # compose generated methods, or
            return self._t.raw("GET", "/some/path/")  # call an endpoint the catalog lacks
"""

from __future__ import annotations

from typing import Any

from .._errors import ResponseValidationError
from ..managed_credits import ManagedCreditSummary, _parse_summary
from .base import AsyncGatewayResource, GatewayResource


def _summary(data: Any) -> ManagedCreditSummary:
    try:
        return _parse_summary(data)
    except ValueError as exc:
        raise ResponseValidationError("gateway.managed_credits", exc, data) from exc


class AsyncGateway(AsyncGatewayResource):
    """`client.gateway` for `AsyncClient`: the same methods as `Gateway`, awaited."""

    async def managed_credits(self) -> ManagedCreditSummary:
        """Read the organization-scoped managed-credit summary (Owner/Admin only).

        Uses the platform API key pair and base URL, not an inference key or URL.
        Amounts are USD decimals. ``billing_available=False`` and
        ``gateway_warning`` are successful degraded states.
        ``BillingUnavailableError`` is an unavailable ledger, not a zero balance.
        Missing required fields raise ``ResponseValidationError`` in every mode.

        HTTP-idempotent GET: uses the transport's configured retries, including
        retries on 503; no idempotency key is sent.
        """
        return _summary(await self._t.raw("GET", "/agentcc/managed-credits/", unwrap=None, decode="text"))


class Gateway(GatewayResource):
    """`client.gateway`: every generated `gateway.*` method, plus the hand-written additions in this module."""

    def managed_credits(self) -> ManagedCreditSummary:
        """Read the organization-scoped managed-credit summary (Owner/Admin only).

        Uses the platform API key pair and base URL, not an inference key or URL.
        Amounts are USD decimals. ``billing_available=False`` and
        ``gateway_warning`` are successful degraded states.
        ``BillingUnavailableError`` is an unavailable ledger, not a zero balance.
        Missing required fields raise ``ResponseValidationError`` in every mode.

        HTTP-idempotent GET: uses the transport's configured retries, including
        retries on 503; no idempotency key is sent.
        """
        return _summary(self._t.raw("GET", "/agentcc/managed-credits/", unwrap=None, decode="text"))
