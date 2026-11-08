"""B3/D6 composition controls: local responses only; never a service probe."""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest

import fi
from fi import errors

API_KEY = "composition-api-key"
SECRET_KEY = "composition-secret-key"


def client_for(monkeypatch, asynchronous, answer):
    monkeypatch.delenv("FI_PLATFORM_BASE_URL", raising=False)
    cls = fi.AsyncFutureAGIClient if asynchronous else fi.FutureAGIClient
    client = cls(api_key=API_KEY, secret_key=SECRET_KEY, base_url="https://api.futureagi.com", retries=2)
    calls = []

    def handler(request):
        calls.append(request)
        return answer()

    mock = httpx.MockTransport(handler)
    client._platform.shared._recorder._inner = mock
    client._platform.shared._recorder._inner_async = mock
    return client, calls


def invoke(client, asynchronous):
    result = client.agents.get("missing-id")
    return asyncio.run(result) if asynchronous else result


def close(client, asynchronous):
    if asynchronous:
        asyncio.run(client.aclose())
    else:
        client.close()


def envelope(code, shape):
    error = {"code": code, "message": f"denied {SECRET_KEY}",
             "detail": {"feature": f"error_feed {API_KEY}", "api_key": SECRET_KEY}}
    if shape == "nested":
        return {"detail": "denied", "error": error}
    if shape == "result":
        return {"status": False, "result": {"error": error}}
    return error


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("shape", ["top", "nested", "result"])
@pytest.mark.parametrize("status,code,expected", [
    (402, "LICENSE_MISSING", errors.LicenseRequiredError),
    (402, "ENTITLEMENT_DENIED", errors.PaymentRequiredError),
    (402, "product_not_admitted", errors.PaymentRequiredError),
    (404, "LICENSE_MISSING", errors.NotFoundError),
    (404, "product_not_admitted", errors.ProductNotAvailableError),
    (410, "LICENSE_MISSING", errors.FutureAGIAPIError),
])
def test_console_envelopes_keep_status_family_and_scrub_features(monkeypatch, asynchronous, shape, status, code, expected):
    client, calls = client_for(monkeypatch, asynchronous, lambda: httpx.Response(
        status, json=envelope(code, shape), headers={"x-request-id": "composition-request"}))
    try:
        with pytest.raises(errors.FutureAGIAPIError) as caught:
            invoke(client, asynchronous)
        error = caught.value
        assert type(error) is expected
        assert error.status_code == status and error.code == code
        assert error.request_id == "composition-request"
        assert error.__cause__ is None and error.__context__ is None
        assert "Console API is not available" not in str(error)
        for text in (str(error), repr(error), json.dumps(error.payload), json.dumps(error.to_dict())):
            assert API_KEY not in text and SECRET_KEY not in text
        if expected is errors.LicenseRequiredError:
            assert isinstance(error, errors.PaymentRequiredError)
            assert "error_feed" in str(error) and "Enterprise licence on this server" in str(error)
            assert "hosted" not in str(error).lower()
        else:
            assert "Enterprise licence on this server" not in str(error)
        assert len(calls) == 1  # no preflight or retry, even with a nonzero retry budget
    finally:
        close(client, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_availability_diagnosis_does_not_stick_to_later_license_responses(monkeypatch, asynchronous):
    responses = iter([
        httpx.Response(404, content=f"<html>{SECRET_KEY}</html>", headers={"x-request-id": API_KEY}),
        httpx.Response(402, json=envelope("LICENSE_MISSING", "nested")),
        httpx.Response(404, json=envelope("LICENSE_MISSING", "result")),
        httpx.Response(402, json={"code": "ENTITLEMENT_DENIED"}),
    ])
    client, calls = client_for(monkeypatch, asynchronous, lambda: next(responses))
    try:
        for count, expected in enumerate((errors.ConsoleUnavailableError, errors.LicenseRequiredError,
                                          errors.NotFoundError, errors.PaymentRequiredError), start=1):
            with pytest.raises(errors.FutureAGIAPIError) as caught:
                invoke(client, asynchronous)
            assert type(caught.value) is expected
            rendered = str(caught.value) + json.dumps(caught.value.to_dict())
            assert API_KEY not in rendered and SECRET_KEY not in rendered and "<html>" not in rendered
            assert ("Console API is not available" in rendered) == (expected is errors.ConsoleUnavailableError)
            assert len(calls) == count
    finally:
        close(client, asynchronous)


@pytest.mark.parametrize("status,expected", [(402, errors.LicenseRequiredError), (404, errors.NotFoundError)])
def test_core_mapping_requires_console_executor_evidence(status, expected):
    body = {"code": "LICENSE_MISSING", "detail": {"feature": "error_feed"}}
    error = errors.api_error(status, body)
    assert type(error) is expected and error.payload is body
    assert error.code == "LICENSE_MISSING"
    assert type(errors.api_error(402, body, console_unavailable_message="must not replace a 402")) is errors.LicenseRequiredError


def test_both_donor_error_exports_remain_identical():
    for name in ("PaymentRequiredError", "LicenseRequiredError", "ConsoleUnavailableError"):
        assert name in fi.__all__ and name in errors.__all__
        assert getattr(fi, name) is getattr(errors, name)
        assert name in errors.__doc__
    assert issubclass(fi.LicenseRequiredError, fi.PaymentRequiredError)
    assert issubclass(fi.ConsoleUnavailableError, errors.NotFoundError)
