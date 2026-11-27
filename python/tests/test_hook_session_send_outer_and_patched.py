"""Sends through ``session.send`` by a response hook, for the session object given to the client, and the
``Session.send`` that applies to a session after the SDK has sent through it.

* A ``FuturesSession`` that wraps another session (``FuturesSession(session=inner)``) is the session given to the
  client; a hook of the inner session sends a keyed copy of the request through the outer session's ``send``.
* ``send`` read from the session after it is given to the client, and before the client's first request, is the
  ``send`` a later hook calls.
* ``requests.Session.send`` replaced on the class (as ``unittest.mock.patch`` and request mocking libraries do)
  after the client's first request applies to the client's later requests.

Listeners are on the loopback interface; ``plain.example.test`` resolves to it through the lookup shim of
``test_plain_http_key_guards``. Each case reads the connections and marker bytes at the target and the proxy.
"""

from __future__ import annotations

from unittest import mock

import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from tests.test_hook_session_send_is_judged import KEYED, Resend, _nothing_at_target_or_proxy, _report
from tests.test_keyed_request_paths import ok, sites  # noqa: F401
from tests.test_plain_http_key_guards import PLAIN, _attempt, net, refused  # noqa: F401


def _config(origin: str) -> RequestConfig:
    return RequestConfig(method=HttpMethod.GET, url=origin + "/v1/ping", retry_attempts=1, timeout=3)


def test_hook_send_through_the_outer_session_given_to_the_client_is_refused(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    inner = requests.Session()
    outer = FuturesSession(session=inner)
    hook = Resend(f"http://{PLAIN}:{net.target.port}/v1/ping")
    hook.session = outer
    inner.hooks["response"].append(hook)
    client = HttpClient(base_url=origin.base, session=outer, default_headers=dict(KEYED))
    exc = _attempt(lambda: client.request(_config(origin.base)))
    _nothing_at_target_or_proxy(net, origin, hook)
    refused(exc, ValueError)


def test_hook_send_through_a_send_read_before_the_first_request_is_refused(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = FuturesSession()
    client = HttpClient(base_url=origin.base, session=session, default_headers=dict(KEYED))
    early_send = session.send
    hook = Resend(f"http://{PLAIN}:{net.target.port}/v1/ping")

    class Early:
        send = staticmethod(early_send)

    hook.session = Early
    session.hooks["response"].append(hook)
    exc = _attempt(lambda: client.request(_config(origin.base)))
    _nothing_at_target_or_proxy(net, origin, hook)
    refused(exc, ValueError)


def test_session_send_replaced_on_the_class_applies_after_the_first_request(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = FuturesSession()
    client = HttpClient(base_url=origin.base, session=session, default_headers=dict(KEYED))
    first = client.request(_config(origin.base))
    assert first.status_code == 200
    connections = origin.connections

    answer = requests.Response()
    answer.status_code = 299
    answer._content = b"{}"
    answer.url = origin.base + "/v1/ping"
    with mock.patch.object(requests.Session, "send", autospec=True, return_value=answer) as replaced:
        second = client.request(_config(origin.base))
    assert (replaced.call_count, second.status_code, origin.connections - connections) == (1, 299, 0), (
        replaced.call_count,
        second.status_code,
        origin.connections - connections,
    )
