"""Keys added on a redirect hop: the first request goes to a loopback URL without a key, the loopback listener
answers 302 to plain ``http://`` on another host, and something the session holds adds a key to that hop:

* ``session-hook-send`` / ``auth-hook-send`` / ``request-hook-send``: a response hook (of the session, registered by
  the session's authentication, or given with the request) answers a 401 by sending the request again with
  ``X-Api-Key`` through ``session.send``;
* ``session-hook-header`` / ``auth-hook-header``: a response hook sets ``X-Api-Key`` on ``r.request.headers`` of the
  302, which ``requests`` copies into the hop;
* ``session-hook-cookie`` / ``auth-hook-cookie``: a response hook sets a session cookie named ``X-Api-Key`` on the
  302, which ``requests`` merges into the hop;
* ``adapter``: an ``HTTPAdapter`` subclass that adds ``X-Api-Key``, mounted only for the hop's host.

Each case goes through ``HttpClient``. For ``HttpClient`` the request hook comes from
a ``FuturesSession`` subclass whose ``request()`` adds it. Listeners run on the loopback interface;
``plain.example.test`` resolves to them through the lookup shim of ``test_plain_http_key_guards``. Each case reads,
at the hop's target and at the proxy listener, the connections, the connections that held the marker key and the
marker bytes.
"""

from __future__ import annotations

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.errors import KeyedRedirectRefusedError
from fi.api.types import HttpMethod, RequestConfig
from tests.test_keys_added_after_judgement import ChallengeSink
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, Sink, _attempt, _marker_forms, net, refused  # noqa: F401

PLAIN = "plain.example.test"
VARIANTS = [
    "session-hook-send",
    "auth-hook-send",
    "request-hook-send",
    "session-hook-header",
    "auth-hook-header",
    "session-hook-cookie",
    "auth-hook-cookie",
    "adapter",
]


class RedirectSink(Sink):
    """A loopback listener that answers every request with 302 to ``location``."""

    def __init__(self, location: str) -> None:
        self.location = location
        super().__init__()

    def _handle(self, conn) -> None:
        conn.settimeout(0.4)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            with self._lock:
                self.raw += data
            conn.sendall(
                f"HTTP/1.1 302 Found\r\nLocation: {self.location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode()
            )
        except OSError:
            pass
        finally:
            conn.close()


class DigestSink(Sink):
    """A loopback listener that answers 401 with a Digest challenge to a request without a Digest
    ``Authorization`` header, and 200 to one with it."""

    def __init__(self) -> None:
        self.digest_ok = 0
        super().__init__()

    def _handle(self, conn) -> None:
        conn.settimeout(0.4)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            with self._lock:
                self.raw += data
            if b"\r\nAuthorization: Digest " in data:
                with self._lock:
                    self.digest_ok += 1
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
            else:
                conn.sendall(
                    b"HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Digest realm=\"r\", nonce=\"n1\", qop=\"auth\"\r\n"
                    b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                )
        except OSError:
            pass
        finally:
            conn.close()


class Hops:
    def __init__(self) -> None:
        self.target = ChallengeSink()
        self.proxy = ChallengeSink()
        self.redirect: RedirectSink | None = None

    def redirect_to(self, location: str) -> str:
        self.redirect = RedirectSink(location)
        return f"http://127.0.0.1:{self.redirect.port}/v1/ping"

    def counts(self, sink: ChallengeSink) -> tuple:
        return sink.connections, sink.keyed_connections, sink.marker_bytes()

    def report(self) -> str:
        return f"target (connections, keyed, marker bytes): {self.counts(self.target)}; proxy: {self.counts(self.proxy)}"

    def nothing_reached_target_or_proxy(self) -> None:
        assert (self.counts(self.target), self.counts(self.proxy)) == ((0, 0, 0), (0, 0, 0)), self.report()
        if self.redirect is not None:
            assert self.redirect.connections == 1 and self.redirect.marker_bytes() == 0, self.redirect.connections

    def no_key_through_proxy(self) -> None:
        assert (self.proxy.keyed_connections, self.proxy.marker_bytes()) == (0, 0), self.report()

    def delivered_direct(self) -> None:
        assert self.target.keyed_connections >= 1 and self.target.marker_bytes() > 0, self.report()
        self.no_key_through_proxy()

    def followed_or_not_followed(self, exc) -> None:
        """Where 0.8.1 follows a keyed redirect, 0.9.0 does not follow it (``KeyedRedirectRefusedError``): then the hop
        target and the proxy receive nothing."""
        if isinstance(exc, KeyedRedirectRefusedError):
            assert (self.counts(self.target), self.counts(self.proxy)) == ((0, 0, 0), (0, 0, 0)), self.report()
            return
        assert exc is None, repr(exc)
        self.delivered_direct()

    def close(self) -> None:
        for sink in (self.target, self.proxy, self.redirect):
            if sink is not None:
                sink.close()


@pytest.fixture
def hops(net):
    pair = Hops()
    yield pair
    pair.close()


# ---------------------------------------------------------------------------------------------
# what adds the key on the hop
# ---------------------------------------------------------------------------------------------


def _send_again_with_key(session):
    def hook(r, **kwargs):
        if r.status_code != 401 or "X-Api-Key" in r.request.headers:
            return r
        r.content
        r.close()
        prep = r.request.copy()
        prep.headers["X-Api-Key"] = KEY
        return session.send(prep, **kwargs)

    return hook


def _set_header_on_redirect(r, **kwargs):
    if r.is_redirect:
        r.request.headers["X-Api-Key"] = KEY
    return r


def _set_cookie_on_redirect(session):
    def hook(r, **kwargs):
        if r.is_redirect:
            session.cookies.set("X-Api-Key", KEY)
        return r

    return hook


class HookAuth(requests.auth.AuthBase):
    def __init__(self, hook) -> None:
        self._hook = hook

    def __call__(self, r):
        r.register_hook("response", self._hook)
        return r


class KeyAddingAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        request.headers["X-Api-Key"] = KEY
        return super().send(request, **kwargs)


class HookingFuturesSession(FuturesSession):
    """A ``FuturesSession`` whose ``request()`` adds a response hook that sends again with a key."""

    def request(self, *args, **kwargs):
        kwargs.setdefault("hooks", {"response": [_send_again_with_key(self)]})
        return super().request(*args, **kwargs)


class FalsyHooks(list):
    def __bool__(self):
        return False

    def __len__(self):
        return 0


def _session(cls, variant: str, target_prefix: str, *, trust_env: bool = True, proxies=None):
    """``(session, request hooks)`` for ``variant``."""
    if variant == "request-hook-send" and cls is FuturesSession:
        cls = HookingFuturesSession
    session = cls()
    session.trust_env = trust_env
    if proxies:
        session.proxies.update(proxies)
    request_hooks = None
    if variant == "session-hook-send":
        session.hooks["response"].append(_send_again_with_key(session))
    elif variant == "auth-hook-send":
        session.auth = HookAuth(_send_again_with_key(session))
    elif variant == "request-hook-send":
        if cls is requests.Session:
            request_hooks = {"response": [_send_again_with_key(session)]}
    elif variant == "session-hook-header":
        session.hooks["response"].append(_set_header_on_redirect)
    elif variant == "auth-hook-header":
        session.auth = HookAuth(_set_header_on_redirect)
    elif variant == "session-hook-cookie":
        session.hooks["response"].append(_set_cookie_on_redirect(session))
    elif variant == "auth-hook-cookie":
        session.auth = HookAuth(_set_cookie_on_redirect(session))
    elif variant == "adapter":
        session.mount(target_prefix, KeyAddingAdapter())
    elif variant == "falsy-session-hooks":
        hooks = FalsyHooks()
        list.append(hooks, _send_again_with_key(session))
        session.hooks["response"] = hooks
    elif variant == "none":
        pass
    else:
        raise AssertionError(variant)
    return session, request_hooks


# ---------------------------------------------------------------------------------------------
# senders: each sends one request without a key to ``url`` and returns the error it raised, if any
# ---------------------------------------------------------------------------------------------


def via_http_client(url: str, variant: str, target_prefix: str, *, allow_insecure_http=None, headers=None, **session_kwargs):
    session, _ = _session(FuturesSession, variant, target_prefix, **session_kwargs)
    client = HttpClient(base_url=url, session=session, default_headers=headers or {}, allow_insecure_http=allow_insecure_http)
    config = RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1, timeout=3)
    try:
        return _attempt(lambda: client.request(config))
    finally:
        session.close()




SENDERS = [
    pytest.param(via_http_client, id="http-client"),
    # 0.9.0 has no _prepare/_send_prepared send: HttpClient is the requests sender the session reaches.
]


def _plain_hop(hops: Hops) -> tuple:
    """``(first URL, adapter prefix of the hop)`` for a loopback URL that redirects to ``plain.example.test``."""
    return hops.redirect_to(f"http://{PLAIN}:{hops.target.port}/landed"), f"http://{PLAIN}:{hops.target.port}/"


# ---------------------------------------------------------------------------------------------
# a hop to a plain http host that is not loopback, without the opt-in: refused before the hop connects
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("env_proxy", [pytest.param(False, id="no-proxy"), pytest.param(True, id="env-proxy")])
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_on_a_hop_to_a_named_plain_http_host_is_refused(monkeypatch, hops, sender, variant, env_proxy):
    if env_proxy:
        monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{hops.proxy.port}")
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    url, prefix = _plain_hop(hops)
    exc = sender(url, variant, prefix)
    hops.nothing_reached_target_or_proxy()
    refused(exc, ValueError)


@pytest.mark.parametrize("proxy_key", [pytest.param("http://", id="http-host"), pytest.param("all://", id="all-host")])
@pytest.mark.parametrize("trust_env", [pytest.param(True, id="trust-env"), pytest.param(False, id="no-trust-env")])
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_on_a_hop_with_a_host_keyed_session_proxy_is_refused(hops, sender, variant, trust_env, proxy_key):
    url, prefix = _plain_hop(hops)
    proxies = {f"{proxy_key}{PLAIN}": f"http://127.0.0.1:{hops.proxy.port}"}
    exc = sender(url, variant, prefix, trust_env=trust_env, proxies=proxies)
    hops.nothing_reached_target_or_proxy()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# a hop that may be sent (opt-in, or loopback): the key goes through no proxy
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("proxy_key", [pytest.param("http://", id="http-host"), pytest.param("all://", id="all-host")])
@pytest.mark.parametrize("trust_env", [pytest.param(True, id="trust-env"), pytest.param(False, id="no-trust-env")])
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_opted_in_hop_never_carries_a_key_through_a_host_keyed_session_proxy(hops, sender, variant, trust_env, proxy_key):
    url, prefix = _plain_hop(hops)
    proxies = {f"{proxy_key}{PLAIN}": f"http://127.0.0.1:{hops.proxy.port}"}
    exc = sender(url, variant, prefix, allow_insecure_http=True, trust_env=trust_env, proxies=proxies)
    hops.no_key_through_proxy()
    if exc is None:
        hops.delivered_direct()
    else:
        refused(exc, ValueError)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_opted_in_hop_never_carries_a_key_through_an_environment_proxy(monkeypatch, hops, sender, variant):
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{hops.proxy.port}")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    url, prefix = _plain_hop(hops)
    exc = sender(url, variant, prefix, allow_insecure_http=True)
    hops.no_key_through_proxy()
    if exc is None:
        hops.delivered_direct()
    else:
        refused(exc, ValueError)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_loopback_hop_never_carries_a_key_through_a_host_keyed_session_proxy(hops, sender, variant):
    url = hops.redirect_to(f"http://localhost:{hops.target.port}/landed")
    proxies = {"http://localhost": f"http://127.0.0.1:{hops.proxy.port}"}
    exc = sender(url, variant, f"http://localhost:{hops.target.port}/", trust_env=False, proxies=proxies)
    hops.no_key_through_proxy()
    if exc is None:
        hops.delivered_direct()
    else:
        refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# no redirect: hooks the first judgement did not see
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sender", SENDERS)
def test_falsy_session_hook_container_is_judged_by_its_items(hops, sender):
    exc = sender(f"http://{PLAIN}:{hops.target.port}/v1/ping", "falsy-session-hooks", "unused://")
    hops.nothing_reached_target_or_proxy()
    refused(exc, ValueError)


def test_hooks_a_session_subclass_adds_in_request_are_judged(hops):
    exc = via_http_client(f"http://{PLAIN}:{hops.target.port}/v1/ping", "request-hook-send", "unused://")
    hops.nothing_reached_target_or_proxy()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# controls: loopback to loopback, the opt-in, and digest authentication still work
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sender", SENDERS)
def test_keyed_redirect_from_loopback_to_loopback_is_followed(hops, sender):
    url = hops.redirect_to(f"http://127.0.0.1:{hops.target.port}/landed")
    exc = sender(url, "none", "unused://", headers={"X-Api-Key": KEY})
    hops.followed_or_not_followed(exc)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_on_a_hop_from_loopback_to_loopback_is_sent_directly(hops, sender, variant):
    url = hops.redirect_to(f"http://127.0.0.1:{hops.target.port}/landed")
    exc = sender(url, variant, f"http://127.0.0.1:{hops.target.port}/")
    hops.followed_or_not_followed(exc)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_on_an_opted_in_hop_is_sent_directly(hops, sender, variant):
    url, prefix = _plain_hop(hops)
    exc = sender(url, variant, prefix, allow_insecure_http=True)
    hops.followed_or_not_followed(exc)


@pytest.mark.parametrize("keyed", [pytest.param(True, id="keyed"), pytest.param(False, id="unkeyed")])
@pytest.mark.parametrize("sender", ["http-client"])
def test_digest_authentication_through_a_loopback_redirect_is_refused_before_the_target(net, sender, keyed):
    digest = DigestSink()
    redirect = RedirectSink(f"http://127.0.0.1:{digest.port}/landed")
    url = f"http://127.0.0.1:{redirect.port}/v1/ping"
    headers = {"X-Api-Key": KEY} if keyed else {}
    try:
        session = FuturesSession()
        session.auth = requests.auth.HTTPDigestAuth("user", "pass")
        client = HttpClient(base_url=url, session=session, default_headers=headers)
        try:
            # 0.9.0 does not follow a redirect of a request that may carry a key (a callable auth counts as one):
            # the redirect target receives nothing, with or without a key header.
            with pytest.raises(KeyedRedirectRefusedError):
                client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1, timeout=3))
        finally:
            session.close()
        assert digest.marker_bytes() == 0 and digest.digest_ok == 0
        assert digest.connections == 0
    finally:
        digest.close()
        redirect.close()
