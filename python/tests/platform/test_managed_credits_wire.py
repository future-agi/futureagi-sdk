"""Literal JSON bodies retain decimal precision before any numeric conversion."""

from __future__ import annotations

import asyncio
from decimal import Decimal

import httpx
import pytest

import fi.platform as fp
from fi.platform import _transport
from fi.platform.managed_credits import _amount

BASE = "https://platform.example.test"
PATH = "/agentcc/managed-credits/"
WIRE = """{"status": true, "result": {
    "managed_models_available": true, "enabled": true,
    "granted_usd": AMOUNT, "settled_spend_usd": AMOUNT,
    "available_usd": AMOUNT, "balance_exhausted": false,
    "gateway": {"spent_usd": AMOUNT, "held_usd": AMOUNT, "available_usd": AMOUNT},
    "gateway_warning": null, "pending_settlement_usd": AMOUNT,
    "markup_percent": AMOUNT, "min_topup_usd": AMOUNT,
    "low_balance_threshold_usd": AMOUNT,
    "auto_reload": {"enabled": true, "threshold_usd": AMOUNT,
                    "amount_usd": AMOUNT, "disabled_reason": ""},
    "last_reconciled_at": null, "billing_available": true, "currency": "USD"
}}"""
FIELDS = {
    "summary": (
        "granted_usd", "settled_spend_usd", "available_usd",
        "pending_settlement_usd", "min_topup_usd", "low_balance_threshold_usd",
        "markup_percent",
    ),
    "gateway": ("spent_usd", "held_usd", "available_usd"),
    "auto_reload": ("threshold_usd", "amount_usd"),
}


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def wire_read(request, monkeypatch):
    monkeypatch.setattr(_transport.time, "sleep", lambda seconds: None)

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(_transport.asyncio, "sleep", no_sleep)

    def call(text, *, status=200, raw=False, attempts=1):
        seen = []

        def handler(req):
            seen.append(req)
            assert req.method == "GET"
            assert str(req.url) == BASE + PATH
            assert req.url.query == b"" and req.content == b""
            assert req.headers["X-Api-Key"] == "synthetic-key"
            assert req.headers["X-Secret-Key"] == "synthetic-secret"
            assert "authorization" not in req.headers
            return httpx.Response(status, content=text, headers={"Content-Type": "application/json"})

        kwargs = dict(api_key="synthetic-key", secret_key="synthetic-secret", base_url=BASE, max_retries=2)
        try:
            if request.param:
                async def scenario():
                    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
                        async with fp.AsyncClient(http_client=http, **kwargs) as client:
                            if raw:
                                return await client.request("GET", PATH, unwrap=None, decode="text")
                            return await client.gateway.managed_credits()

                return asyncio.run(scenario())
            with httpx.Client(transport=httpx.MockTransport(handler)) as http:
                with fp.Client(http_client=http, **kwargs) as client:
                    if raw:
                        return client.request("GET", PATH, unwrap=None, decode="text")
                    return client.gateway.managed_credits()
        finally:
            assert len(seen) == attempts

    return call


@pytest.mark.parametrize("lexeme", ["12345678901.234567", "99999999999999.999999", "5"])
def test_every_amount_preserves_the_wire_decimal(wire_read, lexeme):
    result = wire_read(WIRE.replace("AMOUNT", lexeme))
    objects = {"summary": result, "gateway": result.gateway, "auto_reload": result.auto_reload}
    amounts = {f"{group}.{name}": getattr(objects[group], name) for group, names in FIELDS.items() for name in names}
    wrong = {name: value for name, value in amounts.items() if not isinstance(value, Decimal) or value != Decimal(lexeme)}
    assert not wrong, f"wire decimal {lexeme} was changed: {wrong}"


def test_raw_dictionaries_preserve_decimal_numbers_and_unknown_fields(wire_read):
    text = WIRE.replace("AMOUNT", "12345678901.234567")
    text = text.replace('"currency": "USD"', '"currency": "USD", "future_field": [0.1234567890123456789, 5]')
    result = wire_read(text)
    for group, obj in (("summary", result), ("gateway", result.gateway), ("auto_reload", result.auto_reload)):
        for name in FIELDS[group]:
            assert isinstance(obj.raw[name], Decimal)
            assert obj.raw[name] == Decimal("12345678901.234567")
    assert result.raw["future_field"] == [Decimal("0.1234567890123456789"), 5]
    assert type(result.raw["future_field"][1]) is int
    assert result.raw["gateway"] is result.gateway.raw
    assert result.raw["auto_reload"] is result.auto_reload.raw


@pytest.mark.parametrize("name", ["granted_usd", "spent_usd", "threshold_usd", "markup_percent"])
@pytest.mark.parametrize("lexeme", ["NaN", "Infinity", "-Infinity", '"5"', "true", "false"])
def test_invalid_amount_literals_are_validation_errors(wire_read, name, lexeme):
    text = WIRE.replace("AMOUNT", "5").replace(f'"{name}": 5', f'"{name}": {lexeme}')
    with pytest.raises(fp.ResponseValidationError):
        wire_read(text)


@pytest.mark.parametrize("lexeme", ["NaN", "Infinity", "-Infinity"])
def test_non_json_constants_are_rejected_even_in_unknown_fields(wire_read, lexeme):
    text = WIRE.replace("AMOUNT", "5").replace('"currency": "USD"', f'"currency": "USD", "future_field": {lexeme}')
    with pytest.raises(fp.ResponseValidationError):
        wire_read(text)


@pytest.mark.parametrize("status", ["false", "1", "1.0", '"true"', "null"])
def test_success_envelope_requires_exactly_true(wire_read, status):
    text = WIRE.replace("AMOUNT", "5").replace('"status": true', f'"status": {status}', 1)
    with pytest.raises(fp.ResponseValidationError):
        wire_read(text)


@pytest.mark.parametrize("text", [
    "", "not json", "null", "[]", "{}", '{"status": true}',
    '{"status": true, "result": []}', '{"status": true, "result": null}',
])
def test_invalid_wire_envelope_is_validation_error(wire_read, text):
    with pytest.raises(fp.ResponseValidationError):
        wire_read(text)


def test_missing_status_is_validation_error(wire_read):
    text = WIRE.replace("AMOUNT", "5").replace('"status": true, ', "", 1)
    with pytest.raises(fp.ResponseValidationError):
        wire_read(text)


@pytest.mark.parametrize("status,code,error", [
    (503, "billing_unavailable", fp.BillingUnavailableError),
    (503, "maintenance", fp.InternalServerError),
    (500, "billing_unavailable", fp.InternalServerError),
    (400, "invalid", fp.BadRequestError),
    (401, "not_authenticated", fp.AuthenticationError),
    (403, "permission_denied", fp.PermissionDeniedError),
    (404, "not_found", fp.NotFoundError),
])
@pytest.mark.parametrize("raw", [False, True], ids=["managed-credits", "decode-text"])
def test_http_errors_are_typed_before_success_decoding(wire_read, monkeypatch, status, code, error, raw):
    def unexpected_decode(*args):
        pytest.fail("HTTP errors must be raised before success-body decoding")

    monkeypatch.setattr(_transport, "_decode", unexpected_decode)
    text = '{"status": false, "code": "' + code + '", "detail": "Request rejected"}'
    with pytest.raises(error) as exc:
        wire_read(text, status=status, raw=raw, attempts=3 if status >= 500 else 1)
    assert type(exc.value) is error
    assert exc.value.status_code == status and exc.value.code == code
    if status >= 500:
        assert isinstance(exc.value, fp.InternalServerError)


@pytest.mark.parametrize("value", [True, False, "5", 5.0, Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_amount_helper_rejects_non_decimal_and_non_finite_values(value):
    with pytest.raises(ValueError):
        _amount({"amount_usd": value}, "amount_usd")


@pytest.mark.parametrize("value", [5, Decimal("12345678901.234567")])
def test_amount_helper_accepts_exact_numbers(value):
    amount = _amount({"amount_usd": value}, "amount_usd")
    assert isinstance(amount, Decimal) and amount == Decimal(value)
