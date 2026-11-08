"""Fold-only portable parity controls. Authored, NOT_RUN; all transport is mock-only."""
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fi import errors
from fi._core.core_http import AsyncMappedClient, MappedClient
from fi._core.http_security import check_http_security

from ._h6_k2w_transport import (
    API_KEY,
    EU,
    SECRET_KEY,
    SUBMITTED,
    US,
    assert_private,
    assert_selected_only,
    close,
    invoke,
    regional_guidance,
    run,
    success,
)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("action,mode", [("core", "keys"), ("console", "keys"), ("console", "bearer")])
def test_supported_regional_errors_drop_all_response_diagnostics(wire, asynchronous, action, mode):
    wire.respond = lambda r: httpx.Response(403, json={
        "error": "wrong_region", "message": SUBMITTED, "reason": SUBMITTED,
        "fix": EU + "/untrusted", "detail": {"private": SUBMITTED},
        "code": "role_forbidden", "requestId": "synthetic-gateway-id",
        "request_id": "synthetic-upstream-id", "retryAfterSeconds": 99,
    }, headers={"x-request-id": "synthetic-header-id", "x-upstream-request-id": "synthetic-header-upstream",
                "x-omega-receipt-id": "synthetic-receipt-id", "retry-after": "99"})
    c = wire.client(asynchronous, mode, retries=0, base_url=US)
    try:
        with pytest.raises(errors.WrongRegionError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        error = caught.value
        regional_guidance(error)
        assert isinstance(error, errors.PermissionDeniedError)
        assert error.get_error_code() == "WRONG_REGION"
        assert error.payload == {"error": "wrong_region"}
        assert (error.request_id, error.upstream_request_id, error.receipt_id, error.retry_after) == (None, None, None, None)
        assert_private(error, extra=("synthetic-gateway-id", "synthetic-upstream-id", "synthetic-header-id",
                                     "synthetic-header-upstream", "synthetic-receipt-id", EU + "/untrusted"))
        assert_selected_only(wire, US, mode, 1)
        assert wire.sleeps == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("action,mode", [("core", "keys"), ("console", "keys"), ("console", "bearer")])
@pytest.mark.parametrize("status,kind", [(401, errors.AuthenticationError), (503, errors.ServerError)])
def test_supported_non_403_keeps_ordinary_status(wire, asynchronous, action, mode, status, kind):
    wire.respond = lambda r: httpx.Response(status, json={"error": "wrong_region"})
    c = wire.client(asynchronous, mode, retries=0, base_url=EU)
    try:
        with pytest.raises(kind) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        assert type(caught.value) is kind
        assert US not in str(caught.value) and EU not in str(caught.value)
        assert_selected_only(wire, EU, mode, 1)
        assert wire.sleeps == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("base", [US, EU])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
@pytest.mark.parametrize("recovers", [False, True])
def test_supported_503_retries_only_the_selected_origin(wire, asynchronous, base, mode, recovers):
    wire.respond = lambda r: (success(r) if recovers and len(wire.requests) > 1 else
                              httpx.Response(503, json={"error": "omega_service_unavailable"}))
    c = wire.client(asynchronous, mode, retries=2, base_url=base)
    try:
        if recovers:
            run(asynchronous, lambda: c.environments.list())
        else:
            with pytest.raises(errors.ServerError):
                run(asynchronous, lambda: c.environments.list())
        count = 2 if recovers else 3
        assert_selected_only(wire, base, mode, count)
        assert len(wire.sleeps) == count - 1
        assert len({str(r.url) for r in wire.requests}) == 1
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_privacy_scrubber_cannot_promote_a_nonregional_wire_body(wire, asynchronous):
    wire.respond = lambda r: httpx.Response(403, json={"error": {"code": "wrong_region"}})
    c = wire.client(asynchronous, retries=0, base_url=US)
    c._platform.shared.error_scrubber = lambda value, secrets: {"error": "wrong_region"}
    try:
        with pytest.raises(errors.PermissionDeniedError) as caught:
            run(asynchronous, lambda: c.environments.list())
        assert type(caught.value) is errors.PermissionDeniedError
        assert US not in str(caught.value) and EU not in str(caught.value)
        assert_selected_only(wire, US, "keys", 1)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("body,parsed,kind", [
    (b'{"error":"wrong_region"}', {"err": "[redacted]"}, errors.WrongRegionError),
    (b'{"error":{"code":"wrong_region"}}', {"error": "wrong_region"}, errors.PermissionDeniedError),
])
def test_generated_model_conversion_cannot_change_core_wire_authority(body, parsed, kind):
    from fi.futureagi_client import _status_error

    response = SimpleNamespace(status_code=403, content=body, parsed=parsed, headers={})
    error = _status_error(response)
    assert type(error) is kind
    if kind is errors.WrongRegionError:
        regional_guidance(error)
        assert error.payload == {"error": "wrong_region"}
    else:
        assert US not in str(error) and EU not in str(error)


@pytest.mark.parametrize("first_mode", ["keys", "bearer"])
def test_canonical_warning_is_shared_between_credential_modes(capsys, first_mode):
    host = "fold-parity-" + uuid4().hex + ".invalid"
    other_mode = "bearer" if first_mode == "keys" else "keys"
    check_http_security(httpx.URL(f"http://{host}/private-path/a"), first_mode, allow_insecure_http=True)
    check_http_security(httpx.URL(f"http://{host.upper()}.:80/private-path/b"), other_mode, allow_insecure_http=True)
    texts = capsys.readouterr().err.splitlines()
    assert len(texts) == 1
    assert "cleartext" in texts[0] and "deprecated" in texts[0] and "future" in texts[0]
    assert "private-path" not in texts[0]


@pytest.mark.parametrize("asynchronous", [False, True])
def test_ipv4_mapped_ipv6_is_not_the_ipv6_loopback_exception(wire, asynchronous):
    c = wire.client(asynchronous, "bearer", retries=0, base_url="http://[::ffff:127.0.0.1]:19876")
    try:
        with pytest.raises(errors.ConfigurationError) as caught:
            run(asynchronous, lambda: c.environments.list())
        assert caught.value.code == "insecure_http_origin"
        assert wire.requests == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_shared_python_client_cannot_enable_redirect_following(wire, asynchronous, status):
    wire.respond = lambda r: httpx.Response(status, headers={"location": EU + "/untrusted"})
    cls = AsyncMappedClient if asynchronous else MappedClient
    c = cls(transport=httpx.MockTransport(wire.send), follow_redirects=True)
    request = httpx.Request("GET", US + "/test", headers={"X-Api-Key": API_KEY, "X-Secret-Key": SECRET_KEY})
    try:
        response = run(asynchronous, lambda: c.send(request, follow_redirects=True))
        assert response.status_code == status
        assert_selected_only(wire, US, "keys", 1)
        assert wire.sleeps == []
    finally:
        close(c, asynchronous)
