"""FA error envelopes retain the same metadata as HTTP errors, without leaking values."""
import asyncio
import json

import httpx
import pytest

from fi.errors import BadRequestError
from tests.test_fa_management import make


HEADERS = {
    "X-Request-Id": "trace-fixture-id",
    "X-Upstream-Request-Id": "upstream-fixture-id",
    "X-Omega-Receipt-Id": "receipt-fixture-id",
    "Retry-After": "9",
}


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [200, 400])
@pytest.mark.parametrize("envelope_status", [False, "error", "failed"])
@pytest.mark.parametrize("raw", [False, True])
@pytest.mark.parametrize("copy", [False, True])
def test_error_envelopes_preserve_response_metadata(asynchronous, status, envelope_status, raw, copy):
    secret = "private-value-fixture"
    body = {"credentials": {"password": secret}}
    payload = {"status": envelope_status, "result": {
        "error_code": "validation_failed", "message": "Rejected " + secret,
        "diagnostic": secret, "details": [{secret: secret}],
    }}
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.path == "/agentcc/provider-credentials/provider/rotate/"
        assert json.loads(request.content) == body
        return httpx.Response(status, json=payload, headers=HEADERS)

    client = make(handler, asynchronous)
    target = client.with_options(retries=0) if copy else client
    resource = target.gateway.provider_credentials
    if raw:
        resource = resource.with_raw_response

    async def execute():
        try:
            await resource.rotate("provider", body)
        finally:
            await client.aclose()

    with pytest.raises(BadRequestError) as caught:
        if asynchronous:
            asyncio.run(execute())
        else:
            try:
                resource.rotate("provider", body)
            finally:
                client.close()

    error = caught.value
    assert len(calls) == 1
    assert error.payload == {"status": envelope_status, "result": {
        "error_code": "validation_failed", "message": "Rejected [redacted]",
        "diagnostic": "[redacted]", "details": [{secret: "[redacted]"}],
    }}
    assert error.status_code == 400
    assert error.code == "validation_failed"
    assert error.operation == "gateway.provider_credentials.rotate"
    assert secret not in str(error)
    assert {
        "request_id": error.request_id,
        "upstream_request_id": error.upstream_request_id,
        "receipt_id": error.receipt_id,
        "retry_after": error.retry_after,
    } == {
        "request_id": HEADERS["X-Request-Id"],
        "upstream_request_id": HEADERS["X-Upstream-Request-Id"],
        "receipt_id": HEADERS["X-Omega-Receipt-Id"],
        "retry_after": 9,
    }
    assert payload["result"]["diagnostic"] == secret
