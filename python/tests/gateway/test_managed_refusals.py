"""Managed admission tuples, typed details and conservative envelope boundaries."""
import pickle

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._retry_policy import _REFUSALS, classify_refusal
from fi.gateway._transport._base import BaseClient, RequestOptions

ROWS = [
    (403, "managed_model_unpriced", gw.PermissionDeniedError, "permission",
     "Choose a priced model or use your own provider key.",
     {"model": "provider/model-variant", "reason": "unpriced"}),
    (400, "managed_model_ambiguous", gw.BadRequestError, "generic",
     "Choose a provider-prefixed candidate ID or use the organization's own provider key for a candidate.",
     {"model": "model", "candidates": ["provider/team/model-variant", "other/model"]}),
    (400, "managed_resource_unsupported", gw.BadRequestError, "generic",
     "Use a supported managed request shape or your own provider key.", {}),
]


@pytest.mark.parametrize("status,code,cls,category,remedy,metadata", ROWS)
@pytest.mark.parametrize("native", [False, True], ids=["canonical", "messages"])
def test_managed_refusal_tuple(status, code, cls, category, remedy, metadata, native):
    metadata = {**metadata, "dispatched": True, "request_id": "provider-id", "unknown": None, "integer": 2**70}
    body = {"error": {"code": code, "type": "unrelated", "message": "unrelated prose",
                       "param": "messages[0].content", "metadata": metadata}}
    if native:
        body["type"] = "error"
    exc = gw.APIStatusError.from_response(httpx.Response(status, json=body))
    assert isinstance(exc, cls)
    assert exc.category == category and exc.remedy == remedy
    assert exc.param == "messages[0].content" and exc.metadata == metadata
    assert getattr(exc, "model", None) == metadata.get("model")
    assert getattr(exc, "candidates", None) == metadata.get("candidates")
    assert classify_refusal(status, code, metadata)[1] is False
    assert (status, code) in _REFUSALS
    # All status errors, including the new generic 400/403 rows, are safe to pickle.
    restored = pickle.loads(pickle.dumps(exc))
    assert restored.body == body and restored.response is None
    assert restored.remedy == remedy


@pytest.mark.parametrize("status,code,cls,category,remedy,metadata", ROWS)
def test_terminal_rows_override_retry_policy(status, code, cls, category, remedy, metadata):
    class Permissive:
        def get_retries_for_status(self, status):
            return 99

    client = BaseClient(api_key="fixture-only", base_url="https://gateway.test", retry_policy=Permissive())
    exc = gw.APIStatusError.from_response(httpx.Response(status, json={"error": {"code": code}},
        headers={"retry-after": "2", "x-agentcc-dispatched": "false"}))
    assert client._retry_delay(RequestOptions("POST", "/v1/test"), exc, 0, 99) is None


@pytest.mark.parametrize("metadata", [None, [], {"model": 42, "candidates": "a/b", "reason": 1},
                                       {"candidates": ["a/b", None]}, {"reason": "other"}])
def test_typed_managed_details_do_not_coerce(metadata):
    for status, code in [(403, "managed_model_unpriced"), (400, "managed_model_ambiguous")]:
        exc = gw.APIStatusError.from_response(httpx.Response(status, json={"error": {"code": code, "metadata": metadata}}))
        assert hasattr(type(exc), "model") and hasattr(type(exc), "candidates")
        assert exc.model is None and exc.candidates is None
        if code == "managed_model_unpriced":
            assert exc.reason is None
        assert exc.body["error"]["metadata"] == metadata
        assert classify_refusal(status, code, metadata)[1] is False


@pytest.mark.parametrize("status,code,cls,category,remedy,metadata", ROWS)
def test_flat_new_codes_and_wrong_status_are_not_canonical(status, code, cls, category, remedy, metadata):
    flat = gw.APIStatusError.from_response(httpx.Response(status, json={"code": code, "metadata": metadata}))
    assert flat.code is None and flat.remedy is None and flat.metadata == {}
    mismatch = gw.APIStatusError.from_response(httpx.Response(503, json={"error": {"code": code}}))
    assert mismatch.remedy is None and classify_refusal(503, code)[1] is False


def test_legacy_codes_are_distinct_from_managed_rows():
    assert len(_REFUSALS) == 52
    assert _REFUSALS[403, "permission_denied"].remedy != _REFUSALS[403, "managed_model_unpriced"].remedy
    assert _REFUSALS[400, "model_ambiguous"].remedy != _REFUSALS[400, "managed_model_ambiguous"].remedy
