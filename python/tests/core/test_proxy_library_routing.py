"""With the plain-HTTP opt-in, a request counts as proxied when the library that sends it routes it through a proxy
or when CPython's ``proxy_bypass_environment`` does. The proxies here are loopback listeners and addresses nothing
connects to; the target hosts are reserved names. A ``requests`` session the caller passes to the legacy client is
judged by the routing of ``requests`` itself (0.8.1), and those checks map the target host to a loopback listener."""

from __future__ import annotations

import itertools
from urllib.request import proxy_bypass_environment

import httpx
import pytest

from fi._core.http_security import env_proxied, httpx_client_proxied, plaintext_decision, requests_session_proxied
from fi._credentials import Credentials
from fi._http import LazyKeyAuth
from fi.errors import ConfigurationError

from tests.experiments.unit.test_plaintext_measured_sends import rig  # noqa: F401

PROXY = "http://127.0.0.1:3128"
TARGET = "http://example.com"
KEY = "key-not-a-secret"
SECRET = "secret-not-a-secret"
NAMES = ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP")


@pytest.fixture
def clean_env(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def _cpython_proxied(url: str) -> bool:
    from urllib.parse import urlsplit

    netloc = urlsplit(url).netloc.rsplit("@", 1)[-1]
    return not proxy_bypass_environment(netloc)


def test_a_library_that_proxies_a_host_the_no_proxy_rule_exempts_is_refused(clean_env):
    clean_env.setenv("HTTP_PROXY", PROXY)
    clean_env.setenv("NO_PROXY", ".example.com")
    clean_env.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert env_proxied("http://example.com/") is True
    decision = plaintext_decision("http://example.com/")
    assert (decision.allowed, decision.reason) == (False, "env_proxy")


def test_the_explicit_environment_is_read_by_the_library_routers():
    env = {"HTTP_PROXY": PROXY, "NO_PROXY": ".example.com", "FI_ALLOW_INSECURE_HTTP": "1"}
    assert plaintext_decision("http://example.com/", environ=env).reason == "env_proxy"


def _send_with_legacy_client(rig):
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig
    from requests_futures.sessions import FuturesSession

    rig.env(HTTP_PROXY="http://127.0.0.1:{a}", FI_ALLOW_INSECURE_HTTP="1")
    base = f"{TARGET}:{rig.target.port}"
    with FuturesSession() as session:
        client = APIKeyAuth(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, session=session)
        return client.request(RequestConfig(method=HttpMethod.GET, url=base + "/x", retry_attempts=1, timeout=2))


def test_a_legacy_client_sends_direct_with_a_requests_dot_suffix_exemption(rig):
    rig.env(NO_PROXY=".example.com")
    assert _send_with_legacy_client(rig).status_code == 200
    received = b"".join(rig.target.data)
    assert KEY.encode() in received and SECRET.encode() in received
    assert rig.a.connections == 0 and not rig.a.data


def test_a_legacy_client_with_an_environment_proxy_and_no_exemption_is_refused(rig):
    with pytest.raises(ConfigurationError) as error:
        _send_with_legacy_client(rig)
    assert error.value.code == "KEYED_PROXY_REFUSED"
    assert rig.target.connections == rig.a.connections == 0
    assert not rig.target.data and not rig.a.data


def test_a_port_is_compared_as_written(clean_env):
    clean_env.setenv("HTTP_PROXY", PROXY)
    clean_env.setenv("NO_PROXY", "example.com:8")
    assert env_proxied("http://example.com:08/") is True


def test_a_trailing_dot_is_kept_for_the_no_proxy_match(clean_env):
    clean_env.setenv("HTTP_PROXY", PROXY)
    clean_env.setenv("NO_PROXY", "example.com")
    assert env_proxied("http://example.com./") is True


def test_an_empty_lowercase_no_proxy_wins(clean_env):
    clean_env.setenv("HTTP_PROXY", PROXY)
    clean_env.setenv("no_proxy", "")
    clean_env.setenv("NO_PROXY", "example.com")
    assert env_proxied("http://example.com/") is True


NO_PROXY_VALUES = ["*", "example.com", ".example.com", "example.com:8", "example.com:08", "example.com:80", "ample.com",
                   "other.org,example.com", " example.com ", "example.com.", "..example.com", "192.0.2.3", "2.3",
                   "[2001:db8::1]", "[2001:db8::1]:8080", "*.example.com", "xn--bcher-kva.example"]
URLS = ["http://example.com/", "http://example.com:8/", "http://example.com:08/", "http://example.com:80/",
        "http://api.example.com/", "http://EXAMPLE.com./", "http://example.com.:8/", "http://192.0.2.3/",
        "http://[2001:db8::1]/", "http://[2001:db8::1]:8080/"]


@pytest.mark.parametrize("no_proxy,url", list(itertools.product(NO_PROXY_VALUES, URLS)))
@pytest.mark.parametrize("lower_first", [False, True])
def test_a_request_the_standard_library_routes_is_never_called_unproxied(clean_env, no_proxy, url, lower_first):
    clean_env.setenv("HTTP_PROXY", PROXY)
    if lower_first:
        clean_env.setenv("no_proxy", "")
    clean_env.setenv("NO_PROXY", no_proxy)
    if _cpython_proxied(url):
        assert env_proxied(url) is True


def test_a_client_whose_auth_runs_deep_in_the_stack_is_checked(clean_env):
    clean_env.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    creds = Credentials(api_key=KEY, secret_key=SECRET, base_url=TARGET, keys_source="argument", base_url_source="argument")
    inner = LazyKeyAuth(lambda: creds)

    class Deep(httpx.Auth):
        def auth_flow(self, request):
            def layer(n):
                if n == 0:
                    yield from inner.auth_flow(request)
                else:
                    yield from layer(n - 1)

            yield from layer(14)

    with httpx.Client(proxy="http://127.0.0.1:9", auth=Deep()) as client:
        with pytest.raises(ConfigurationError) as error:
            client.get(TARGET + "/v1/x")
    assert error.value.code == "KEYED_PROXY_REFUSED"


class OpaqueTransport(httpx.BaseTransport):
    def handle_request(self, request):  # pragma: no cover - construction does not send a request
        return httpx.Response(200)


def test_a_custom_transport_that_cannot_be_inspected_counts_as_proxied():
    with httpx.Client(transport=OpaqueTransport()) as client:
        assert httpx_client_proxied(client, TARGET + "/x") is True


def test_a_wrapper_around_a_proxy_transport_is_seen_through():
    class Wrapper(httpx.BaseTransport):
        def __init__(self, inner):
            self.something_else = inner

        def handle_request(self, request):  # pragma: no cover
            return httpx.Response(200)

    with httpx.Client(transport=Wrapper(httpx.HTTPTransport(proxy="http://127.0.0.1:9"))) as client:
        assert httpx_client_proxied(client, TARGET + "/x") is True
    with httpx.Client(transport=Wrapper(httpx.HTTPTransport())) as client:
        assert httpx_client_proxied(client, TARGET + "/x") is False


def test_a_client_that_fails_to_answer_counts_as_proxied():
    class Broken:
        def _transport_for_url(self, url):
            raise RuntimeError("no")

    assert httpx_client_proxied(Broken(), TARGET + "/x") is True


def test_a_session_adapter_that_is_not_an_http_adapter_counts_as_proxied():
    import requests

    class Odd(requests.adapters.BaseAdapter):
        def send(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError

        def close(self):  # pragma: no cover
            pass

    session = requests.Session()
    session.mount("http://", Odd())
    assert requests_session_proxied(session, TARGET + "/x") is True


def test_a_proxy_manager_cached_by_requests_own_adapter_is_not_read(clean_env):
    # requests' own adapter uses a cached proxy manager only for a request that selects that proxy (0.8.1 sends).
    import requests

    session = requests.Session()
    session.get_adapter(TARGET).proxy_manager["http://127.0.0.1:9"] = object()
    assert requests_session_proxied(session, TARGET + "/x") is False
    session.proxies = {"http": "http://127.0.0.1:9"}
    assert requests_session_proxied(session, TARGET + "/x") is True


def test_a_plain_session_is_not_proxied(clean_env):
    import requests

    assert requests_session_proxied(requests.Session(), TARGET + "/x") is False


@pytest.mark.parametrize("url", [
    "http://example.com\\@127.0.0.1/", "http://example.com%5C@127.0.0.1/", "http://example.com%5c@127.0.0.1/",
    "http://127.0.0.1/@example.com", "http://127.0.0.1/p?x=@example.com", "http://127.0.0.1/p#@example.com",
    "http:///x", "http://", "http://:80/", "http://user@/x",
])
def test_a_url_whose_written_and_parsed_host_differ_or_that_has_no_host_is_refused(url):
    decision = plaintext_decision(url, allow_insecure_http=True, environ={})
    assert decision.allowed is False


def test_the_final_header_set_of_a_session_is_the_one_checked(clean_env):
    from fi.api.auth import HttpClient
    from fi.api.types import HttpMethod, RequestConfig
    from requests_futures.sessions import FuturesSession

    session = FuturesSession()
    session.headers["X-Api-Key"] = KEY
    client = HttpClient(base_url=TARGET, session=session)
    with pytest.raises(ConfigurationError) as error:
        client.request(RequestConfig(method=HttpMethod.GET, url=TARGET + "/x", headers={}, retry_attempts=1, timeout=2))
    assert error.value.code == "insecure_http_origin"


def test_an_auth_flow_run_with_no_client_on_the_stack_counts_as_proxied(clean_env):
    clean_env.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    creds = Credentials(api_key=KEY, secret_key=SECRET, base_url=TARGET, keys_source="argument", base_url_source="argument")
    with pytest.raises(ConfigurationError):
        next(LazyKeyAuth(lambda: creds).auth_flow(httpx.Request("GET", TARGET + "/x")))
