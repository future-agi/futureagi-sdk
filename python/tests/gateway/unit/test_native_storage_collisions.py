"""Native fields win over payload decoys; failed masks do not prune data edges."""
import httpx
import pytest

from fi.gateway._transport import _scrub
from fi.gateway._transport._exchange_mask import mask_known_exchange

ORIGIN = "https://gateway.example.test"
KEY = "synthetic-collision-key"
MASK = "[REDACTED]"


def decoy(namespace, name, value, first):
    class AttributeName(str):
        def __hash__(self):
            return str.__hash__(self) ^ 1

    item = {AttributeName(name): value}
    return {**item, **namespace} if first else {**namespace, **item}


@pytest.mark.parametrize("first", [False, True])
@pytest.mark.parametrize("root_kind", ["request", "response", "headers"])
@pytest.mark.parametrize("direct", [False, True])
def test_exact_header_rows_win_over_wrong_hash_payload(first, root_kind, direct):
    headers = httpx.Headers({"Authorization": KEY})
    headers.__dict__ = decoy(vars(headers), "_list", list(httpx.Headers({"X-Public": "safe"})._list), first)
    root = headers
    if root_kind == "request":
        root = httpx.Request("GET", ORIGIN)
        root.headers = headers
    elif root_kind == "response":
        root = httpx.Response(200)
        root.headers = headers
    if direct:
        mask_known_exchange(root, None, frozenset())
    else:
        _scrub.scrub_reachable((root,))
    assert headers["authorization"] == MASK


@pytest.mark.parametrize("first", [False, True])
def test_exact_response_headers_keep_provenance(first):
    response = httpx.Response(200, headers={"X-Private": "gateway-value", "Set-Cookie": KEY})
    other = httpx.Headers({"X-Private": "decoy-value"})
    response.__dict__ = decoy(vars(response), "headers", other, first)
    _scrub.scrub_reachable((response,), frozenset({"x-private"}))
    assert response.headers["x-private"] == "gateway-value"
    assert response.headers["set-cookie"] == MASK


@pytest.mark.parametrize("root_kind", ["headers", "response"])
@pytest.mark.parametrize("missing", [False, True])
def test_unmaskable_storage_keeps_other_data_edges(root_kind, missing):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": KEY})
    headers = httpx.Headers({"X-Public": "safe"})
    if missing:
        del headers.__dict__["_list"]
    else:
        headers._list = tuple(headers._list)
    if root_kind == "headers":
        root = headers
        root.diagnostic = request
    else:
        root = httpx.Response(200, request=request)
        root.headers = headers
    walk = _scrub._Walk()
    walk.run((root,))
    walk.mask(frozenset())
    assert request.headers["authorization"] == MASK
    assert id(headers) not in walk.sent and id(headers) not in walk.received
    assert walk.report.inspection_errors
    assert walk.report.scanned <= _scrub.SCAN_CAP
    assert walk.report.visited <= _scrub.NODE_CAP
