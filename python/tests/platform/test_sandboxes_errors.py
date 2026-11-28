"""Every sandbox error class (sync and async): status and code mapping from each PlatformError shape,
the fields, the existing ``fi.errors`` classes still catching them, every status and code the
generic contract oracle uses (sandbox rows are checked here instead), the network-policy 412/428,
transport failures, and no key in any error text."""

from __future__ import annotations

import json

import httpx
import pytest
from fi import errors as fe
from fi.sandbox import errors as se

from ._gates_support import REPO
from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    MODES,
    SBX,
    MockServer,
    api,
    resolve,
    run,
)

DATA = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
#: The independent oracle: contract section 4 (v2.1 for 412) by status, for every status the
#: generic fixture lists plus the sandbox-only ones.
SECTION_4 = {
    400: se.ValidationError, 401: se.AuthenticationError, 402: se.SandboxAPIError,
    403: se.PermissionDeniedError, 404: se.NotFoundError, 409: se.ConflictError,
    410: se.SandboxAPIError, 412: se.ConflictError, 413: se.PayloadTooLargeError,
    418: se.SandboxAPIError, 422: se.ValidationError, 428: se.ValidationError,
    429: se.RateLimitError, 500: se.SandboxAPIError, 502: se.ProviderError,
    503: se.UnavailableError, 504: se.SandboxAPIError, 507: se.InsufficientStorageError,
}

EE = {"code": "sandbox_busy", "message": "busy now", "detail": {"state": "active"}, "request_id": "req_ee"}
# (status, body, sandbox class, the fi.errors class it also is)
CASES = [
    (400, {"code": "invalid_body", "message": "bad"}, se.ValidationError, fe.BadRequestError),
    (401, {"error": "unauthorized", "reason": "no key"}, se.AuthenticationError, fe.AuthenticationError),
    (403, {"error": {"code": "forbidden", "message": "role", "fix": "ask an admin"}}, se.PermissionDeniedError,
     fe.PermissionDeniedError),
    (404, {"code": "not_found", "message": "no sandbox"}, se.NotFoundError, fe.NotFoundError),
    (409, EE, se.ConflictError, fe.ConflictError),
    (409, {**EE, "detail": {"state": "hibernated"}}, se.SandboxHibernatedError, fe.SandboxStateError),
    (409, {"code": "quota_exceeded", "message": "limit"}, se.QuotaExceededError, fe.ConflictError),
    (413, {"code": "payload_too_large", "message": "big"}, se.PayloadTooLargeError, fe.PayloadTooLargeError),
    (422, {"code": "invalid_policy", "message": "bad"}, se.ValidationError, fe.UnprocessableEntityError),
    (429, {"error": "rate_limited", "retryAfterSeconds": 7}, se.RateLimitError, fe.RateLimitError),
    (502, {"code": "provider_failed", "message": "docker"}, se.ProviderError, fe.ServerError),
    (503, {"code": "unavailable", "message": "later"}, se.UnavailableError, fe.ServerError),
    (507, {"code": "insufficient_storage", "message": "disk"}, se.InsufficientStorageError, fe.ServerError),
    (500, {"code": "internal", "message": "oops"}, se.SandboxAPIError, fe.FutureAGIAPIError),
]


def _get(mode, server):
    return run(resolve(api(server, mode, retries=0).get_info(SBX)))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("status,body,cls,legacy", CASES, ids=[f"{c[0]}-{c[2].__name__}" for c in CASES])
def test_each_status_maps_to_its_class(mode, status, body, cls, legacy):
    server = MockServer()
    server.on("sandboxes.getInfo", httpx.Response(status, json=body, headers={"x-request-id": "req-h"}))
    with pytest.raises(cls) as caught:
        _get(mode, server)
    err = caught.value
    assert type(err) is cls
    assert isinstance(err, se.SandboxError) and isinstance(err, legacy)
    assert err.status == status == err.status_code
    assert err.request_id in ("req-h", "req_ee") and err.message == str(err)
    assert err.operation == "sandboxes.getInfo" and err.code
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_every_status_and_code_of_the_generic_oracle_maps_by_section_4(mode):
    statuses = {int(s) for s in DATA["status_classes"]} | {412, 428, 507}
    assert statuses <= set(SECTION_4), sorted(statuses - set(SECTION_4))
    answers = [(status, None) for status in sorted(statuses)]
    answers += [(status, code) for code, status in DATA["fa_codes"].items()]
    answers += [(404, "product_not_admitted"), (422, "idempotency_key_reused"),
                (409, "idempotency_key_in_progress")]
    for status, code in answers:
        server = MockServer()
        body = {"status": False, "code": code, "message": "fixture refusal"}
        server.on("sandboxes.getInfo", httpx.Response(status, json=body, headers={"X-Request-Id": "contract-request"}))
        with pytest.raises(se.SandboxError) as caught:
            _get(mode, server)
        err = caught.value
        assert type(err) is SECTION_4[status], (status, code, type(err).__name__)
        assert err.status_code == status and err.request_id == "contract-request"
        assert isinstance(err, fe.FutureAGIAPIError) and len(server.seen) == 1
        if code:
            assert err.code == code


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("status,code,cls", [
    (412, "network_policy_revision_mismatch", se.ConflictError),
    (428, "network_policy_precondition_required", se.ValidationError),
])
def test_network_policy_preconditions_are_typed_and_never_retried(mode, status, code, cls):
    server = MockServer()
    server.on("sandboxes.networkPolicy.update", httpx.Response(status, json={"code": code, "message": "stale"}))
    with pytest.raises(cls) as caught:
        run(resolve(api(server, mode).network_policy.update(SBX, body={"mode": "off"}, if_match='"3"')))
    assert caught.value.code == code and caught.value.status == status
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_the_regional_guard_and_redirects_keep_their_core_class(mode):
    from fi._core.errors import WrongRegionError

    server = MockServer()
    server.on("sandboxes.list", httpx.Response(403, json={"error": "wrong_region"}))
    with pytest.raises(WrongRegionError):
        run(resolve(api(server, mode, retries=0).list()))
    server.on("sandboxes.list", httpx.Response(307, headers={"location": "https://elsewhere.test/x"}))
    with pytest.raises(fe.UnexpectedRedirectError):
        run(resolve(api(server, mode, retries=0).list()))
    assert len(server.seen) == 2


@pytest.mark.parametrize("mode", MODES)
def test_a_status_error_chains_nothing(mode):
    server = MockServer()
    server.on("sandboxes.getInfo", httpx.Response(404, json={"code": "not_found", "message": "gone"}))
    with pytest.raises(se.NotFoundError) as caught:
        _get(mode, server)
    assert caught.value.__cause__ is None and caught.value.__context__ is None


@pytest.mark.parametrize("mode", MODES)
def test_detail_and_the_ee_request_id_are_kept(mode):
    server = MockServer()
    server.on("sandboxes.getInfo", httpx.Response(409, json={**EE, "detail": {"state": "hibernated"}}))
    with pytest.raises(se.SandboxHibernatedError) as caught:
        _get(mode, server)
    assert caught.value.detail == {"state": "hibernated"}
    assert caught.value.request_id == "req_ee" and caught.value.code == "sandbox_busy"
    assert caught.value.payload["detail"] == {"state": "hibernated"}


@pytest.mark.parametrize("mode", MODES)
def test_a_state_that_is_not_a_sandbox_state_stays_redacted(mode):
    server = MockServer()
    server.on("sandboxes.getInfo", httpx.Response(409, json={**EE, "detail": {"state": "opaque-value"}}))
    with pytest.raises(se.ConflictError) as caught:
        _get(mode, server)
    assert type(caught.value) is se.ConflictError
    assert caught.value.detail == {"state": "[redacted]"}
    assert "opaque-value" not in " ".join([str(caught.value), str(caught.value.payload)])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("headers,body,expected", [
    ({"Retry-After": "4"}, {"error": "rate_limited"}, 4.0),
    ({}, {"code": "rate_limited", "message": "slow", "detail": {"retryAfterSeconds": 9}}, 9.0),
])
def test_retry_after_seconds_comes_from_the_header_or_the_detail(mode, headers, body, expected):
    server = MockServer()
    server.on("sandboxes.getInfo", httpx.Response(429, json=body, headers=headers))
    with pytest.raises(se.RateLimitError) as caught:
        _get(mode, server)
    assert caught.value.retry_after_seconds == expected


@pytest.mark.parametrize("mode", MODES)
def test_a_create_that_got_no_answer_says_completion_is_unknown(mode):
    server = MockServer()

    def drop(request):
        raise httpx.ReadTimeout("slow", request=request)

    server.on("sandboxes.create", drop)
    with pytest.raises(se.ConnectionError) as caught:
        run(resolve(api(server, mode).create(body={"name": "n"})))
    err = caught.value
    assert isinstance(err, se.ConnectionTimeoutError) and isinstance(err, fe.APITimeoutError)
    assert err.possibly_applied and "completion is unknown" in str(err) and err.status is None
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_a_refused_connection_is_a_connection_error(mode):
    server = MockServer()

    def refuse(request):
        raise httpx.ConnectError("refused", request=request)

    server.on("sandboxes.list", refuse)
    with pytest.raises(se.ConnectionError) as caught:
        run(resolve(api(server, mode, retries=0).list()))
    assert isinstance(caught.value, fe.APIConnectionError) and not caught.value.possibly_applied
    assert "completion is unknown" not in str(caught.value)


@pytest.mark.parametrize("mode", MODES)
def test_a_path_that_climbs_out_is_refused_before_sending(mode):
    server = MockServer()
    with pytest.raises(se.ConfigurationError) as caught:
        run(resolve(api(server, mode).files.read(SBX, "a/../../etc/passwd")))
    assert caught.value.code == "invalid_path" and server.seen == []  # the files rule refuses it first


@pytest.mark.parametrize("mode", MODES)
def test_an_oversized_upload_is_refused_before_sending(mode, monkeypatch):
    from fi._core.request import BODY_LIMITS

    monkeypatch.setitem(BODY_LIMITS, "bundle", 8)
    server = MockServer()
    with pytest.raises(se.PayloadTooLargeError) as caught:
        run(resolve(api(server, mode).files.upload(SBX, "big.bin", body=b"x" * 64)))
    assert caught.value.local and caught.value.limit_bytes == 8 and server.seen == []


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_a_reflected_key_never_reaches_the_error(mode, auth):
    from ._sandbox_mock import FAKE_TOKEN

    server = MockServer()
    echo = f"bad credential {FAKE_KEY} {FAKE_SECRET} {FAKE_TOKEN}"
    server.on("sandboxes.getInfo", httpx.Response(401, json={"code": "unauthorized", "message": echo}))
    with pytest.raises(se.AuthenticationError) as caught:
        run(resolve(api(server, mode, auth=auth).get_info(SBX)))
    text = " ".join([str(caught.value), repr(caught.value), str(caught.value.payload), str(caught.value.to_dict())])
    secrets = (FAKE_KEY, FAKE_SECRET) if auth == "keys" else (FAKE_TOKEN,)
    assert not any(secret in text for secret in secrets)


def test_command_errors_carry_the_partial_output():
    err = se.CommandIncompleteError("cut", exec_id="exec_1", stdout="a", stderr="b")
    assert isinstance(err, se.SandboxError) and err.status is None
    assert (err.exec_id, err.stdout, err.stderr, err.operation) == ("exec_1", "a", "b", "sandboxes.commands.run")
    assert se.CommandFailedError("x").get_error_code() == "COMMAND_FAILED"


def test_configuration_errors_are_both_trees():
    err = se.ConfigurationError("no base url", code="missing_base_url")
    assert isinstance(err, fe.ConfigurationError) and isinstance(err, se.SandboxError)
    assert err.code == "missing_base_url" and err.status is None
