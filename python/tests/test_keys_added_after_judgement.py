"""Keys added to a request after it was judged: by a response hook that sends again, or inside a mounted adapter.

The first request carries no key, so it is not refused on its own. A key is added later:

* ``auth``: the session's authentication registers a response hook that answers a 401 challenge by sending the
  request again with ``X-Api-Key`` through ``r.connection.send`` (as ``HTTPDigestAuth.handle_401`` does);
* ``session-hook``: the same send again from ``session.hooks["response"]``;
* ``adapter``: a mounted ``HTTPAdapter`` subclass whose ``send`` adds ``X-Api-Key``.

Each case goes through ``HttpClient`` (``fi.api.auth``) and through ``_send_prepared``, the send used by the
knowledge base upload (``fi.kb.client``). Listeners run on the loopback interface and answer 401 to a request
without the marker key; ``plain.example.test`` resolves to them through the lookup shim of
``test_plain_http_key_guards`` (its ``net`` fixture applies here too), so no case reaches a real host. Each case
reads, at the target and at the proxy listener, the connections, the connections that carried the marker key and
the marker bytes.
"""

from __future__ import annotations

import socket

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient, _prepare, _send_prepared
from fi.api.types import HttpMethod, RequestConfig
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, Net, Sink, _attempt, _marker_forms, net, refused  # noqa: F401

PLAIN = "plain.example.test"
VARIANTS = ["auth", "session-hook", "adapter"]
RESEND_VARIANTS = ["auth", "session-hook"]


class ChallengeSink(Sink):
    """A :class:`Sink` that answers 401 with a challenge to a request without the marker key, and 200 to one with
    it. It also counts the connections whose bytes held the marker key."""

    def __init__(self, family: int = socket.AF_INET) -> None:
        self.keyed_connections = 0
        super().__init__(family)

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(0.4)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            keyed = any(form in data for form in _marker_forms(KEY, SECRET))
            with self._lock:
                self.raw += data
                self.keyed_connections += int(keyed)
            if keyed:
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
            else:
                conn.sendall(
                    b"HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: ApiKey realm=\"r\"\r\n"
                    b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                )
        except OSError:
            pass
        finally:
            conn.close()


class Sinks(Net):
    def report(self) -> str:
        return (
            f"target: {self.target.connections} connections, {self.target.keyed_connections} keyed, "
            f"{self.target.marker_bytes()} marker bytes; proxy: {self.proxy.connections} connections, "
            f"{self.proxy.keyed_connections} keyed, {self.proxy.marker_bytes()} marker bytes"
        )

    def nothing_sent(self) -> None:
        counts = (
            self.target.connections, self.target.keyed_connections, self.target.marker_bytes(),
            self.proxy.connections, self.proxy.keyed_connections, self.proxy.marker_bytes(),
        )
        assert counts == (0, 0, 0, 0, 0, 0), self.report()

    def no_key_through_proxy(self) -> None:
        assert (self.proxy.keyed_connections, self.proxy.marker_bytes()) == (0, 0), self.report()

    def delivered_direct(self) -> None:
        assert self.target.keyed_connections >= 1 and self.target.marker_bytes() > 0, self.report()
        self.no_key_through_proxy()


@pytest.fixture
def sinks(net):
    pair = Sinks(ChallengeSink(), ChallengeSink())
    yield pair
    pair.target.close()
    pair.proxy.close()


# ---------------------------------------------------------------------------------------------
# what adds the key
# ---------------------------------------------------------------------------------------------


def _send_again_with_key(r, **kwargs):
    """Answer a 401 by sending the request again with ``X-Api-Key``, as ``HTTPDigestAuth.handle_401`` does."""
    if r.status_code != 401 or "X-Api-Key" in r.request.headers:
        return r
    r.content
    r.close()
    prep = r.request.copy()
    prep.headers["X-Api-Key"] = KEY
    again = r.connection.send(prep, **kwargs)
    again.history.append(r)
    again.request = prep
    return again


class ChallengeAuth(requests.auth.AuthBase):
    def __call__(self, r):
        r.register_hook("response", _send_again_with_key)
        return r


class KeyAddingAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        request.headers["X-Api-Key"] = KEY
        return super().send(request, **kwargs)


def _session(cls, variant: str, *, trust_env: bool = True, proxies=None):
    session = cls()
    session.trust_env = trust_env
    if proxies:
        session.proxies.update(proxies)
    if variant == "auth":
        session.auth = ChallengeAuth()
    elif variant == "session-hook":
        session.hooks["response"].append(_send_again_with_key)
    elif variant == "adapter":
        adapter = KeyAddingAdapter()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    else:
        raise AssertionError(variant)
    return session


# ---------------------------------------------------------------------------------------------
# senders: each sends one request without a key to ``base`` + ``/v1/ping`` and returns the error it raised, if any
# ---------------------------------------------------------------------------------------------


def via_http_client(base: str, variant: str, *, allow_insecure_http=None, **session_kwargs):
    session = _session(FuturesSession, variant, **session_kwargs)
    client = HttpClient(base_url=base, session=session, default_headers={}, allow_insecure_http=allow_insecure_http)
    config = RequestConfig(method=HttpMethod.GET, url=base + "/v1/ping", retry_attempts=1, timeout=3)
    return _attempt(lambda: client.request(config))


def via_send_prepared(base: str, variant: str, *, allow_insecure_http=None, **session_kwargs):
    url = base + "/v1/ping"

    def send():
        with _session(requests.Session, variant, **session_kwargs) as session:
            prepared = _prepare(session, requests.Request(method="GET", url=url, headers={}), allow_insecure_http)
            _send_prepared(session, prepared, 3, allow_insecure_http, url=url)

    return _attempt(send)


SENDERS = [
    pytest.param(via_http_client, id="http-client"),
    pytest.param(via_send_prepared, id="send-prepared"),
]

PROXY_MODES = [
    pytest.param(True, id="trust-env-with-env-proxy"),
    pytest.param(False, id="no-trust-env"),
]


def _env_proxy(monkeypatch, sinks: Sinks) -> None:
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{sinks.proxy.port}")


# ---------------------------------------------------------------------------------------------
# plain http to a host that is not loopback, without the opt-in: refused before any connection
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("trust_env", PROXY_MODES)
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_after_judgement_to_a_named_plain_http_host_is_refused(monkeypatch, sinks, sender, variant, trust_env):
    _env_proxy(monkeypatch, sinks)
    exc = sender(f"http://{PLAIN}:{sinks.target.port}", variant, trust_env=trust_env)
    sinks.nothing_sent()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# a send again through ``r.connection`` to a loopback target with a proxy configured: direct or refused
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "proxy_source",
    [pytest.param("env", id="env-proxy"), pytest.param("session", id="session-proxy")],
)
@pytest.mark.parametrize("variant", RESEND_VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_send_again_to_loopback_never_carries_the_key_through_a_proxy(monkeypatch, sinks, sender, variant, proxy_source):
    proxy = f"http://127.0.0.1:{sinks.proxy.port}"
    if proxy_source == "env":
        monkeypatch.setenv("HTTP_PROXY", proxy)
        exc = sender(f"http://127.0.0.1:{sinks.target.port}", variant, trust_env=True)
    else:
        exc = sender(f"http://127.0.0.1:{sinks.target.port}", variant, trust_env=False, proxies={"http": proxy})
    sinks.no_key_through_proxy()
    if exc is None:
        sinks.delivered_direct()
    else:
        refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# controls: loopback, and the opt-in, still send the key directly
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_after_judgement_to_loopback_is_sent_directly(sinks, sender, variant):
    exc = sender(f"http://127.0.0.1:{sinks.target.port}", variant)
    assert exc is None, repr(exc)
    sinks.delivered_direct()


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_after_judgement_with_the_opt_in_is_sent_directly(sinks, sender, variant):
    exc = sender(f"http://{PLAIN}:{sinks.target.port}", variant, allow_insecure_http=True)
    assert exc is None, repr(exc)
    sinks.delivered_direct()


@pytest.mark.parametrize("variant", RESEND_VARIANTS)
@pytest.mark.parametrize("sender", SENDERS)
def test_key_added_after_judgement_with_the_opt_in_goes_past_an_environment_proxy(monkeypatch, sinks, sender, variant):
    _env_proxy(monkeypatch, sinks)
    exc = sender(f"http://{PLAIN}:{sinks.target.port}", variant, allow_insecure_http=True)
    sinks.no_key_through_proxy()
    if exc is None:
        sinks.delivered_direct()
    else:
        refused(exc, ValueError)
