"""Routing contract additions: terminal envelope rows, not status/type guesses."""

import httpx
import pytest
import fi.gateway as gw
from fi.gateway._retry_policy import _REFUSALS, classify_refusal
from fi.gateway._transport._base import BaseClient, RequestOptions, RetryConfig
from .onekey_contract_oracle import R3_ADDITIONS, expected_class, sample, wire

ROWS = R3_ADDITIONS["rows"]


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
def test_r3_explicit_table_entry_and_unchanged_status_class(row):
    entry = _REFUSALS.get((row["status"], row["code"]))
    assert entry is not None
    assert entry.exception is expected_class(row)
    assert entry.retry is False
    assert entry.category == "generic"
    assert entry.remedy == row["remedy"]


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
@pytest.mark.parametrize("header", [None, "2", "0", "invalid"])
def test_r3_never_retries_even_with_retry_hints_and_headers(row, header):
    metadata = {"remedy_hint": "retry", "limit_source": "agentcc_in_flight"}
    headers = {} if header is None else {"Retry-After": header}
    exc = gw.APIStatusError.from_response(
        httpx.Response(row["status"], json=wire(row, metadata), headers=headers)
    )
    assert classify_refusal(row["status"], row["code"], metadata)[1] is False
    client = BaseClient(api_key="unit-placeholder", base_url="https://gateway.example.test",
                        max_retries=5, retry_config=RetryConfig(backoff_jitter=0))
    for attempt in range(6):
        assert client._retry_delay(RequestOptions("POST", "/v1/test"), exc, attempt, 5) is None


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
@pytest.mark.parametrize("status", [429, 503, 504])
def test_r3_flat_codes_are_absent_and_wrong_status_envelopes_are_terminal(row, status):
    body = wire(row)["error"]
    flat = gw.APIStatusError.from_response(httpx.Response(status, json=body))
    wrapped = gw.APIStatusError.from_response(httpx.Response(status, json={"error": body}))
    assert flat.code is None and flat.category == "generic" and flat.remedy is None
    assert classify_refusal(status, flat.code)[1] is None
    assert wrapped.code == row["code"] and wrapped.category == "generic" and wrapped.remedy is None
    assert classify_refusal(status, wrapped.code)[1] is False
    client = BaseClient(api_key="unit-placeholder", base_url="https://gateway.example.test",
                        max_retries=1, retry_config=RetryConfig(backoff_jitter=0))
    options = RequestOptions("POST", "/v1/test")
    assert client._retry_delay(options, flat, 0, 1) is not None
    assert client._retry_delay(options, wrapped, 0, 1) is None


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
def test_r3_preserves_param_metadata_and_ignores_message_and_type(row):
    metadata = sample(row["error"]["metadata"])
    body = wire(row, metadata)
    body["error"].update(param="model", message="retry rate limit", type="rate_limit_error")
    exc = gw.APIStatusError.from_response(httpx.Response(row["status"], json=body))
    assert type(exc) is expected_class(row)
    assert exc.param == "model"
    assert exc.body == body
    assert exc.category == "generic" and exc.remedy == row["remedy"]
    assert exc.metadata == (metadata or {})
    for name, value in (metadata or {}).items():
        assert isinstance(getattr(type(exc), name, None), property)
        assert getattr(exc, name, None) == value
        with pytest.raises(AttributeError):
            setattr(exc, name, "changed")


def test_requested_alias_accessor_is_optional():
    exc = gw.APIStatusError.from_response(httpx.Response(400, json={"error": {
        "code": "omega_default_unroutable", "message": "unroutable",
    }}))
    assert isinstance(getattr(type(exc), "model_alias_requested", None), property)
    assert exc.model_alias_requested is None
