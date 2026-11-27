"""A keyed SDK request that a response hook sends again through ``session.send`` with a different URL or proxy.

The SDK sends a keyed request to a listener on 127.0.0.1 (the origin); that is allowed and sent directly. A
response hook then copies the request (``response.request.copy()``), sets another URL and sends the copy itself
through ``session.send``. The hook is registered in one of two ways:

* ``session-hook``: in ``session.hooks["response"]``;
* ``auth-hook``: by the session's authentication, on the request it prepares.

Each case goes through ``HttpClient`` (``fi.api.auth``, with a ``FuturesSession``) and through ``_send_prepared``,
the send used by the knowledge base upload (``fi.kb.client``). The other listeners are the target and the proxy
of the ``net`` fixture of ``test_plain_http_key_guards``; ``plain.example.test`` resolves to the loopback interface
through its lookup shim, so no case reaches a real host. Each case reads the connections and the marker bytes at
the target and at the proxy, and prints them in its assertion messages.
"""

from __future__ import annotations

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient, _prepare, _send_prepared
from fi.api.types import HttpMethod, RequestConfig
from tests.test_keyed_request_paths import ok, sites  # noqa: F401
from tests.test_plain_http_key_guards import CODE, KEY, PLAIN, SECRET, Net, _attempt, net, refused, use_proxy  # noqa: F401

KEYED = {"X-Api-Key": KEY, "X-Secret-Key": SECRET}
REGISTRATIONS = ["session-hook", "auth-hook"]


class Resend:
    """A response hook that, on its first call, sends a copy of the request to ``url`` through ``session.send``.
    With ``pass_kwargs``, the send arguments the hook received (among them ``proxies``) are passed on; ``proxies``
    replaces them. What the send raised is kept in ``errors`` and raised again."""

    def __init__(self, url: str, *, pass_kwargs: bool = False, proxies=None) -> None:
        self.url = url
        self.pass_kwargs = pass_kwargs
        self.proxies = proxies
        self.session = None
        self.calls = 0
        self.errors: list = []

    def __call__(self, r, **kwargs):
        self.calls += 1
        if self.calls > 1:
            return r
        r.content
        prep = r.request.copy()
        prep.url = self.url
        send_kwargs = dict(kwargs) if self.pass_kwargs else {"timeout": 3}
        if self.proxies is not None:
            send_kwargs["proxies"] = self.proxies
        try:
            again = self.session.send(prep, **send_kwargs)
        except Exception as exc:
            self.errors.append(exc)
            raise
        again.content
        return r


class Registering(requests.auth.AuthBase):
    def __init__(self, hook) -> None:
        self.hook = hook

    def __call__(self, r):
        r.register_hook("response", self.hook)
        return r


def _hooked(session: requests.Session, hook: Resend, registration: str, *, proxies=None) -> requests.Session:
    hook.session = session
    if proxies:
        session.proxies.update(proxies)
    if registration == "session-hook":
        session.hooks["response"].append(hook)
    elif registration == "auth-hook":
        session.auth = Registering(hook)
    else:
        raise AssertionError(registration)
    return session


def via_http_client(origin: str, hook: Resend, registration: str, *, headers=KEYED, allow_insecure_http=None, proxies=None, mount=None):
    session = _hooked(FuturesSession(), hook, registration, proxies=proxies)
    if mount:
        session.mount(*mount)
    client = HttpClient(base_url=origin, session=session, default_headers=dict(headers), allow_insecure_http=allow_insecure_http)
    config = RequestConfig(method=HttpMethod.GET, url=origin + "/v1/ping", retry_attempts=1, timeout=3)
    return _attempt(lambda: client.request(config))


def via_send_prepared(origin: str, hook: Resend, registration: str, *, headers=KEYED, allow_insecure_http=None, proxies=None, mount=None):
    url = origin + "/v1/ping"

    def send():
        with _hooked(requests.Session(), hook, registration, proxies=proxies) as session:
            if mount:
                session.mount(*mount)
            prepared = _prepare(session, requests.Request(method="GET", url=url, headers=dict(headers)), allow_insecure_http)
            _send_prepared(session, prepared, 3, allow_insecure_http, url=url)

    return _attempt(send)


SENDERS = [
    pytest.param(via_http_client, id="http-client"),
    pytest.param(via_send_prepared, id="send-prepared"),
]


def _report(net: Net, origin, hook: Resend) -> str:
    return f"{net.report()}; origin: {len(origin.requests)} requests; hook calls: {hook.calls}; hook errors: {hook.errors!r}"


def _nothing_at_target_or_proxy(net: Net, origin, hook: Resend) -> None:
    counts = (net.target.connections, net.target.marker_bytes(), net.proxy.connections, net.proxy.marker_bytes())
    assert counts == (0, 0, 0, 0), _report(net, origin, hook)


# ---------------------------------------------------------------------------------------------
# a named plain-http host, without the opt-in: refused before any connection
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_to_a_named_plain_http_host_is_refused(net, sites, sender, registration):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"http://{PLAIN}:{net.target.port}/v1/ping")
    exc = sender(origin.base, hook, registration)
    _nothing_at_target_or_proxy(net, origin, hook)
    assert origin.requests == [("GET", "/v1/ping")], _report(net, origin, hook)
    refused(exc, ValueError)
    assert len(hook.errors) == 1, _report(net, origin, hook)
    refused(hook.errors[0], ValueError)


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_to_a_named_plain_http_host_with_the_send_arguments_is_refused(net, sites, sender, registration):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"http://{PLAIN}:{net.target.port}/v1/ping", pass_kwargs=True)
    exc = sender(origin.base, hook, registration)
    _nothing_at_target_or_proxy(net, origin, hook)
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# the opt-in: a named plain-http host is sent directly
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_to_a_named_plain_http_host_with_the_opt_in_is_sent_directly(net, sites, sender, registration):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"http://{PLAIN}:{net.target.port}/v1/ping")
    exc = sender(origin.base, hook, registration, allow_insecure_http=True)
    assert exc is None, f"{exc!r}; {_report(net, origin, hook)}"
    assert (net.target.connections, net.proxy.connections, net.proxy.marker_bytes()) == (1, 0, 0), _report(net, origin, hook)
    assert net.target.marker_bytes() > 0, _report(net, origin, hook)


# ---------------------------------------------------------------------------------------------
# a proxy that the hook's send would use: refused, for loopback and for the opt-in
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("proxy_source", ["session-proxies", "env-proxy", "send-proxies"])
@pytest.mark.parametrize(
    "host,allow",
    [pytest.param("127.0.0.1", None, id="loopback"), pytest.param(PLAIN, True, id="named-host-opt-in")],
)
@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_through_a_proxy_is_refused(monkeypatch, net, sites, sender, registration, host, allow, proxy_source):
    origin = sites(lambda method, path: ok())
    proxy = f"http://127.0.0.1:{net.proxy.port}"
    hook = Resend(f"http://{host}:{net.target.port}/v1/ping", proxies={"http": proxy} if proxy_source == "send-proxies" else None)
    if proxy_source == "env-proxy":
        use_proxy(monkeypatch, net)
    session_proxies = {"http": proxy} if proxy_source == "session-proxies" else None
    exc = sender(origin.base, hook, registration, allow_insecure_http=allow, proxies=session_proxies)
    _nothing_at_target_or_proxy(net, origin, hook)
    assert origin.requests == [("GET", "/v1/ping")], _report(net, origin, hook)
    refused(exc, ValueError)


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_through_a_custom_adapter_is_refused(net, sites, sender, registration):
    class CustomAdapter(HTTPAdapter):
        pass

    origin = sites(lambda method, path: ok())
    target = f"http://127.0.0.1:{net.target.port}/"
    hook = Resend(target + "v1/ping")
    exc = sender(origin.base, hook, registration, mount=(target, CustomAdapter()))
    _nothing_at_target_or_proxy(net, origin, hook)
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# controls: loopback directly, https, and a request without a key are sent as before
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_to_loopback_is_sent_directly(net, sites, sender, registration):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"http://127.0.0.1:{net.target.port}/v1/ping")
    exc = sender(origin.base, hook, registration)
    assert exc is None, f"{exc!r}; {_report(net, origin, hook)}"
    assert (net.target.connections, net.proxy.connections, net.proxy.marker_bytes()) == (1, 0, 0), _report(net, origin, hook)
    assert net.target.marker_bytes() > 0, _report(net, origin, hook)


@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_of_an_https_url_is_not_refused(net, sites, sender, registration):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"https://{PLAIN}:{net.target.port}/v1/ping")
    exc = sender(origin.base, hook, registration)
    assert len(hook.errors) == 1, _report(net, origin, hook)
    assert getattr(hook.errors[0], "code", None) != CODE, f"{hook.errors[0]!r}; {_report(net, origin, hook)}"
    assert isinstance(hook.errors[0], requests.exceptions.ConnectionError), f"{hook.errors[0]!r}"
    assert getattr(exc, "code", None) != CODE, f"{exc!r}"
    assert net.target.connections == 1, _report(net, origin, hook)
    assert (net.target.marker_bytes(), net.proxy.connections, net.proxy.marker_bytes()) == (0, 0, 0), _report(net, origin, hook)


@pytest.mark.parametrize("through_proxy", [pytest.param(False, id="direct"), pytest.param(True, id="session-proxy")])
@pytest.mark.parametrize("host", ["127.0.0.1", PLAIN])
@pytest.mark.parametrize("registration", REGISTRATIONS)
@pytest.mark.parametrize("sender", SENDERS)
def test_hook_session_send_of_a_request_without_a_key_is_unchanged(net, sites, sender, registration, host, through_proxy):
    origin = sites(lambda method, path: ok())
    hook = Resend(f"http://{host}:{net.target.port}/v1/ping")
    proxies = {"http": f"http://127.0.0.1:{net.proxy.port}"} if through_proxy else None
    exc = sender(origin.base, hook, registration, headers={}, proxies=proxies)
    assert exc is None, f"{exc!r}; {_report(net, origin, hook)}"
    assert hook.errors == [], _report(net, origin, hook)
    expected = (0, 1) if through_proxy else (1, 0)
    assert (net.target.connections, net.proxy.connections) == expected, _report(net, origin, hook)
    assert (net.target.marker_bytes(), net.proxy.marker_bytes()) == (0, 0), _report(net, origin, hook)
