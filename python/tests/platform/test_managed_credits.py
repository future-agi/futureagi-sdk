"""Managed-credit reads use the platform transport, never an inference endpoint."""

from __future__ import annotations

import asyncio
import json
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import httpx
import pytest

import fi.platform as fp
from fi.platform import _transport

BASE = "https://platform.example.test"
PATH = "/agentcc/managed-credits/"
OPTIONAL = (
    "gateway", "gateway_warning", "pending_settlement_usd", "markup_percent",
    "low_balance_threshold_usd", "last_reconciled_at",
)
REQUIRED = (
    "managed_models_available", "enabled", "granted_usd", "settled_spend_usd",
    "available_usd", "balance_exhausted", "min_topup_usd", "auto_reload",
    "billing_available", "currency",
)


def _body():
    return {
        "managed_models_available": True,
        "enabled": True,
        "granted_usd": 20,
        "settled_spend_usd": 1.234567,
        "available_usd": 12.345678,
        "balance_exhausted": False,
        "gateway": {"spent_usd": 2.345678, "held_usd": 0.000001, "available_usd": 17.654321},
        "gateway_warning": None,
        "pending_settlement_usd": 1.111111,
        "markup_percent": 12.5,
        "min_topup_usd": 5,
        "low_balance_threshold_usd": 2.000001,
        "auto_reload": {"enabled": True, "threshold_usd": 2.5, "amount_usd": 10, "disabled_reason": ""},
        "last_reconciled_at": "2026-01-01T00:00:00Z",
        "billing_available": True,
        "currency": "USD",
    }


def _export(name):
    value = getattr(fp, name, None)
    assert value is not None, f"fi.platform must export {name}"
    assert name in fp.__all__
    return value


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def read(request, monkeypatch):
    monkeypatch.setattr(_transport.time, "sleep", lambda seconds: None)

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(_transport.asyncio, "sleep", no_sleep)

    def call(body, *, status=200, retries=0, recover=False):
        seen = []

        def handler(req):
            seen.append(req)
            assert req.method == "GET"
            assert str(req.url) == BASE + PATH
            assert req.url.query == b""
            assert req.content == b""
            assert req.headers["X-Api-Key"] == "synthetic-key"
            assert req.headers["X-Secret-Key"] == "synthetic-secret"
            assert "authorization" not in req.headers
            if recover and len(seen) > 1:
                return httpx.Response(200, json={"status": True, "result": _body()})
            payload = {"status": True, "result": body} if status == 200 else body
            return httpx.Response(status, json=payload, headers={"Retry-After": "0"})

        kwargs = dict(api_key="synthetic-key", secret_key="synthetic-secret", base_url=BASE)
        if retries is not None:
            kwargs["max_retries"] = retries
        if request.param:
            async def scenario():
                async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
                    async with fp.AsyncClient(http_client=http, **kwargs) as client:
                        method = getattr(client.gateway, "managed_credits", None)
                        assert callable(method), "AsyncGateway.managed_credits must exist"
                        return await method()
            result = asyncio.run(scenario())
        else:
            with httpx.Client(transport=httpx.MockTransport(handler)) as http:
                with fp.Client(http_client=http, **kwargs) as client:
                    method = getattr(client.gateway, "managed_credits", None)
                    assert callable(method), "Gateway.managed_credits must exist"
                    result = method()
        assert seen
        return result, seen

    return call


def test_full_summary_has_exact_decimals_and_wire_fields(read):
    body = _body()
    result, seen = read(body)
    assert len(seen) == 1
    assert isinstance(result, _export("ManagedCreditSummary"))
    assert isinstance(result.gateway, _export("GatewayCredits"))
    assert isinstance(result.auto_reload, _export("AutoReload"))
    for name, value in body.items():
        if name not in ("gateway", "auto_reload"):
            expected = Decimal(str(value)) if name.endswith("_usd") or name == "markup_percent" else value
            assert getattr(result, name) == expected
            if name.endswith("_usd") or name == "markup_percent":
                assert isinstance(getattr(result, name), Decimal)
    for name, value in body["gateway"].items():
        assert getattr(result.gateway, name) == Decimal(str(value))
        assert isinstance(getattr(result.gateway, name), Decimal)
    assert result.auto_reload.enabled is True
    assert result.auto_reload.threshold_usd == Decimal("2.5")
    assert result.auto_reload.amount_usd == Decimal("10")
    assert isinstance(result.auto_reload.threshold_usd, Decimal)
    assert isinstance(result.auto_reload.amount_usd, Decimal)
    assert result.auto_reload.disabled_reason == ""
    raw = json.loads(json.dumps(body), parse_float=Decimal)
    assert result.raw == raw
    assert result.gateway.raw == raw["gateway"]
    assert result.auto_reload.raw == raw["auto_reload"]
    assert not hasattr(result, "org_id") and not hasattr(result, "as_of")
    for obj in (result, result.gateway, result.auto_reload):
        assert is_dataclass(obj)
        with pytest.raises(FrozenInstanceError):
            obj.raw = {}


def test_syncing_gateway_is_a_successful_degraded_state(read):
    body = _body()
    body.update(gateway=None, gateway_warning="syncing", pending_settlement_usd=None, markup_percent=None)
    result, _ = read(body)
    assert result.gateway is None and result.gateway_warning == "syncing"
    assert result.pending_settlement_usd is None and result.markup_percent is None
    assert result.available_usd == Decimal("12.345678")


def test_billing_unavailable_flag_is_still_a_success(read):
    body = _body()
    body["billing_available"] = False
    result, _ = read(body)
    assert result.billing_available is False
    assert result.available_usd == Decimal("12.345678")


@pytest.mark.parametrize("omit", [False, True], ids=["null", "missing"])
def test_optional_fields_stay_none(read, omit):
    body = _body()
    for name in OPTIONAL:
        if omit:
            body.pop(name)
        else:
            body[name] = None
    for name in ("threshold_usd", "amount_usd"):
        if omit:
            body["auto_reload"].pop(name)
        else:
            body["auto_reload"][name] = None
    result, _ = read(body)
    assert all(getattr(result, name) is None for name in OPTIONAL)
    assert result.auto_reload.threshold_usd is None
    assert result.auto_reload.amount_usd is None


@pytest.mark.parametrize("name", REQUIRED)
def test_missing_required_field_is_validation_error_even_in_default_mode(read, name):
    body = _body()
    body.pop(name)
    with pytest.raises(fp.ResponseValidationError):
        read(body)


@pytest.mark.parametrize("parent,name", [
    ("gateway", "spent_usd"), ("gateway", "held_usd"), ("gateway", "available_usd"),
    ("auto_reload", "enabled"), ("auto_reload", "disabled_reason"),
])
def test_missing_nested_required_field_is_validation_error(read, parent, name):
    body = _body()
    body[parent].pop(name)
    with pytest.raises(fp.ResponseValidationError):
        read(body)


@pytest.mark.parametrize("name,value", [
    ("granted_usd", None), ("available_usd", "12.345678"), ("available_usd", True),
    ("enabled", 1), ("auto_reload", None), ("gateway", []), ("gateway_warning", 1),
])
def test_invalid_fields_never_become_balances(read, name, value):
    body = _body()
    body[name] = value
    with pytest.raises(fp.ResponseValidationError):
        read(body)


@pytest.mark.parametrize("body", [None, [], "unavailable"])
def test_invalid_summary_shape_is_validation_error(read, body):
    with pytest.raises(fp.ResponseValidationError):
        read(body)


@pytest.mark.parametrize("status,code,error", [
    (503, "billing_unavailable", "BillingUnavailableError"),
    (503, "maintenance", "InternalServerError"),
    (500, "billing_unavailable", "InternalServerError"),
    (403, "permission_denied", "PermissionDeniedError"),
    (401, "not_authenticated", "AuthenticationError"),
    (401, "authentication_failed", "AuthenticationError"),
    (401, "api_key_retired", "AuthenticationError"),
    (404, "not_found", "NotFoundError"),
    (400, "invalid", "BadRequestError"),
    (400, "['Unknown field.']", "BadRequestError"),
])
def test_top_level_error_envelope_is_typed(read, status, code, error):
    cls = _export(error)
    body = {"status": False, "type": "service_error", "code": code, "detail": "Request rejected"}
    with pytest.raises(cls) as exc:
        read(body, status=status)
    assert type(exc.value) is cls
    assert exc.value.code == code and exc.value.status_code == status
    if status >= 500:
        assert isinstance(exc.value, fp.InternalServerError)


def test_nested_gateway_error_code_does_not_select_billing_error(read):
    with pytest.raises(fp.InternalServerError) as exc:
        read({"error": {"code": "billing_unavailable"}}, status=503)
    assert type(exc.value) is fp.InternalServerError


@pytest.mark.parametrize("balance", [0, -0.000001])
def test_zero_and_negative_balances_remain_successful_values(read, balance):
    body = _body()
    body.update(available_usd=balance, balance_exhausted=True)
    result, _ = read(body)
    assert result.available_usd == Decimal(str(balance)) and result.balance_exhausted is True


def test_billing_error_does_not_change_get_retry_policy(read):
    body = {"status": False, "code": "billing_unavailable", "detail": "Unavailable"}
    result, seen = read(body, status=503, retries=None, recover=True)
    assert len(seen) == 2
    assert result.available_usd == Decimal("12.345678")


def test_unknown_response_fields_are_preserved_only_in_raw(read):
    body = _body()
    body["future_field"] = {"value": 1}
    result, _ = read(body)
    assert result.raw["future_field"] == {"value": 1}
    assert not hasattr(result, "future_field")
