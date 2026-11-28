"""A request decides from its final headers: a Future AGI key that reaches it only through a header (the client's
``default_headers``, the call's own headers, a caller session's ``headers``, any letter case of ``X-Api-Key`` /
``X-Secret-Key`` / ``Authorization``, or a header whose value holds ``FI_API_KEY`` / ``FI_SECRET_KEY``) is sent under the
plain-http, proxy and redirect rules of a key the client resolved itself.

Host names resolve to the loopback address (``getaddrinfo`` is replaced for the test); the listeners count raw marker
bytes and connections at the target, at a ``CONNECT``-aware proxy sink and at a redirect target.
"""

import base64
import re
import socket
import types

import pytest
from requests.auth import HTTPBasicAuth
from requests.exceptions import TooManyRedirects

from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV, require_endpoint_with_keys, require_secure_credential_headers
from fi._core.proxy_routing import carries_credentials
from fi._keyed_errors import KeyedRedirectRefusedError
from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import ConfigurationError
from tests.experiments.unit.oracle_probe import KEY, SECRET, Sink

NAMES = ("FI_ALLOW_INSECURE_HTTP", "FI_API_KEY", "FI_SECRET_KEY", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy",
         "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy")
MARKER = KEY.decode()
OTHER = SECRET.decode()


def wire_count(sink):
    """Marker occurrences a listener received: the raw bytes, and the marker inside a Basic credential, decoded."""
    blob = b"".join(sink.data)
    found = sink.marker_bytes
    for token in re.findall(rb"(?i)authorization: basic ([A-Za-z0-9+/=]+)", blob):
        try:
            decoded = base64.b64decode(token)
        except ValueError:
            continue
        found += decoded.count(KEY) + decoded.count(SECRET)
    return found


class Rig:
    def __init__(self):
        self.target = Sink(False)
        self.proxy = Sink(True)
        self.landing = Sink(False)
        self.redirect_same = Sink(
            False, reply=b"HTTP/1.1 302 Found\r\nLocation: /next\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        )
        self.redirect_to = Sink(False, redirect=f"http://elsewhere.test:{self.landing.port}/next")
        self.sinks = [self.target, self.proxy, self.landing, self.redirect_same, self.redirect_to]

    def bytes(self):
        return sum(wire_count(sink) for sink in self.sinks)

    def connections(self):
        return sum(sink.connections for sink in self.sinks)

    def close(self):
        for sink in self.sinks:
            sink.close()


@pytest.fixture
def rig(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str) and name not in ("localhost",) and not name.replace(".", "").isdigit() and ":" not in name:
            host = "127.0.0.1"
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    from fi.api import auth

    monkeypatch.setattr(auth, "time", types.SimpleNamespace(sleep=lambda seconds: None))
    made = Rig()
    yield made
    made.close()


def remote(sink):
    return f"http://plain.example.test:{sink.port}"


def caller_session():
    from requests_futures.sessions import FuturesSession

    from fi.utils.executor import BoundedExecutor

    return FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1))


def env_key(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", MARKER)


# Each sender hands a Future AGI key to the request through a header only; none of them is the client's own key pair.
def default_headers(headers):
    return lambda base, monkeypatch: (HttpClient(base_url=base, default_headers=headers), {})


def per_call(headers):
    return lambda base, monkeypatch: (HttpClient(base_url=base), headers)


def on_session(headers):
    def make(base, monkeypatch):
        session = caller_session()
        session.headers.update(headers)
        return HttpClient(base_url=base, session=session), {}

    return make


def on_session_with(configure):
    def make(base, monkeypatch):
        session = caller_session()
        configure(session)
        return HttpClient(base_url=base, session=session), {}

    return make


def on_inner_session(configure):
    """A caller session that hands its requests to another session: the inner one holds the settings."""
    def make(base, monkeypatch):
        import requests

        from requests_futures.sessions import FuturesSession

        from fi.utils.executor import BoundedExecutor

        inner = requests.Session()
        configure(inner)
        outer = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=inner)
        return HttpClient(base_url=base, session=outer), {}

    return make


def _nested_session(base):
    """A ``FuturesSession`` that hands its requests to another ``FuturesSession``, which hands them to the session that holds the key."""
    import requests
    from requests_futures.sessions import FuturesSession

    from fi.utils.executor import BoundedExecutor

    innermost = requests.Session()
    innermost.headers.update({"X-Api-Key": MARKER})
    middle = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=innermost)
    outer = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=middle)
    return HttpClient(base_url=base, session=outer), {}


def with_env_key(make):
    def wrapped(base, monkeypatch):
        env_key(monkeypatch)
        return make(base, monkeypatch)

    return wrapped


SDK_BUILT = {
    "default_headers X-Api-Key": default_headers({"X-Api-Key": MARKER}),
    "default_headers in another letter case": default_headers({"x-SECRET-key": MARKER}),
    "default_headers Authorization Bearer": default_headers({"Authorization": f"Bearer {MARKER}"}),
    "default_headers value holding the environment key": with_env_key(default_headers({"X-Trace": f"pre-{MARKER}-post"})),
    "per-call X-Api-Key": per_call({"X-Api-Key": MARKER}),
    "per-call in another letter case": per_call({"X-SECRET-KEY": MARKER}),
    "per-call Authorization Bearer": per_call({"authorization": f"Bearer {MARKER}"}),
    "per-call value holding the environment key": with_env_key(per_call({"X-Trace": MARKER})),
}
CALLER = {
    "session headers X-Api-Key": on_session({"X-Api-Key": MARKER}),
    "session headers in another letter case": on_session({"x-secret-key": MARKER}),
    "session headers Authorization Bearer": on_session({"Authorization": f"Bearer {MARKER}"}),
    "session headers value holding the environment key": with_env_key(on_session({"X-Trace": MARKER})),
}


def key_hook(request):
    request.headers["X-Api-Key"] = MARKER
    return request


def _set_auth(auth):
    def configure(session):
        session.auth = auth

    return configure


def _set_cookie(session):
    session.cookies.set("sid", MARKER)


def _set_bytes_name(name):
    def configure(session):
        session.headers[name] = MARKER

    return configure


CALLER_WIRE = {
    "session.auth tuple": on_session_with(_set_auth(("user", MARKER))),
    "session.auth HTTPBasicAuth": on_session_with(_set_auth(HTTPBasicAuth("user", MARKER))),
    "session.auth hook setting X-Api-Key": on_session_with(_set_auth(key_hook)),
    "session cookie holding the environment key": with_env_key(on_session_with(_set_cookie)),
    "session headers with a bytes name": on_session_with(_set_bytes_name(b"X-Api-Key")),
    "session headers with a padded name": on_session_with(_set_bytes_name(" x-api-key")),
    "session headers with an underscore name": on_session_with(_set_bytes_name("x_api_key")),
    "nested inner session headers X-Api-Key": lambda base, monkeypatch: _nested_session(base),
    "inner session auth tuple": on_inner_session(_set_auth(("user", MARKER))),
    "inner session auth hook setting X-Api-Key": on_inner_session(_set_auth(key_hook)),
    "inner session headers X-Api-Key": on_inner_session(lambda session: session.headers.update({"X-Api-Key": MARKER})),
    "inner session cookie holding the environment key": with_env_key(on_inner_session(_set_cookie)),
}


def send(make, base, monkeypatch):
    client, headers = make(base, monkeypatch)
    config = RequestConfig(method=HttpMethod.GET, url=f"{base}/probe", headers=headers, retry_attempts=1)
    try:
        return client.request(config)
    finally:
        client.close()


def outcome(make, base, monkeypatch):
    try:
        send(make, base, monkeypatch)
    except Exception as error:  # noqa: BLE001 - the kind of failure is what the tests read
        return error
    return None


def refused(error):
    return isinstance(error, ConfigurationError) and error.code == "insecure_http_origin"


ALL = {**SDK_BUILT, **CALLER, **CALLER_WIRE}


@pytest.mark.parametrize("sender", list(ALL))
def test_a_non_loopback_host_is_refused_without_the_opt_in(rig, monkeypatch, sender):
    error = outcome(ALL[sender], remote(rig.target), monkeypatch)
    assert refused(error), error
    assert MARKER not in str(error) and OTHER not in str(error)
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("value", ["true", "yes", "0", "", " 1", "1 ", "01"])
@pytest.mark.parametrize("sender", list(ALL))
def test_other_values_are_not_the_opt_in(rig, monkeypatch, sender, value):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, value)
    assert refused(outcome(ALL[sender], remote(rig.target), monkeypatch))
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("host", ["api.futureagi.com", "a.b.futureagi.com"])
@pytest.mark.parametrize("sender", list(ALL))
def test_a_future_agi_host_is_refused_whatever_the_opt_in(rig, monkeypatch, sender, host):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    error = outcome(ALL[sender], f"http://{host}:{rig.target.port}", monkeypatch)
    assert isinstance(error, ConfigurationError), error  # a Future AGI host has a code of its own
    assert rig.connections() == 0 and rig.bytes() == 0


def proxied(rig, monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(name, f"http://127.0.0.1:{rig.proxy.port}")


@pytest.mark.parametrize("sender", list(ALL))
def test_an_environment_proxy_without_the_opt_in_receives_nothing(rig, monkeypatch, sender):
    proxied(rig, monkeypatch)
    assert refused(outcome(ALL[sender], remote(rig.target), monkeypatch))
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("sender", list(SDK_BUILT))
def test_the_opt_in_sends_directly_to_the_target(rig, monkeypatch, sender):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    outcome(SDK_BUILT[sender], remote(rig.target), monkeypatch)
    assert rig.target.marker_bytes > 0
    assert rig.proxy.connections == 0


@pytest.mark.parametrize("sender", list(SDK_BUILT))
def test_the_opt_in_with_an_environment_proxy_sends_directly_to_the_target(rig, monkeypatch, sender):
    proxied(rig, monkeypatch)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    outcome(SDK_BUILT[sender], remote(rig.target), monkeypatch)
    assert rig.target.marker_bytes > 0
    assert rig.proxy.connections == 0


@pytest.mark.parametrize("sender", list(SDK_BUILT))
def test_a_same_origin_redirect_loop_hits_the_limit(rig, monkeypatch, sender):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    sink = rig.redirect_same
    with pytest.raises(TooManyRedirects, match=r"^Exceeded 5 redirects\.$"):
        send(SDK_BUILT[sender], remote(sink), monkeypatch)
    assert sink.connections == 6
    requests = re.findall(rb"(GET [^\r\n]+)\r\n(.*?)\r\n\r\n", b"".join(sink.data), re.DOTALL)
    assert [line for line, _ in requests] == [b"GET /probe HTTP/1.1"] + [b"GET /next HTTP/1.1"] * 5
    assert all(KEY in headers for _, headers in requests)


@pytest.mark.parametrize("sender", list(SDK_BUILT))
def test_a_cross_origin_redirect_is_not_followed(rig, monkeypatch, sender):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    sink = rig.redirect_to
    error = outcome(SDK_BUILT[sender], remote(sink), monkeypatch)
    assert isinstance(error, KeyedRedirectRefusedError), error
    assert sink.connections == 1
    assert rig.landing.connections == 0 and rig.landing.marker_bytes == 0


@pytest.mark.parametrize("sender", list(SDK_BUILT))
def test_a_loopback_host_is_sent_to_directly_with_an_environment_proxy(rig, monkeypatch, sender):
    proxied(rig, monkeypatch)
    outcome(SDK_BUILT[sender], f"http://localhost:{rig.target.port}", monkeypatch)
    assert rig.target.marker_bytes > 0
    assert rig.proxy.connections == 0


CONTROLS = {
    "no key header": default_headers({"X-Team": "blue"}),
    "an empty value": per_call({"X-Team": ""}),
    "a short environment value": lambda base, monkeypatch: (monkeypatch.setenv("FI_API_KEY", "abc"), default_headers({"X-Team": "abcdef"})(base, monkeypatch))[1],
}


@pytest.mark.parametrize("control", list(CONTROLS))
def test_a_request_with_no_key_header_goes_to_a_non_loopback_host_unchanged(rig, monkeypatch, control):
    error = outcome(CONTROLS[control], remote(rig.target), monkeypatch)
    assert not isinstance(error, ConfigurationError), error
    assert rig.target.connections == 1


# The shared decision, on its own.
@pytest.mark.parametrize("headers", [
    {"X-Api-Key": "v"}, {"x-secret-key": "v"}, {"AUTHORIZATION": "Bearer v"}, ["x-api-key"],
])
def test_a_credential_header_in_any_letter_case_is_a_key(headers):
    assert carries_credentials(headers) is True


@pytest.mark.parametrize("headers", [{}, None, {"Accept": "application/json"}, {"X-Team": "blue"}])
def test_other_headers_are_not_a_key(headers):
    assert carries_credentials(headers or {}) is False


def test_a_header_value_holding_an_environment_key_is_a_key(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    monkeypatch.setenv("FI_SECRET_KEY", OTHER)
    for value in (MARKER, f"pre-{MARKER}", f"{OTHER}-post"):
        assert carries_credentials({"X-Trace": value}) is True
        with pytest.raises(ConfigurationError) as caught:
            require_secure_credential_headers("http://remote.test", {"X-Trace": value})
        assert MARKER not in str(caught.value) and OTHER not in str(caught.value)
    assert carries_credentials({"X-Trace": "unrelated"}) is False
    require_secure_credential_headers("http://remote.test", {"X-Trace": "unrelated"})
    require_secure_credential_headers("https://remote.test", {"X-Trace": MARKER})
    require_secure_credential_headers("http://127.0.0.1", {"X-Trace": MARKER})


def test_a_short_environment_value_is_not_looked_for_inside_other_values(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "abc")
    assert carries_credentials({"X-Team": "abcdef"}) is False


def test_a_credential_header_with_an_empty_value_is_a_key():
    assert carries_credentials({"Authorization": ""}) is True


def test_the_environment_key_must_have_eight_characters_to_be_looked_for(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "abcdefgh")
    assert carries_credentials({"X-Team": "abcdefgh-team"}) is True
    monkeypatch.setenv("FI_API_KEY", "abcdefg")
    assert carries_credentials({"X-Team": "abcdefg-team"}) is False


def test_the_secret_key_of_the_environment_is_looked_for_too(monkeypatch):
    monkeypatch.setenv("FI_SECRET_KEY", OTHER)
    assert carries_credentials({"X-Trace": f"pre-{OTHER}"}) is True


def test_an_exporter_with_a_key_in_a_header_value_and_no_endpoint_is_refused(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    with pytest.raises(ConfigurationError) as caught:
        require_endpoint_with_keys("", {"X-Trace": MARKER})
    assert caught.value.code == "insecure_http_origin" and MARKER not in str(caught.value)
    require_endpoint_with_keys("", {"X-Trace": "unrelated"})
    require_endpoint_with_keys("https://collector.test", {"X-Trace": MARKER})


# --- the forms a header set takes: pairs, bytes names, padded names, underscore names, containers ---------------------------

def _forms(name, value="v"):
    """One header (``name``, ``value``) in every container and spelling the senders are handed."""
    import httpx
    from requests.structures import CaseInsensitiveDict

    text = name.decode() if isinstance(name, bytes) else name
    raw = name if isinstance(name, bytes) else name.encode()
    return {
        "dict": {name: value},
        "dict with a bytes value": {name: value.encode()},
        "list of pairs": [(name, value)],
        "tuple of pairs": ((name, value),),
        "list of lists": [[name, value]],
        "list of bytes pairs": [(raw, value.encode())],
        "httpx.Headers": httpx.Headers([(raw, value.encode())]),
        "CaseInsensitiveDict": CaseInsensitiveDict({text: value}),
        "generator of pairs": (pair for pair in [(name, value)]),
    }


NAME_SPELLINGS = [
    "X-Api-Key", "x-secret-key", "AUTHORIZATION", b"X-Api-Key", b"x-secret-key", b"Authorization",
    " x-api-key", "x-api-key ", "\tAuthorization", "X_API_KEY", "x_secret_key", b"x_api_key", " X_Secret_Key ",
]


@pytest.mark.parametrize("spelling", NAME_SPELLINGS, ids=repr)
@pytest.mark.parametrize("form", list(_forms("X-Api-Key")))
def test_a_credential_header_is_a_key_in_every_container_and_spelling(spelling, form):
    assert carries_credentials(_forms(spelling)[form]) is True


@pytest.mark.parametrize("spelling", NAME_SPELLINGS, ids=repr)
@pytest.mark.parametrize("form", list(_forms("X-Api-Key")))
def test_a_credential_header_in_any_form_is_refused_over_plain_http(monkeypatch, spelling, form):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigurationError) as caught:
        require_secure_credential_headers("http://remote.test", _forms(spelling)[form])
    assert caught.value.code == "insecure_http_origin"
    require_secure_credential_headers("https://remote.test", _forms(spelling)[form])
    require_secure_credential_headers("http://127.0.0.1", _forms(spelling)[form])


@pytest.mark.parametrize("name", ["X-Team", b"X-Team", "accept", b"X-Api-Keys", "x-api-key-2", "my_x_api_key", "X_Team"], ids=repr)
@pytest.mark.parametrize("form", list(_forms("X-Team")))
def test_another_header_is_not_a_key_in_any_form(monkeypatch, name, form):
    for variable in NAMES:
        monkeypatch.delenv(variable, raising=False)
    assert carries_credentials(_forms(name)[form]) is False
    require_secure_credential_headers("http://remote.test", _forms(name)[form])


@pytest.mark.parametrize("form", list(_forms("X-Trace")))
def test_a_header_value_holding_an_environment_key_is_a_key_in_every_form(monkeypatch, form):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    for value in (MARKER, f"pre-{MARKER}-post"):
        assert carries_credentials(_forms("X-Trace", value)[form]) is True
        assert carries_credentials(_forms(b"X-Trace", value)[form]) is True
    assert carries_credentials(_forms("X-Trace", "unrelated")[form]) is False


@pytest.mark.parametrize("spelling", ["X-Api-Key", b"x-secret-key", " X_API_KEY", "x_secret_key "], ids=repr)
@pytest.mark.parametrize("form", list(_forms("X-Api-Key")))
def test_the_exporter_header_checks_read_every_form(spelling, form):
    from fi._otlp_headers import carries_final_credentials, carries_key_headers, carries_sdk_keys

    assert carries_key_headers(_forms(spelling)[form]) is True
    assert carries_sdk_keys(_forms(spelling)[form]) is True
    assert carries_final_credentials(_forms(spelling)[form]) is True


# The session the SDK builds for keyed sends (LoopbackDirectSession): a plain-http request whose final headers hold a key
# goes straight to its host and a redirect is not followed, whatever form the key header was handed over in.
SEND_FORMS = {
    "a dict": lambda: {"X-Api-Key": MARKER},
    "a bytes name": lambda: {b"X-Api-Key": MARKER},
    "a bytes value": lambda: {"X-Api-Key": MARKER.encode()},
    "an underscore name": lambda: {"X_Api_Key": MARKER},
    "an Authorization value": lambda: {"Authorization": f"Bearer {MARKER}"},
}


def _direct_session():
    from fi._core.requests_session import LoopbackDirectSession

    return LoopbackDirectSession()


@pytest.mark.parametrize("form", list(SEND_FORMS))
def test_a_loopback_direct_session_sends_a_keyed_plain_request_straight_to_its_host(rig, monkeypatch, form):
    proxied(rig, monkeypatch)
    with _direct_session() as session:
        session.get(f"{remote(rig.target)}/probe", headers=SEND_FORMS[form](), timeout=3)
    assert wire_count(rig.target) > 0
    assert rig.proxy.connections == 0


@pytest.mark.parametrize("form", list(SEND_FORMS))
def test_a_loopback_direct_session_does_not_follow_a_redirect_of_a_keyed_request(rig, monkeypatch, form):
    for sink in (rig.redirect_same, rig.redirect_to):
        with _direct_session() as session:
            with pytest.raises(KeyedRedirectRefusedError):
                session.get(f"{remote(sink)}/probe", headers=SEND_FORMS[form](), timeout=3, allow_redirects=True)
        assert sink.connections == 1
    assert rig.landing.connections == 0 and rig.landing.marker_bytes == 0


def test_a_loopback_direct_session_keeps_the_proxy_for_a_request_without_a_key(rig, monkeypatch):
    proxied(rig, monkeypatch)
    with _direct_session() as session:
        session.get(f"{remote(rig.target)}/probe", headers={"X-Team": "blue"}, timeout=3)
    assert rig.proxy.connections == 1 and rig.target.connections == 0


@pytest.mark.parametrize("form", ["a session auth tuple", "a session auth hook", "a session cookie"])
def test_a_loopback_direct_session_judges_the_request_after_its_own_auth_and_cookies(rig, monkeypatch, form):
    proxied(rig, monkeypatch)
    monkeypatch.setenv("FI_API_KEY", MARKER)
    with _direct_session() as session:
        if form == "a session auth tuple":
            session.auth = ("user", MARKER)
        elif form == "a session auth hook":
            session.auth = key_hook
        else:
            session.cookies.set("sid", MARKER)
        session.get(f"{remote(rig.target)}/probe", timeout=3)
    assert wire_count(rig.target) > 0
    assert rig.proxy.connections == 0


# The exporters the evaluations tracer builds: the header forms reach the same plain-http decision.
EXPORTER_HEADERS = {
    "a dict": lambda: {"X-Api-Key": MARKER},
    "a bytes name": lambda: {b"X-Api-Key": MARKER},
    "a padded name": lambda: {" x-secret-key": MARKER},
    "an underscore name": lambda: {"x_api_key": MARKER},
    "a list of pairs": lambda: [("x-api-key", MARKER)],
    "a tuple of pairs": lambda: (("x-api-key", MARKER),),
    "a tuple of bytes pairs": lambda: ((b"x-secret-key", MARKER.encode()),),
}
# What the OpenTelemetry exporter classes accept as headers (the others fail inside the library, after the SDK's own check).
BUILDS = {"OTLP_HTTP": ["a dict", "a bytes name", "a padded name", "an underscore name"],
          "OTLP_GRPC": ["a dict", "a bytes name", "a padded name", "an underscore name", "a tuple of pairs"]}


def _exporter(kind, endpoint, headers):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType

    return _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint, headers=headers))


@pytest.mark.parametrize("form", list(EXPORTER_HEADERS))
@pytest.mark.parametrize("kind", ["OTLP_HTTP", "OTLP_GRPC", "ARIZE", "PHOENIX", "LANGFUSE"])
def test_an_exporter_with_a_key_in_any_header_form_is_refused_for_a_plain_remote_endpoint(rig, kind, form):
    endpoint = "http://plain.example.test:4317" if kind == "OTLP_GRPC" else "http://plain.example.test:4318/v1/traces"
    with pytest.raises(ConfigurationError) as caught:
        _exporter(kind, endpoint, EXPORTER_HEADERS[form]())
    assert caught.value.code == "insecure_http_origin" and MARKER not in str(caught.value)
    assert rig.connections() == 0


@pytest.mark.parametrize("kind,form", [(kind, form) for kind, forms in BUILDS.items() for form in forms])
def test_an_exporter_with_a_key_in_any_header_form_is_built_for_a_loopback_endpoint(rig, kind, form):
    endpoint = "http://127.0.0.1:4317" if kind == "OTLP_GRPC" else "http://127.0.0.1:9/v1/traces"
    assert _exporter(kind, endpoint, EXPORTER_HEADERS[form]()) is not None


@pytest.mark.parametrize("form", ["a dict", "a bytes name", "an underscore name"])
def test_the_http_exporter_with_the_opt_in_sends_a_key_in_any_header_form_directly(rig, monkeypatch, form):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SpanExportResult

    proxied(rig, monkeypatch)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    exporter = _exporter("OTLP_HTTP", f"{remote(rig.target)}/v1/traces", EXPORTER_HEADERS[form]())
    span = TracerProvider().get_tracer("t").start_span("s")
    span.end()
    exporter.export([span])
    assert wire_count(rig.target) > 0
    assert rig.proxy.connections == 0


@pytest.mark.parametrize("sender", list(CALLER_WIRE))
def test_the_opt_in_sends_a_caller_sessions_auth_and_cookies_directly_to_the_target(rig, monkeypatch, sender):
    """A key reaches the target in the raw bytes, or inside a Basic credential that the listener decodes."""
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    outcome(CALLER_WIRE[sender], remote(rig.target), monkeypatch)
    assert rig.proxy.connections == 0
    # The library refuses a header name that starts with white space, after the SDK's check, and a session nested twice answers
    # with a future of a future: its send ends on the executor's thread after the call has returned.
    if "padded" not in sender and "nested" not in sender:
        assert wire_count(rig.target) > 0


def test_a_file_the_caller_uploads_is_read_once_by_the_send(rig):
    import io

    client = HttpClient(base_url=f"http://127.0.0.1:{rig.target.port}", default_headers={"X-Api-Key": MARKER})
    config = RequestConfig(method=HttpMethod.POST, url=f"http://127.0.0.1:{rig.target.port}/up", retry_attempts=1,
                           files={"file": ("a.csv", io.BytesIO(b"upload-body-bytes\n"))})
    try:
        client.request(config)
    finally:
        client.close()
    assert b"upload-body-bytes" in b"".join(rig.target.data)


def test_a_callable_auth_runs_once_and_its_key_is_judged_and_sent(rig, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    calls = []

    def hook(request):
        calls.append(1)
        return key_hook(request)

    outcome(on_session_with(_set_auth(hook)), remote(rig.target), monkeypatch)
    assert len(calls) == 1 and wire_count(rig.target) > 0
