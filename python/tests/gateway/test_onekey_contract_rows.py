"""All current contract rows, across every transport; tests import on the r3 base."""

import httpx
import pytest
import fi.gateway as gw
from fi.gateway._retry_policy import _REFUSALS
from onekey_contract_oracle import (
    ROWS, R1, CONTRACT, STATUS_CLASSES, sample, response, wire,
    check_error, expected_attempts, expected_class, expected_remedy,
)
from test_onekey_unknown_refusals import invoke, settings, sleeps  # noqa: F401


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
@pytest.mark.parametrize("policy", [False, True])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
def test_contract_row_sync(row, policy, path, sleeps):
    calls = []
    metadata = sample(row["error"]["metadata"])

    def handle(request):
        calls.append(request)
        return response(row, metadata)

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with gw.AgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                invoke(client, path)
    check_error(caught.value, row, metadata)
    attempts = 1 if path == "stream" else expected_attempts(row, metadata)
    assert len(calls) == attempts
    assert sleeps == [2.0] * (attempts - 1)
    assert (row["status"], row["code"]) in _REFUSALS


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
@pytest.mark.parametrize("policy", [False, True])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
@pytest.mark.anyio
async def test_contract_row_async(row, policy, path, sleeps):
    calls = []
    metadata = sample(row["error"]["metadata"])

    def handle(request):
        calls.append(request)
        return response(row, metadata)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with gw.AsyncAgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                await invoke(client, path)
    check_error(caught.value, row, metadata)
    attempts = 1 if path == "stream" else expected_attempts(row, metadata)
    assert len(calls) == attempts
    assert sleeps == [2.0] * (attempts - 1)
    assert (row["status"], row["code"]) in _REFUSALS


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
def test_flat_body_only_admits_the_eight_r1_codes(row):
    metadata = sample(row["error"]["metadata"])
    body = wire(row, metadata)["error"]
    exc = gw.APIStatusError.from_response(httpx.Response(row["status"], json=body))
    assert exc.body == body
    if row["code"] in R1:
        assert type(exc) is expected_class(row)
        assert exc.code == row["code"]
        assert exc.remedy == expected_remedy(row)
        # The compatibility flat code is not a gateway metadata envelope.
        assert getattr(exc, "metadata", None) == {}
    else:
        assert type(exc) is STATUS_CLASSES[row["status"]]
        assert exc.code is None
        assert exc.category == "generic"
        assert exc.remedy is None


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["code"])
def test_missing_metadata_is_optional_and_guidance_is_read_only(row):
    exc = gw.APIStatusError.from_response(response(row))
    check_error(exc, row, None)
    for name in ("category", "remedy"):
        with pytest.raises(AttributeError):
            setattr(exc, name, "changed")


def test_table_matches_current_not_pending_contract():
    expected = {(row["status"], row["code"]) for row in ROWS}
    assert len(expected) == 49
    additions = {(403, "managed_model_unpriced"), (400, "managed_model_ambiguous"),
                 (400, "managed_resource_unsupported")}
    assert set(_REFUSALS) == expected | additions
    for row in CONTRACT["pending_rows"]:
        if (row["status"], row["code"]) not in expected | additions:
            exc = gw.APIStatusError.from_response(response(row))
            assert exc.category == "generic" and exc.remedy is None
