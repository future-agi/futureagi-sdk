"""Source-derived H6 contract controls, NOT live captures and NOT executed evidence.

Authority: H6-REGIONAL-SOURCE-FIXTURE-r1.json, upstream
077a67e123501299cc0a47943c285fb1ea391301. Literal wire bytes below are independent
of SDK policy/error tables. No response location/hint is supplied by that fixture.
Existing no-redirect/no-replay behavior is preserved; regional typed guidance is
new expected-RED behavior. A failed test is not evidence until admitted execution.
"""
import logging
import re

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
    run,
)

# STRING error, never a nested code/message fixture. No varying headers invented.
REFUSALS = (
    (401, b'{"error":"omega_session_unavailable"}'),
    (403, b'{"error":"wrong_region"}'),
    (503, b'{"error":"omega_service_unavailable"}'),
)
OPERATIONS = {"json": "sandboxes.list", "create": "sandboxes.create",
              "sse": "sandboxes.commands.run", "upload": "sandboxes.files.upload",
              "download": "sandboxes.files.download"}


def regional_guidance(error):
    assert isinstance(error, errors.FutureAGIAPIError)
    assert error.status_code == 403 and error.code == "wrong_region"
    # The contract requires a distinct typed error, but does not freeze its class
    # spelling. Do not invent a new import which would mask transport RED at collection.
    assert type(error) not in (errors.FutureAGIAPIError, errors.PermissionDeniedError)
    assert getattr(errors, type(error).__name__, None) is type(error), "publicly catchable type"
    text = str(error)
    assert US in text and EU in text
    assert re.search(r"manual|explicit", text, re.I)
    assert re.search(r"select|configur|set .*base", text, re.I)
    assert not re.search(r"(?:your |the )(?:org|organization|workspace) (?:is|resides|belongs) (?:in|to)", text, re.I)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base", [US, EU], ids=["selected-us", "selected-eu"])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
@pytest.mark.parametrize("retries", [None, 0], ids=["default-retries", "retries-zero"])
@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("status,body", REFUSALS, ids=["unknown-key-401", "wrong-region-403", "unavailable-503"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_frozen_refusal_never_discovers_or_retries_another_region(
    wire, caplog, asynchronous, base, mode, retries, action, status, body,
):
    caplog.set_level(logging.DEBUG)
    wire.respond = lambda r: httpx.Response(status, content=body, headers={"content-type": "application/json"})
    c = wire.client(asynchronous, mode, retries, base_url=base)
    try:
        with pytest.raises(errors.FutureAGIAPIError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        error = caught.value
        # Same-origin retries on safe GET/PUT are not regional fallback. Exec and
        # creation remain one-shot even when a client uses normal default retries.
        count = 4 if status == 503 and retries is None and action in ("json", "upload", "download") else 1
        assert_selected_only(wire, base, mode, count)
        assert len(wire.sleeps) == count - 1
        assert error.status_code == status
        assert error.operation == OPERATIONS[action]
        assert_private(error, caplog.text)
        assert error.request_id is None
        assert error.retry_after is None
        if status == 403:
            regional_guidance(error)
        else:
            assert type(error) is (errors.AuthenticationError if status == 401 else errors.ServerError)
            assert US not in str(error) and EU not in str(error)
            assert "wrong_region" not in str(error)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base,other", [(US, EU), (EU, US)], ids=["us-to-eu", "eu-to-us"])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
@pytest.mark.parametrize("retries", [None, 0], ids=["default-retries", "retries-zero"])
@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("target_kind", ["cross-region", "same-host-downgrade"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_all_regional_redirects_and_downgrades_are_single_send(
    wire, caplog, asynchronous, base, other, mode, retries, action, status, target_kind,
):
    caplog.set_level(logging.DEBUG)
    target = (other if target_kind == "cross-region" else base.replace("https://", "http://")) + "/collect/" + SUBMITTED
    wire.respond = lambda r: httpx.Response(status, headers={"location": target})
    c = wire.client(asynchronous, mode, retries, base_url=base)
    try:
        with pytest.raises(errors.UnexpectedRedirectError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, action))
        assert_selected_only(wire, base, mode, 1)
        assert wire.sleeps == []
        assert caught.value.status_code == status
        assert caught.value.target_host is None  # stronger sandbox privacy boundary
        assert_private(caught.value, caplog.text, extra=(target,))
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base", [US, EU])
@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_guidance_is_fixed_not_a_reflected_response_destination(wire, caplog, asynchronous, base, action):
    caplog.set_level(logging.DEBUG)
    # Adversarial SUPPLEMENTAL input, not a claimed gateway response or fixture.
    # The accepted gateway supplies no destination URL. Hostile prose must not
    # become a new authority, even alongside its recognized string error code.
    bait = "https://untrusted-h6.invalid/" + SUBMITTED
    c = wire.client(asynchronous, retries=0, base_url=base)
    messages = []
    try:
        for payload in ({"error": "wrong_region"},
                        {"error": "wrong_region", "message": "move to " + bait,
                         "reason": "your organization is in stolen-region " + bait,
                         "fix": "send credentials to " + bait}):
            wire.respond = lambda r, p=payload: httpx.Response(403, json=p)
            with pytest.raises(errors.FutureAGIAPIError) as caught:
                run(asynchronous, lambda: invoke(c, asynchronous, action))
            messages.append(str(caught.value))
            assert_private(caught.value, caplog.text, extra=(bait, "stolen-region"))
            regional_guidance(caught.value)
        assert messages[0] == messages[1]
        assert_selected_only(wire, base, "keys", 2)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("status,body,kind", [
    (401, b'{"error":"wrong_region"}', errors.AuthenticationError),
    (503, b'{"error":"wrong_region"}', errors.ServerError),
    (403, b'{"error":"role_forbidden"}', errors.PermissionDeniedError),
])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_specialization_does_not_guess_from_code_or_status_alone(wire, asynchronous, status, body, kind):
    # Deliberately non-contract combinations: ordinary status semantics still win.
    wire.respond = lambda r: httpx.Response(status, content=body)
    c = wire.client(asynchronous, retries=0, base_url=EU)
    try:
        with pytest.raises(kind) as caught:
            run(asynchronous, lambda: c.sandboxes.list())
        assert type(caught.value) is kind
        assert US not in str(caught.value) and EU not in str(caught.value)
        assert_selected_only(wire, EU, "keys", 1)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base", [US, EU])
@pytest.mark.parametrize("action", ["json", "upload", "download"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_safe_same_origin_retry_is_not_regional_fallback(wire, asynchronous, base, action):
    from ._h6_k2w_transport import success
    wire.respond = lambda r: (httpx.Response(503, content=b'{"error":"omega_service_unavailable"}')
                              if len(wire.requests) == 1 else success(r))
    c = wire.client(asynchronous, base_url=base)
    try:
        run(asynchronous, lambda: invoke(c, asynchronous, action))
        assert_selected_only(wire, base, "keys", 2)
        assert len(wire.sleeps) == 1
        assert wire.requests[0].url == wire.requests[1].url
        assert wire.requests[0].content == wire.requests[1].content
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base", [US, EU])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_clone_retries_zero_keeps_selected_origin(wire, asynchronous, base):
    wire.respond = lambda r: httpx.Response(503, content=b'{"error":"omega_service_unavailable"}')
    c = wire.client(asynchronous, base_url=base)
    clone = c.with_options(retries=0)
    try:
        with pytest.raises(errors.ServerError):
            run(asynchronous, lambda: clone.sandboxes.list())
        assert_selected_only(wire, base, "keys", 1)
        assert wire.sleeps == []
    finally:
        close(clone, asynchronous)
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("case", ["us-derived", "eu-env-derived", "platform-env", "argument-wins", "selfhost"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_h6_selected_base_derivation_and_explicit_overrides(wire, monkeypatch, asynchronous, case):
    if case == "us-derived":
        options, expected = {"base_url": US}, US + "/omega/api"
    elif case == "eu-env-derived":
        monkeypatch.setenv("FI_BASE_URL", EU)
        options, expected = {}, EU + "/omega/api"
    elif case == "platform-env":
        monkeypatch.setenv("FI_PLATFORM_BASE_URL", EU + "/custom/api")
        options, expected = {"base_url": US}, EU + "/custom/api"
    elif case == "argument-wins":
        monkeypatch.setenv("FI_PLATFORM_BASE_URL", US + "/ignored")
        options, expected = {"base_url": US, "platform_base_url": EU + "/chosen/api"}, EU + "/chosen/api"
    else:
        options, expected = {"base_url": "https://selfhost-h6.invalid/root"}, "https://selfhost-h6.invalid/root/omega/api"
    c = wire.client(asynchronous, retries=0, **options)
    try:
        run(asynchronous, lambda: c.sandboxes.list())
        run(asynchronous, lambda: c.environments.list())
        assert [str(r.url) for r in wire.requests] == [
            expected + "/workspace/sandboxes", expected + "/workspace/environments"]
    finally:
        close(c, asynchronous)
