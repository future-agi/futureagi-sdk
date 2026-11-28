"""Keyed sends the 0.8.1 line refuses: a proxy transport held by a caller's transport
wrapper in a container, a loopback host written with a non-ASCII port, and a send a response hook makes through the
adapter (``response.connection``). Each case reads the connections and the marker bytes at the target and the proxy of
the ``net`` fixture of ``test_plain_http_key_guards``; ``plain.example.test`` resolves to the loopback interface."""

from __future__ import annotations

from contextlib import ExitStack

import httpx
import pytest
from requests_futures.sessions import FuturesSession

from fi._core.proxy_routing import httpx_client_proxied
from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import KeyedProxyRefusedError
from fi.platform import APIConnectionError, Client
from tests.test_keyed_request_paths import ok, sites  # noqa: F401
from tests.test_plain_http_key_guards import KEY, PLAIN, SECRET, _attempt, net, refused  # noqa: F401


class Wrapper(httpx.BaseTransport):
    """A direct transport with an optional route held in a list, dict, or client's mounts."""

    def __init__(self, direct: httpx.BaseTransport) -> None:
        self.direct = direct
        self.routes: list[httpx.BaseTransport] | dict[str, httpx.BaseTransport] | httpx.Client | None = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if isinstance(self.routes, httpx.Client):
            return self.routes.send(request, follow_redirects=False)
        if isinstance(self.routes, list):
            return self.routes[0].handle_request(request)
        if isinstance(self.routes, dict):
            return self.routes["http"].handle_request(request)
        return self.direct.handle_request(request)


def _platform(base: str, http_client=None):
    return _attempt(lambda: Client(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3,
                                   http_client=http_client).request("GET", "/v1/ping", unwrap=None))


@pytest.mark.parametrize("held", ["list", "dict", "client-mount"])
def test_a_proxy_transport_held_in_a_container_is_read_as_a_proxy(net, held):
    base = f"http://127.0.0.1:{net.target.port}"
    with ExitStack() as stack:
        wrapper = Wrapper(stack.enter_context(httpx.HTTPTransport()))
        client = stack.enter_context(httpx.Client(transport=wrapper, trust_env=False))
        # The direct transport keeps the wrapper inspectable without the selected container.
        assert not httpx_client_proxied(client, base)
        proxy = httpx.HTTPTransport(proxy=f"http://127.0.0.1:{net.proxy.port}")
        if held == "client-mount":
            wrapper.routes = stack.enter_context(httpx.Client(mounts={"http://": proxy}, trust_env=False))
        else:
            stack.enter_context(proxy)
            wrapper.routes = [proxy] if held == "list" else {"http": proxy}
        exc = _platform(base, client)
    net.nothing_sent()
    refused(exc, KeyedProxyRefusedError, code="KEYED_PROXY_REFUSED")


def test_a_loopback_host_with_a_non_ascii_port_is_refused(net):
    port = "".join(chr(0xFF10 + int(digit)) for digit in str(net.target.port))  # fullwidth digits
    exc = _platform(f"http://127.0.0.1:{port}")
    net.nothing_sent()
    assert exc is not None


def _resend_through_the_adapter(url: str):
    def hook(r, **kwargs):
        if getattr(r.request, "_resent", False):
            return r
        prep = r.request.copy()
        prep.url = url
        prep._resent = True
        return r.connection.send(prep, **kwargs)

    return hook


def test_a_hook_send_through_the_adapter_to_a_named_plain_http_host_is_refused(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = FuturesSession()
    session.trust_env = False
    session.hooks["response"].append(_resend_through_the_adapter(f"http://{PLAIN}:{net.target.port}/v1/ping"))
    client = HttpClient(base_url=origin.base, session=session, default_headers={"X-Api-Key": KEY, "X-Secret-Key": SECRET})
    exc = _attempt(lambda: client.request(RequestConfig(method=HttpMethod.GET, url=origin.base + "/v1/ping",
                                                        retry_attempts=1, timeout=3)))
    net.nothing_sent()
    refused(exc, ValueError)


def test_a_hook_send_through_the_adapter_to_loopback_is_sent(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = FuturesSession()
    session.trust_env = False
    session.hooks["response"].append(_resend_through_the_adapter(f"http://127.0.0.1:{net.target.port}/v1/ping"))
    client = HttpClient(base_url=origin.base, session=session, default_headers={"X-Api-Key": KEY, "X-Secret-Key": SECRET})
    _attempt(lambda: client.request(RequestConfig(method=HttpMethod.GET, url=origin.base + "/v1/ping",
                                                  retry_attempts=1, timeout=3)))
    sent = net.target.marker_bytes()
    # Exactly one send reaches the target: the hook's resend through the adapter, made once.
    assert (net.target.connections, sent > 0) == (1, True), net.report()
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), net.report()


def test_a_loopback_host_with_whitespace_before_the_port_is_refused(net):
    exc = _platform(f"http://127.0.0.1: {net.target.port}")
    net.nothing_sent()
    assert exc is not None


def test_the_sdk_transport_class_with_a_proxy_is_read_as_a_proxy(net):
    from fi._core.proxy_routing import SdkDirectTransport

    client = httpx.Client(base_url=f"http://127.0.0.1:{net.target.port}",
                          transport=SdkDirectTransport(proxy=f"http://127.0.0.1:{net.proxy.port}"), trust_env=False)
    exc = _platform("/", client)
    net.nothing_sent()
    refused(exc, ValueError)


def test_a_caller_https_base_with_user_info_is_not_judged_as_plain_http(net):
    schemes = []

    class RecordingTransport(httpx.HTTPTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            schemes.append(request.url.scheme)
            return super().handle_request(request)

    base_url = f"https://user:pass@127.0.0.1:{net.target.port}"
    with httpx.Client(base_url=base_url, transport=RecordingTransport(), trust_env=False) as client:
        exc = _platform("/", client)
    assert schemes == ["https"], repr(exc)
    assert net.target.connections == 1, net.report()
    # The listener accepts the connection but does not speak TLS.
    assert isinstance(exc, APIConnectionError), repr(exc)
