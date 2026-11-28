"""The OTLP exporters read ``OTEL_EXPORTER_OTLP_HEADERS`` and ``OTEL_EXPORTER_OTLP_TRACES_HEADERS`` themselves, so a Future AGI
key in either variable goes to whatever endpoint the exporter has. A key in those variables is refused for an exporter that does
not send to Future AGI, whatever the header is named or how the value is written, and for a Future AGI endpoint it follows the
same plain-http rule as a key in the exporter's own headers. An exporter with an empty endpoint and keys is refused for every
exporter type, since the exporter would otherwise read its endpoint from the environment. Marker keys are counted at the
loopback target."""

from __future__ import annotations

import os
from typing import Any
from unittest import mock
from urllib.parse import quote

import pytest

from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import KEYS, _clean_env, _exporter

FI_HTTP_ENDPOINTS = ["http://api.futureagi.com/tracer/v1/traces", "http://app.futureagi.com:81/v1/traces", "http://futureagi.com:81/v1/traces"]
HTTP_KINDS = ["OTLP_HTTP", "FUTUREAGI", "ARIZE", "PHOENIX", "LANGFUSE"]
KEY_ENV = {"OTEL_EXPORTER_OTLP_HEADERS": f"x-api-key={MARKER_KEY},x-secret-key={MARKER_SECRET}"}


def _env(**extra: str) -> dict[str, str]:
    return _clean_env(FI_API_KEY=MARKER_KEY, FI_SECRET_KEY=MARKER_SECRET, **extra)


@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS"])
@pytest.mark.parametrize("endpoint", FI_HTTP_ENDPOINTS)
@pytest.mark.parametrize("kind", HTTP_KINDS)
def test_a_key_in_the_environment_headers_is_refused_for_a_plain_http_future_agi_endpoint(kind, endpoint, variable):
    with mock.patch.dict(os.environ, _env(**{variable: KEY_ENV["OTEL_EXPORTER_OTLP_HEADERS"]}), clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter(kind, endpoint)
    assert MARKER_KEY not in str(info.value) and MARKER_SECRET not in str(info.value)


@pytest.mark.parametrize("endpoint", ["api.futureagi.com:4317", "http://api.futureagi.com:4317", "app.futureagi.com:81"])
def test_a_key_in_the_environment_headers_is_refused_for_a_plain_grpc_future_agi_target(endpoint):
    with mock.patch.dict(os.environ, _env(**KEY_ENV), clear=True):
        with pytest.raises(ConfigurationError):
            _exporter("OTLP_GRPC", endpoint, insecure=True)


@pytest.mark.parametrize("kind", HTTP_KINDS)
def test_a_key_in_the_environment_headers_is_accepted_for_an_https_future_agi_endpoint(kind):
    with mock.patch.dict(os.environ, _env(**KEY_ENV), clear=True):
        if kind == "FUTUREAGI" or kind == "OTLP_HTTP":
            assert _exporter(kind, "https://api.futureagi.com/tracer/v1/traces") is not None


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
@pytest.mark.parametrize("endpoint", ["", None])
def test_an_exporter_with_keys_and_no_endpoint_is_refused_as_an_empty_authority(kind, endpoint):
    with mock.patch.dict(os.environ, _clean_env(OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:9", OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://127.0.0.1:9"), clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter(kind, endpoint, headers=dict(KEYS))
    assert MARKER_KEY not in str(info.value)


@pytest.mark.parametrize("header,value", [
    ("authorization", "Basic {key}"),
    ("authorization", "Token {key}"),
    ("authorization", "prefix-{key}"),
    ("authorization", "Bearer\t{key}"),
    ("authorization", "{key};x=y"),
    ("x-fi-key", "{key}"),
    ("api-key", "{key}"),
    ("cookie", "session={key}"),
])
def test_an_environment_header_that_holds_a_future_agi_key_is_refused_for_another_exporter_whatever_its_name(sinks, header, value):
    for each in sinks.values():
        each.reset()
    text = value.format(key=MARKER_KEY)
    with mock.patch.dict(os.environ, _env(OTEL_EXPORTER_OTLP_HEADERS=f"{header}={quote(text, safe='')}"), clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")
    assert MARKER_KEY not in str(info.value)
    assert all(each.marker_bytes == 0 for each in sinks.values())


def test_an_environment_header_that_holds_a_double_encoded_future_agi_key_is_refused(sinks):
    once = quote(f"Bearer {MARKER_KEY}", safe="")
    with mock.patch.dict(os.environ, _env(OTEL_EXPORTER_OTLP_HEADERS=f"authorization={quote(once, safe='')}"), clear=True):
        with pytest.raises(ConfigurationError):
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")


def test_an_environment_header_with_another_value_is_accepted_for_another_exporter(sinks):
    env = _env(OTEL_EXPORTER_OTLP_HEADERS="x-team=blue,authorization=Bearer%20some-other-token")
    with mock.patch.dict(os.environ, env, clear=True):
        assert _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces") is not None


@pytest.mark.parametrize("variable", ["FI_SECRET_KEY", "FI_PLATFORM_TOKEN"])
def test_a_secret_key_or_platform_token_in_an_environment_header_is_refused_for_another_exporter(sinks, variable):
    env = _clean_env(**{variable: MARKER_SECRET, "OTEL_EXPORTER_OTLP_HEADERS": f"authorization=Bearer%20{MARKER_SECRET}"})
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError) as info:
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")
    assert MARKER_SECRET not in str(info.value)


@pytest.mark.parametrize("name", ["x%2Dapi%2Dkey", "X-API-KEY", " x-secret-key "])
def test_a_key_header_name_is_found_whatever_its_encoding_or_case(sinks, name):
    env = _clean_env(OTEL_EXPORTER_OTLP_HEADERS=f"{name}=anything")
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError):
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")


@pytest.mark.parametrize("scheme_word", ["bEaReR", "BEARER", "bearer"])
def test_a_bearer_value_is_found_whatever_the_case_of_its_scheme_word(sinks, scheme_word):
    env = _env(OTEL_EXPORTER_OTLP_HEADERS=f"authorization={scheme_word}%20{MARKER_KEY}")
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError):
            _exporter("OTLP_HTTP", f"http://127.0.0.1:{sinks['target'].port}/v1/traces")
