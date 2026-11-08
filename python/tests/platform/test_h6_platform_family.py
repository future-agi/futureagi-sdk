"""Released-client H6 contract pins. Mock-only; synthetic credentials, no discovery."""
from __future__ import annotations

import asyncio

import httpx
import pytest

from fi import platform as sdk
from fi._core import http_security
from fi.platform import _transport as released_transport

US = "https://api.futureagi.com"
EU = "https://api-eu.futureagi.com"
SERVER_HOST = "untrusted-platform-h6.invalid"
DESTINATION = "https://" + SERVER_HOST + "/server-only-destination"
KEY = "synthetic-platform-h6-key"
SECRET = "synthetic-platform-h6-secret"
TOKEN = "synthetic-platform-h6-token"


@pytest.fixture(autouse=True)
def isolated_http_notices(monkeypatch):
    monkeypatch.setattr(http_security, "_warned", set())


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def asynchronous(request):
    return request.param


def exchange(asynchronous, respond, *, base=US, method="GET", retries=2):
    """Use the released public clients, including a caller client that follows redirects."""
    seen = []

    def send(request):
        seen.append(request)
        return respond(request)

    config = dict(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=retries)
    mock = httpx.MockTransport(send)
    if asynchronous:
        async def go():
            async with httpx.AsyncClient(transport=mock, follow_redirects=True) as http:
                async with sdk.AsyncClient(http_client=http, **config) as client:
                    try:
                        return await client.request(method, "/h6-probe")
                    except Exception as error:
                        return error
        outcome = asyncio.run(go())
    else:
        with httpx.Client(transport=mock, follow_redirects=True) as http:
            with sdk.Client(http_client=http, **config) as client:
                try:
                    outcome = client.request(method, "/h6-probe")
                except Exception as error:
                    outcome = error
    return outcome, seen


def selected_once(seen, base):
    assert len(seen) == 1
    assert str(seen[0].url) == base + "/h6-probe"
    assert seen[0].headers["x-api-key"] == KEY
    assert seen[0].headers["x-secret-key"] == SECRET


@pytest.mark.parametrize("base", [US, EU], ids=["us", "eu"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_exact_wrong_region_is_exported_permission_subclass(asynchronous, base, method):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(403, json={"error": "wrong_region"}),
                           base=base, method=method)
    # Guard the new export: the base must fail by assertion, never import/attribute error.
    kind = getattr(sdk, "WrongRegionError", None)
    assert isinstance(kind, type), "fi.platform must export WrongRegionError"
    assert "WrongRegionError" in sdk.__all__
    assert type(error) is kind
    assert isinstance(error, sdk.PermissionDeniedError)
    try:
        raise error
    except sdk.PermissionDeniedError as caught:
        assert caught is error
    assert error.status_code == 403 and error.code == "wrong_region"
    selected_once(seen, base)


NEAR_MISSES = [
    (403, b'{"code":"wrong_region"}', sdk.PermissionDeniedError),
    (403, b'{"error":{"code":"wrong_region"}}', sdk.PermissionDeniedError),
    (403, b'{"status":false,"result":{"error":"wrong_region"}}', sdk.PermissionDeniedError),
    (403, b'{"error":["wrong_region"]}', sdk.PermissionDeniedError),
    (403, b'"wrong_region"', sdk.PermissionDeniedError),
    (403, b'{"error":"wrong_region"', sdk.PermissionDeniedError),
    (403, b'{"error":"prefix_wrong_region"}', sdk.PermissionDeniedError),
    (403, b'{"error":"wrong_region "}', sdk.PermissionDeniedError),
    (403, b'{"error":"WRONG_REGION"}', sdk.PermissionDeniedError),
    (403, b'{"message":"wrong_region"}', sdk.PermissionDeniedError),
    (403, b'{"error":null}', sdk.PermissionDeniedError),
    (401, b'{"error":"wrong_region"}', sdk.AuthenticationError),
    (503, b'{"error":"wrong_region"}', sdk.InternalServerError),
]


@pytest.mark.parametrize("status,body,kind", NEAR_MISSES, ids=[
    "code-only", "nested", "wrapped", "array", "string", "invalid-json", "substring",
    "whitespace", "case", "prose-only", "null", "401", "503",
])
def test_near_misses_keep_released_status_class(asynchronous, status, body, kind):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(status, content=body), retries=0)
    assert type(error) is kind
    selected_once(seen, US)


@pytest.mark.parametrize("base", [US, EU], ids=["us", "eu"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_wrong_region_never_retries_or_follows_location(asynchronous, base, method):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(
        403, json={"error": "wrong_region", "reason": "move to " + DESTINATION},
        headers={"location": DESTINATION, "retry-after": "0"},
    ), base=base, method=method)
    assert isinstance(error, sdk.PermissionDeniedError)
    selected_once(seen, base)


def test_wrong_region_guidance_and_diagnostics_are_sdk_authored(asynchronous):
    messages = []
    for body in ({"error": "wrong_region"}, {
        "error": "wrong_region", "code": "role_forbidden", "message": "move to " + DESTINATION,
        "reason": "your workspace resides at " + DESTINATION, "fix": DESTINATION,
        "detail": {"destination": DESTINATION}, "requestId": DESTINATION,
    }):
        error, seen = exchange(asynchronous, lambda _, body=body: httpx.Response(
            403, json=body, headers={"location": DESTINATION, "x-request-id": DESTINATION},
        ))
        assert isinstance(error, sdk.PermissionDeniedError)
        text = str(error)
        assert SERVER_HOST not in text and DESTINATION not in text
        assert US in text and EU in text and "Manually select" in text
        assert "base_url / FI_BASE_URL" in text
        assert "never probes, redirects or retries against another region" in text
        assert error.body == {"error": "wrong_region"}
        assert error.detail is None and error.request_id is None
        assert error.code == "wrong_region"
        # The released API's raw HTTP response remains explicitly inspectable.
        assert error.response.status_code == 403
        messages.append(text)
        selected_once(seen, US)
    assert messages[0] == messages[1]


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("target", [DESTINATION, US.replace("https:", "http:") + "/server-only-destination"],
                         ids=["foreign-host", "downgrade"])
def test_redirect_refusal_does_not_echo_destination(asynchronous, status, target):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(status, headers={"location": target}))
    assert isinstance(error, sdk.APIConnectionError)
    assert SERVER_HOST not in str(error) and target not in str(error)
    assert "server-only-destination" not in str(error)
    assert "not followed" in str(error)
    selected_once(seen, US)


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("target", [DESTINATION, US.replace("https:", "http:") + "/h6-probe"],
                         ids=["foreign-host", "downgrade"])
def test_cross_origin_redirect_never_sends_to_target(asynchronous, status, target):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(status, headers={"location": target}))
    assert isinstance(error, sdk.APIConnectionError)
    selected_once(seen, US)


@pytest.mark.parametrize("base", [
    "http://remote-platform-h6.invalid", "http://localhost.attacker.invalid",
    "http://128.0.0.1", "http://[::ffff:127.0.0.1]", "http://[::2]",
], ids=["remote", "localhost-suffix", "outside-127", "mapped-ipv6", "other-ipv6"])
@pytest.mark.parametrize("source", ["argument", "environment"])
def test_keys_http_sends_once_per_call_and_warns_once_per_origin(asynchronous, monkeypatch, capsys, base, source):
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    monkeypatch.delenv("FI_ALLOW_CUSTOM_PLATFORM_URL", raising=False)
    for index, path in enumerate(("/private-path/a", "/private-path/b")):
        target = base + path
        monkeypatch.setenv("FI_BASE_URL", target)
        value, seen = exchange(asynchronous, lambda _: httpx.Response(200, json={"ok": True}),
                               base=target if source == "argument" else None)
        assert value == {"ok": True}
        assert len(seen) == 1, "one transport call per request, with no refusal or retry"
        assert seen[0].url == httpx.URL(target + "/h6-probe")
        assert seen[0].headers["x-api-key"] == KEY and seen[0].headers["x-secret-key"] == SECRET
        assert "authorization" not in seen[0].headers
        notices = capsys.readouterr().err.splitlines()
        assert len(notices) == (1 if index == 0 else 0)
        for notice in notices:
            assert "cleartext" in notice and "deprecated" in notice and "keys" in notice
            assert all(marker not in notice for marker in (KEY, SECRET, TOKEN, "private-path", "h6-probe"))


@pytest.mark.parametrize("first", ["lane", "released"])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
def test_http_notice_budget_is_shared_with_lane_and_canonical_origins(asynchronous, capsys, first, mode):
    base = "http://shared-platform-h6.invalid"

    def lane():
        http_security.check_http_security(httpx.URL(base + "/private-path/lane"), mode, allow_insecure_http=True)

    def released():
        value, seen = exchange(asynchronous, lambda _: httpx.Response(200, json={"ok": True}),
                               base="http://SHARED-PLATFORM-H6.invalid.:80/private-path/released")
        assert value == {"ok": True} and len(seen) == 1

    callers = (lane, released) if first == "lane" else (released, lane)
    for index, caller in enumerate(callers):
        caller()
        notices = capsys.readouterr().err.splitlines()
        assert len(notices) == (1 if index == 0 else 0)
        assert all(marker not in notice for notice in notices for marker in (KEY, SECRET, TOKEN, "private-path"))
    value, seen = exchange(asynchronous, lambda _: httpx.Response(200, json={"ok": True}), base=base + ":8080")
    assert value == {"ok": True} and len(seen) == 1
    assert len(capsys.readouterr().err.splitlines()) == 1, "a different port has its own warning budget"


@pytest.mark.parametrize("base", [US, "http://token-ignored-platform-h6.invalid"], ids=["https", "http"])
def test_released_keys_clients_do_not_discover_or_send_bearer_tokens(asynchronous, monkeypatch, base):
    # No bearer credential mode exists in either released constructor.
    monkeypatch.setenv("FI_PLATFORM_TOKEN", TOKEN)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    value, seen = exchange(asynchronous, lambda _: httpx.Response(200, json={"ok": True}), base=base)
    assert value == {"ok": True}
    selected_once(seen, base)
    assert "authorization" not in seen[0].headers
    assert TOKEN not in str(seen[0].headers)


@pytest.mark.parametrize("base", [
    "https://secure-platform-h6.invalid", "http://localhost:19876", "http://LOCALHOST.:19876",
    "http://127.0.0.1:19876", "http://127.0.0.2:19876", "http://127.255.255.254:19876",
    "http://[::1]:19876",
], ids=["https", "localhost", "localhost-dot", "127-1", "127-2", "127-last", "ipv6"])
def test_https_and_loopback_http_still_send_credentials(asynchronous, capsys, base):
    value, seen = exchange(asynchronous, lambda _: httpx.Response(200, json={"ok": True}), base=base)
    assert value == {"ok": True}
    assert len(seen) == 1
    assert seen[0].url == httpx.URL(base + "/h6-probe")
    assert seen[0].headers["x-api-key"] == KEY and seen[0].headers["x-secret-key"] == SECRET
    assert "authorization" not in seen[0].headers
    assert capsys.readouterr().err == ""


def test_same_origin_http_redirect_rechecks_shared_policy(asynchronous, monkeypatch, capsys):
    base = "http://redirect-platform-h6.invalid"
    checked = []

    def check(url, mode):
        checked.append((str(url), mode))
        http_security.check_http_security(url, mode)

    # The name is absent on the base; install a seam without an AttributeError.
    monkeypatch.setattr(released_transport, "check_http_security", check, raising=False)

    def respond(request):
        if request.url.path == "/h6-probe":
            return httpx.Response(302, headers={"location": "/private-path/done"})
        return httpx.Response(200, json={"ok": True})

    value, seen = exchange(asynchronous, respond, base=base)
    assert value == {"ok": True}
    destinations = [base + "/h6-probe", base + "/private-path/done"]
    assert [str(r.url) for r in seen] == destinations
    assert checked == [(url, "keys") for url in destinations]
    assert all(r.headers["x-api-key"] == KEY and r.headers["x-secret-key"] == SECRET for r in seen)
    notices = capsys.readouterr().err.splitlines()
    assert len(notices) == 1
    assert all(marker not in notices[0] for marker in (KEY, SECRET, TOKEN, "private-path", "h6-probe"))


@pytest.mark.parametrize("base", [US, "http://127.0.0.2:19876"], ids=["https", "loopback"])
@pytest.mark.parametrize("status,expected_method", [(301, "GET"), (302, "GET"), (303, "GET"),
                                                   (307, "POST"), (308, "POST")])
def test_same_origin_redirects_keep_method_rules(asynchronous, base, status, expected_method):
    def respond(request):
        if request.url.path == "/h6-probe":
            return httpx.Response(status, headers={"location": "/done"})
        return httpx.Response(200, json={"ok": True})
    value, seen = exchange(asynchronous, respond, base=base, method="POST")
    assert value == {"ok": True}
    assert [str(r.url) for r in seen] == [base + "/h6-probe", base + "/done"]
    assert [r.method for r in seen] == ["POST", expected_method]
    assert all(r.headers["x-api-key"] == KEY and r.headers["x-secret-key"] == SECRET for r in seen)


def test_same_origin_redirect_budget_is_unchanged(asynchronous):
    error, seen = exchange(asynchronous, lambda _: httpx.Response(302, headers={"location": "/h6-probe"}))
    assert isinstance(error, sdk.APIConnectionError)
    assert "more than 5 redirects" in str(error)
    assert len(seen) == 6
    assert all(str(r.url) == US + "/h6-probe" for r in seen)
