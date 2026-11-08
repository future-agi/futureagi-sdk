"""Wire-shaped managed-credit summaries with decimal USD amounts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass(frozen=True)
class GatewayCredits:
    """Gateway counters in USD, distinct from the ledger's available balance.

    ``raw`` preserves JSON fractional numbers as ``Decimal`` and integers as ``int``.
    """

    spent_usd: Decimal
    held_usd: Decimal
    available_usd: Decimal
    raw: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True)
class AutoReload:
    """Organization auto-reload settings; absent amounts remain ``None``.

    ``raw`` preserves JSON fractional numbers as ``Decimal`` and integers as ``int``.
    """

    enabled: bool
    threshold_usd: Optional[Decimal]
    amount_usd: Optional[Decimal]
    disabled_reason: str
    raw: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True)
class ManagedCreditSummary:
    """Organization-scoped ledger and gateway balances, denominated in USD.

    ``last_reconciled_at`` is the account's reconciliation time, not a response
    timestamp. ``raw`` preserves the unwrapped result, including unknown fields,
    with JSON fractional numbers as ``Decimal`` and integers as ``int``.
    ``markup_percent`` stays an exact ``Decimal`` in percent units, not USD.
    ``billing_available=False`` and ``gateway_warning`` describe successful
    degraded states; neither implies a zero balance.
    """

    managed_models_available: bool
    enabled: bool
    granted_usd: Decimal
    settled_spend_usd: Decimal
    available_usd: Decimal
    balance_exhausted: bool
    gateway: Optional[GatewayCredits]
    gateway_warning: Optional[str]
    pending_settlement_usd: Optional[Decimal]
    markup_percent: Optional[Decimal]
    min_topup_usd: Decimal
    low_balance_threshold_usd: Optional[Decimal]
    auto_reload: AutoReload
    last_reconciled_at: Optional[str]
    billing_available: bool
    currency: str
    raw: dict[str, Any] = field(repr=False, compare=False)


def _value(data: dict[str, Any], name: str, kind: type, *, optional: bool = False) -> Any:
    if name not in data:
        if optional:
            return None
        raise ValueError(f"missing required field: {name}")
    value = data[name]
    if value is None and optional:
        return None
    if not isinstance(value, kind):
        raise ValueError(f"{name} must be {kind.__name__}")
    return value


def _amount(data: dict[str, Any], name: str, *, optional: bool = False) -> Any:
    if name not in data:
        if optional:
            return None
        raise ValueError(f"missing required field: {name}")
    value = data[name]
    if value is None and optional:
        return None
    # JSON money is a number, never a boolean, quoted decimal, cents or micros.
    if type(value) not in (int, Decimal):
        raise ValueError(f"{name} must be a JSON number")
    amount = Decimal(value)
    if not amount.is_finite():
        raise ValueError(f"{name} must be finite")
    return amount


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _parse_summary(text: Any) -> ManagedCreditSummary:
    """Decode exact JSON numbers and validate the success envelope and summary."""
    if not isinstance(text, str):
        raise ValueError("managed-credit response must be JSON text")
    envelope = json.loads(text, parse_float=Decimal, parse_constant=_reject_constant)
    if not isinstance(envelope, dict) or envelope.get("status") is not True:
        raise ValueError("managed-credit response status must be true")
    data = envelope.get("result")
    if not isinstance(data, dict):
        raise ValueError("managed-credit summary must be an object")
    gateway_data = _value(data, "gateway", dict, optional=True)
    gateway = None
    if gateway_data is not None:
        gateway = GatewayCredits(
            spent_usd=_amount(gateway_data, "spent_usd"),
            held_usd=_amount(gateway_data, "held_usd"),
            available_usd=_amount(gateway_data, "available_usd"),
            raw=gateway_data,
        )
    reload_data = _value(data, "auto_reload", dict)
    auto_reload = AutoReload(
        enabled=_value(reload_data, "enabled", bool),
        threshold_usd=_amount(reload_data, "threshold_usd", optional=True),
        amount_usd=_amount(reload_data, "amount_usd", optional=True),
        disabled_reason=_value(reload_data, "disabled_reason", str),
        raw=reload_data,
    )
    currency = _value(data, "currency", str)
    if currency != "USD":
        raise ValueError("currency must be USD")
    return ManagedCreditSummary(
        managed_models_available=_value(data, "managed_models_available", bool),
        enabled=_value(data, "enabled", bool),
        granted_usd=_amount(data, "granted_usd"),
        settled_spend_usd=_amount(data, "settled_spend_usd"),
        available_usd=_amount(data, "available_usd"),
        balance_exhausted=_value(data, "balance_exhausted", bool),
        gateway=gateway,
        gateway_warning=_value(data, "gateway_warning", str, optional=True),
        pending_settlement_usd=_amount(data, "pending_settlement_usd", optional=True),
        markup_percent=_amount(data, "markup_percent", optional=True),
        min_topup_usd=_amount(data, "min_topup_usd"),
        low_balance_threshold_usd=_amount(data, "low_balance_threshold_usd", optional=True),
        auto_reload=auto_reload,
        last_reconciled_at=_value(data, "last_reconciled_at", str, optional=True),
        billing_available=_value(data, "billing_available", bool),
        currency=currency,
        raw=data,
    )
