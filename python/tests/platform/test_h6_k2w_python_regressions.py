"""Supplemental Python controls; not part of the recorded H6/K2W baseline RED.

Only synthetic inputs and mock transports. These controls still require admitted
execution, including the inherited no-socket checks in the wire fixture.
"""
import warnings
from uuid import uuid4

import httpx
import pytest
from fi import errors

from ._h6_k2w_transport import (
    ACTIONS,
    EU,
    NOT_APPLICABLE_AT_FOLD,
    SANDBOX_ABSENT,
    SUBMITTED,
    US,
    assert_private,
    assert_selected_only,
    close,
    invoke,
    regional_guidance,
    run,
)
from .test_k2w_transport_safety import assert_warning_safety, warning_texts


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("flag", ["1", "true", "yes"])
def test_explicit_false_overrides_environment_in_parent_and_clone(wire, monkeypatch, asynchronous, flag):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", flag)
    c = wire.client(asynchronous, "bearer", base_url="http://explicit-false-k2w.invalid",
                    allow_insecure_http=False)
    clone = c.with_options(retries=0)
    try:
        for caller in (c, clone):
            with pytest.raises(errors.ConfigurationError) as caught:
                run(asynchronous, lambda: caller.environments.list())
            assert caught.value.code == "insecure_http_origin"
            assert_private(caught.value)
        assert wire.requests == []
    finally:
        close(clone, asynchronous)
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("flag", ["", "0", "false", "no", "not-an-optout"])
def test_nonoptout_environment_does_not_allow_bearer_http(wire, monkeypatch, asynchronous, flag):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", flag)
    c = wire.client(asynchronous, "bearer", base_url="http://false-env-k2w.invalid")
    try:
        with pytest.raises(errors.ConfigurationError) as caught:
            run(asynchronous, lambda: c.environments.list())
        assert caught.value.code == "insecure_http_origin"
        assert_private(caught.value)
        assert wire.requests == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_explicit_true_overrides_false_environment(wire, monkeypatch, asynchronous):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "0")
    base = "http://true-argument-k2w.invalid"
    c = wire.client(asynchronous, "bearer", base_url=base, allow_insecure_http=True)
    clone = c.with_options(retries=0)
    try:
        for caller in (c, clone):
            run(asynchronous, lambda: caller.environments.list())
        assert_selected_only(wire, base, "bearer", 2)
    finally:
        close(clone, asynchronous)
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_keys_warning_is_shared_by_core_console_paths_and_clones(wire, capsys, caplog, asynchronous):
    host = "shared-k2w-" + uuid4().hex + ".invalid"
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        for base in (f"http://{host}/private-path/a", f"http://{host.upper()}:80/private-path/b"):
            c = wire.client(asynchronous, base_url=base, retries=0)
            clone = c.with_options(retries=0)
            try:
                for caller in (c, clone):
                    for action in ("core", "console"):
                        run(asynchronous, lambda: invoke(caller, asynchronous, action))
            finally:
                close(clone, asynchronous)
                close(c, asynchronous)
    assert_selected_only(wire, "http://" + host, "keys", 8)
    assert_warning_safety(warning_texts(recorded, capsys, caplog), 1, keys=True)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_custom_host_keys_http_uses_one_cleartext_warning(wire, monkeypatch, capsys, caplog, asynchronous):
    host = "custom-keys-k2w-" + uuid4().hex + ".invalid"
    monkeypatch.setenv("FI_PLATFORM_BASE_URL", f"http://{host}/private-path/api")
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        c = wire.client(asynchronous, base_url="https://custom-keys-core.invalid",
                        allow_custom_platform_url=True, retries=0)
        try:
            for _ in range(2):
                run(asynchronous, lambda: c.environments.list())
            assert_selected_only(wire, "http://" + host, "keys", 2)
        finally:
            close(c, asynchronous)
    assert_warning_safety(warning_texts(recorded, capsys, caplog), 1, keys=True)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("action", [
    *(pytest.param(action, marks=pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)) for action in ACTIONS),
    "core", "console",
])
@pytest.mark.parametrize("body", [
    b'{"error":{"code":"wrong_region"}}',
    b'{"code":"wrong_region"}',
    b'{"status":false,"result":{"error":"wrong_region"}}',
    b'{"error":["wrong_region"]}',
    b'"wrong_region"',
    b'{"error":"wrong_region"',
])
def test_noncanonical_region_envelopes_keep_ordinary_permission_error(wire, asynchronous, action, body):
    wire.respond = lambda r: httpx.Response(403, content=body)
    c = wire.client(asynchronous, base_url=EU, retries=0)
    try:
        with pytest.raises(errors.PermissionDeniedError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        assert type(caught.value) is errors.PermissionDeniedError
        assert US not in str(caught.value) and EU not in str(caught.value)
        assert_private(caught.value)
        assert_selected_only(wire, EU, "keys", 1)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("action", ["core", "console"])
def test_non_sandbox_regional_guidance_is_public_and_fixed(wire, asynchronous, action):
    bait = "https://untrusted-regression.invalid/" + SUBMITTED
    c = wire.client(asynchronous, base_url=EU, retries=0)
    messages = []
    try:
        for payload in ({"error": "wrong_region"},
                        {"error": "wrong_region", "message": bait, "reason": bait,
                         "fix": bait, "detail": {"destination": bait}}):
            wire.respond = lambda r, p=payload: httpx.Response(403, json=p)
            with pytest.raises(errors.WrongRegionError) as caught:
                run(asynchronous, lambda: invoke(c, asynchronous, action))
            regional_guidance(caught.value)
            assert isinstance(caught.value, errors.PermissionDeniedError)
            assert caught.value.get_error_code() == "WRONG_REGION"
            assert caught.value.payload == {"error": "wrong_region"}
            assert_private(caught.value, extra=(bait,))
            messages.append(str(caught.value))
        assert messages[0] == messages[1]
        assert_selected_only(wire, EU, "keys", 2)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("action", ["json", "sse", "upload"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_regional_error_discards_every_response_diagnostic(wire, asynchronous, action):
    # Matches TypeScript: response-supplied IDs and Retry-After could carry hostile or private text.
    wire.respond = lambda r: httpx.Response(403, json={
        "error": "wrong_region", "message": SUBMITTED, "fix": SUBMITTED,
        "detail": {"destination": SUBMITTED},
        "requestId": "safe-gateway", "request_id": "safe-upstream",
    }, headers={"x-request-id": "safe-header", "x-omega-receipt-id": "safe-receipt", "retry-after": "0"})
    c = wire.client(asynchronous, base_url=EU, retries=0)
    try:
        with pytest.raises(errors.WrongRegionError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        error = caught.value
        regional_guidance(error)
        assert error.payload == {"error": "wrong_region"}
        assert (error.request_id, error.upstream_request_id, error.receipt_id, error.retry_after) == (None, None, None, None)
        assert "safe-" not in str(error) and "safe-" not in repr(error.to_dict())
        assert_private(error)
        assert_selected_only(wire, EU, "keys", 1)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_regional_authority_is_read_before_privacy_scrubbing(wire, asynchronous):
    # A scrub set may redact the discriminator value or rename its key; the exact wire envelope still decides.
    def hostile_scrubber(value, secrets):
        if isinstance(value, dict):
            return {("err" if k == "error" else k): ("[redacted]" if v == "wrong_region" else v) for k, v in value.items()}
        return value

    wire.respond = lambda r: httpx.Response(403, json={"error": "wrong_region"})
    c = wire.client(asynchronous, base_url=EU, retries=0)
    c._platform.shared.error_scrubber = hostile_scrubber
    try:
        with pytest.raises(errors.WrongRegionError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, "console"))
        regional_guidance(caught.value)
        assert caught.value.payload == {"error": "wrong_region"}
        assert_selected_only(wire, EU, "keys", 1)
    finally:
        close(c, asynchronous)


def test_an_explicit_non_regional_flag_never_promotes_the_exact_envelope():
    from fi._core.errors import api_error

    assert type(api_error(403, {"error": "wrong_region"}, regional=False)) is errors.PermissionDeniedError
    assert type(api_error(403, {"error": "wrong_region"})) is errors.WrongRegionError


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("host", ["127.0.0.2", "127.255.255.254"])
def test_any_127_loopback_bearer_http_is_not_refused(wire, asynchronous, host):
    base = f"http://{host}:19876"
    c = wire.client(asynchronous, "bearer", base_url=base, retries=0)
    try:
        run(asynchronous, lambda: c.environments.list())
        assert_selected_only(wire, base, "bearer", 1)
    finally:
        close(c, asynchronous)


def test_port_zero_and_the_default_port_are_distinct_warning_origins(capsys):
    from fi._core.http_security import check_http_security

    host = "port-zero-k2w-" + uuid4().hex + ".invalid"
    check_http_security(httpx.URL(f"http://{host}:0/"), "keys")
    check_http_security(httpx.URL(f"http://{host}/"), "keys")
    assert len([line for line in capsys.readouterr().err.splitlines() if line.strip()]) == 2


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_a_loopback_custom_host_keeps_its_custom_host_warning(wire, monkeypatch, capsys, caplog, asynchronous):
    base = "http://127.0.0.2:" + str(20000 + (1 if asynchronous else 0))
    monkeypatch.setenv("FI_PLATFORM_BASE_URL", base + "/omega/api")
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        c = wire.client(asynchronous, base_url="https://loopback-custom-core.invalid", allow_custom_platform_url=True, retries=0)
        try:
            run(asynchronous, lambda: c.environments.list())
            assert_selected_only(wire, base, "keys", 1)
        finally:
            close(c, asynchronous)
    texts = warning_texts(recorded, capsys, caplog)
    assert len(texts) == 1 and "outside the Future AGI zone" in texts[0]
