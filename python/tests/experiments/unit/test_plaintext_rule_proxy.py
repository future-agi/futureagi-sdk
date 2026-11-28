"""Proxy settings and the plain-transport rule.

A transport the SDK builds for a plain send of its keys (the OTLP HTTP exporter's session, a gRPC channel, the evaluation
request's session) reaches its target directly, so the proxy settings of the environment do not decide whether the
opt-in applies: ``FI_ALLOW_INSECURE_HTTP`` does, alone.
"""

import pytest
import requests
import requests.adapters

from fi import _otlp_headers
from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401

CODE = "insecure_http_origin"
HOST = "selfhosted.example.test"
HTTP_TARGET = f"http://{HOST}:4318/tracer/v1/traces"
PROXY = "http://127.0.0.1:3128"
VARIABLES = ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy",
             "GRPC_PROXY", "grpc_proxy", "NO_PROXY", "no_proxy", "NO_GRPC_PROXY", "no_grpc_proxy")
SETTINGS = [
    {},
    {"HTTP_PROXY": PROXY},
    {"http_proxy": PROXY},
    {"ALL_PROXY": PROXY},
    {"all_proxy": PROXY},
    {"HTTPS_PROXY": PROXY},
    {"grpc_proxy": PROXY},
    {"https_proxy": PROXY},
    {"HTTP_PROXY": PROXY, "NO_PROXY": "*"},
    {"http_proxy": PROXY, "no_proxy": HOST},
    {"http_proxy": PROXY, "no_proxy": f"{HOST}:9999"},
    {"http_proxy": PROXY, "no_proxy": "192.0.2.0/24"},
    {"grpc_proxy": PROXY, "no_grpc_proxy": "other.example.test"},
    {"HTTP_PROXY": PROXY, "http_proxy": "http://127.0.0.1:3129"},
]


@pytest.fixture
def env(monkeypatch, clean_hosts):  # noqa: F811
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(_otlp_headers, "_PLAIN_OPT_IN_WARNED", True, raising=False)
    return monkeypatch


def decision(call):
    try:
        call()
    except ConfigurationError as refused:
        return refused.code
    return "build"


def http_decision():
    return decision(lambda: _otlp_headers.refuse_plain_http_futureagi(HTTP_TARGET, "FI_BASE_URL", keys=True))


def grpc_decision():
    return decision(lambda: _otlp_headers.grpc_plain_choice(f"{HOST}:4317", True))


@pytest.mark.parametrize("opt_in,expected", [(None, CODE), ("1", "build"), ("true", CODE), (" 1", CODE)])
@pytest.mark.parametrize("settings", SETTINGS)
def test_the_proxy_settings_do_not_decide_a_plain_send_the_sdk_builds(env, settings, opt_in, expected):
    for name, value in settings.items():
        env.setenv(name, value)
    if opt_in is not None:
        env.setenv("FI_ALLOW_INSECURE_HTTP", opt_in)
    assert http_decision() == expected
    assert grpc_decision() == expected


# --- a session the caller supplies ---------------------------------------------------------------------------

URL = f"http://{HOST}:4318/v1"


def stock():
    return requests.Session()


def with_proxies(**proxies):
    session = requests.Session()
    session.proxies = dict(proxies)
    return session


def without_env():
    session = requests.Session()
    session.trust_env = False
    return session


class OpaqueAdapter(requests.adapters.HTTPAdapter):
    pass


def opaque():
    session = requests.Session()
    session.mount("http://", OpaqueAdapter())
    return session


class Unreadable:
    """Not a session at all: its routing cannot be read."""


@pytest.mark.parametrize("settings,build,expected", [
    ({}, stock, False),
    ({"HTTP_PROXY": PROXY}, stock, True),
    ({"http_proxy": PROXY}, stock, True),
    ({"ALL_PROXY": PROXY}, stock, True),
    ({"all_proxy": PROXY}, stock, True),
    ({"HTTPS_PROXY": PROXY}, stock, False),
    ({"http_proxy": PROXY, "NO_PROXY": "*"}, stock, False),
    ({"http_proxy": PROXY, "NO_PROXY": HOST}, stock, False),
    ({"http_proxy": PROXY, "NO_PROXY": f"{HOST}:4318"}, stock, False),
    ({"http_proxy": PROXY, "NO_PROXY": f"{HOST}:9999"}, stock, True),
    ({"http_proxy": PROXY, "NO_PROXY": ".example.test"}, stock, False),
    ({"http_proxy": PROXY, "NO_PROXY": "other.example.test"}, stock, True),
    # requests reads a CIDR entry and the standard library does not: either one saying "proxied" is enough.
    ({"http_proxy": PROXY, "NO_PROXY": "192.0.2.0/24"}, stock, True),
    # The standard library says proxied even when the session ignores the environment.
    ({"http_proxy": PROXY}, without_env, True),
    ({}, without_env, False),
    ({}, lambda: with_proxies(http=PROXY), True),
    ({}, lambda: with_proxies(all=PROXY), True),
    ({}, lambda: with_proxies(https=PROXY), False),
    ({}, opaque, True),
    ({}, Unreadable, True),
])
def test_a_session_the_caller_supplies_is_held_to_the_either_rule(env, settings, build, expected):
    for name, value in settings.items():
        env.setenv(name, value)
    assert _otlp_headers.session_proxied(build(), URL) is expected
