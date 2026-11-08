"""Response redaction must not alter management warning semantics or JSON keys."""
import asyncio
import json
import warnings

import httpx
import pytest

from fi._core.fa_management import GatewayConfigWarning, GatewayConfigWarningError
from fi._core.redact import scrub_text
from fi.errors import BadRequestError
from tests.test_fa_management import make


PAIRS = [
    ("abcd", "abcd-opaque-provider-value"),
    ("abcd", "opaque-provider-value-abcd"),
    ("abcd", "opaque-abcd-provider-value"),
    ('x.*[y]\\"', 'x.*[y]\\"-opaque-provider-value'),
    ("redacted", "redacted-opaque-provider-value"),
]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("short,long", PAIRS)
@pytest.mark.parametrize("method", ["create", "update", "rotate"])
def test_overlapping_credentials_redact_whole_values_in_either_order(asynchronous, reverse, short, long, method):
    entries = [("api_key", short), ("secret_key", long)]
    body = {"credentials": dict(reversed(entries) if reverse else entries)}
    response = {"diagnostic": long + " | " + short, "details": [{"echo": long}],
                "credentials": {"api_key": long}}
    def handler(request):
        assert json.loads(request.content) == body
        return httpx.Response(200, json={"status": True, "result": response})
    client = make(handler, asynchronous)
    call = getattr(client.gateway.provider_credentials.with_raw_response, method)
    result = call(*([] if method == "create" else ["provider"]), body)
    if asynchronous:
        result = asyncio.run(result)
    assert result.data == {"diagnostic": "[redacted] | [redacted]",
                           "details": [{"echo": "[redacted]"}],
                           "credentials": {"api_key": "[REDACTED]"}}
    assert response["diagnostic"] == long + " | " + short


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("short,long", PAIRS)
def test_text_scrubbing_is_literal_single_pass_and_order_independent(reverse, short, long):
    secrets = [short, long]
    if reverse:
        secrets.reverse()
    assert scrub_text(long + " | " + short, secrets) == "[redacted] | [redacted]"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("secret", ["a", "gateway_synced", "gateway_warning", "warnings", "status", "result", "credentials", "hasWarnings"])
@pytest.mark.parametrize("trigger", ["gateway_synced", "gateway_warning", "warnings", "none"])
@pytest.mark.parametrize("source", ["body", "auth"])
def test_warning_semantics_and_keys_survive_colliding_credentials(asynchronous, secret, trigger, source):
    response = {"gateway_synced": trigger != "gateway_synced", "warnings": [], "gateway_warning": "",
                "diagnostic": secret, "details": [{"warnings": secret, "a": secret}],
                "credentials": {"api_key": secret}}
    if trigger == "warnings":
        response["warnings"] = [secret]
    if trigger == "gateway_warning":
        response["gateway_warning"] = secret
    body = {"credentials": {"api_key": secret}} if source == "body" else {}
    client = make(lambda r: httpx.Response(200, json={"status": True, "result": response}), asynchronous,
                  **({"api_key": secret} if source == "auth" else {}))
    def invoke(strict):
        result = client.gateway.provider_credentials.with_raw_response.rotate("provider", body, strict=strict)
        return asyncio.run(result) if asynchronous else result
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = invoke(False).data
    assert len(caught) == (0 if trigger == "none" else 1)
    if caught:
        assert caught[0].category is GatewayConfigWarning
        assert str(caught[0].message) == "The server saved the change with warnings; inspect the result before relying on it."
    expected = {**response, "diagnostic": "[redacted]", "details": [{"warnings": "[redacted]", "a": "[redacted]"}],
                "credentials": {"api_key": "[REDACTED]"}}
    if trigger == "warnings":
        expected["warnings"] = ["[redacted]"]
    if trigger == "gateway_warning":
        expected["gateway_warning"] = "[redacted]"
    assert value == expected
    if trigger == "none":
        assert invoke(True).data == expected
    else:
        with pytest.raises(GatewayConfigWarningError) as error:
            invoke(True)
        assert error.value.code == "gateway_config_warning"
    assert response["diagnostic"] == secret


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("secret", ["a", "status", "result", "error_code"])
def test_false_status_envelopes_remain_errors_with_colliding_auth_credentials(asynchronous, secret):
    client = make(lambda r: httpx.Response(200, json={"status": False, "result": {
        "error_code": "rejected", "message": secret}}), asynchronous, api_key=secret)
    with pytest.raises(BadRequestError):
        result = client.gateway.config.get_active()
        if asynchronous:
            asyncio.run(result)


HTTP_PAIRS = [
    ("a", "fixture-secret"), ("ab", "fixture-secret"), ("abc", "fixture-secret"),
    ("details", "fixture-secret"), ("message", "fixture-secret"),
    ("error_code", "fixture-secret"), ("redacted", "fixture-secret"),
    ("abcd", 'abcd"opaque-provider-value'),
    ("abcd", 'opaque-provider-value"abcd'),
    ("abcd", 'opaque"abcd"provider-value'),
    ("abcd", "abcd\\opaque-provider-value"),
    ("abcd", "abcd/opaque-provider-value"),
]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("short,long", HTTP_PAIRS)
@pytest.mark.parametrize("source", ["auth", "mixed"])
def test_http_errors_scrub_decoded_values_once_and_preserve_keys(asynchronous, reverse, short, long, source):
    first, second = (long, short) if reverse else (short, long)
    body = {"credentials": {"api_key": second}} if source == "mixed" else None
    response = {"status": False, "result": {"error_code": "rejected", "message": first + " | " + second,
                "diagnostic": second + " | " + first, "details": [{"details": first, "message": second}],
                "credentials": {"api_key": second}}}
    def handler(request):
        if body is not None:
            assert json.loads(request.content) == body
        # Construct a JSON Unicode escape visibly to exercise decoded redaction,
        # without hiding printable source text inside an encoded literal.
        escaped_slash = "\\" + "u" + format(ord("/"), "04x")
        return httpx.Response(400, content=json.dumps(response).replace("/", escaped_slash), headers={
            "x-request-id": "request-fixture", "x-upstream-request-id": "upstream-fixture",
            "x-omega-receipt-id": "receipt-fixture", "retry-after": "7"})
    client = make(handler, asynchronous, api_key=first,
                  secret_key=second if source == "auth" else "fixture-secret")
    with pytest.raises(BadRequestError) as caught:
        call = (client.gateway.config.with_raw_response.get_active() if body is None else
                client.gateway.provider_credentials.with_raw_response.rotate("provider", body))
        if asynchronous:
            asyncio.run(call)
    error = caught.value
    name = "gateway.config.get_active" if body is None else "gateway.provider_credentials.rotate"
    assert error.payload == {"status": False, "result": {"error_code": "rejected",
        "message": "[redacted] | [redacted]", "diagnostic": "[redacted] | [redacted]",
        "details": [{"details": "[redacted]", "message": "[redacted]"}], "credentials": "[redacted]"}}
    assert str(error) == f"{name} failed with status 400 (rejected): [redacted] | [redacted] (request id request-fixture)"
    assert error.status_code == 400
    assert error.code == "rejected"
    assert error.operation == name
    assert error.request_id == "request-fixture"
    assert error.upstream_request_id == "upstream-fixture"
    assert error.receipt_id == "receipt-fixture"
    assert error.retry_after == 7
    assert response["result"]["message"] == first + " | " + second
