# ruff: noqa: F811
"""An endpoint wrapped in white space is not read as a Future AGI host.

``requests`` refuses ``"https://api.futureagi.com "`` as an invalid URL, so the text is ambiguous: it is not
cleaned up and then classed as Future AGI.
"""

import pytest

from fi._otlp_headers import is_future_agi_endpoint
from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import CODE, build
from tests.experiments.unit.test_fi_bound_authority_forms import (  # noqa: F401
    clean_hosts,
    through_sink,
)
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    ambient,
    sink,
)

WRAPS = [" ", "\t", "\n", "\r\n", " ", " "]


@pytest.mark.parametrize("space", WRAPS)
@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futureagi.com/tracer/v1/traces",
        "api.futureagi.com:443",
        "dns:///grpc.futureagi.com:443",
    ],
)
def test_an_endpoint_with_white_space_around_it_is_not_futureagi(endpoint, space):
    assert is_future_agi_endpoint(endpoint)
    assert not is_future_agi_endpoint(endpoint + space)
    assert not is_future_agi_endpoint(space + endpoint)


# An endpoint wrapped in white space is also refused when the exporter is built.

@pytest.mark.parametrize("space", WRAPS)
@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP"])
def test_an_http_endpoint_with_white_space_around_it_is_refused_at_build(
    through_sink, clean_hosts, ambient, monkeypatch, kind, space
):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    for endpoint in (
        "https://api.futureagi.com/tracer/v1/traces" + space,
        space + "https://api.futureagi.com/tracer/v1/traces",
    ):
        with pytest.raises(ConfigurationError) as refused:
            build(kind, endpoint)
        assert refused.value.code == CODE
    assert through_sink.requests == []


@pytest.mark.parametrize("space", WRAPS)
@pytest.mark.parametrize("endpoint", ["api.futureagi.com:443", "dns:///grpc.futureagi.com:443"])
def test_a_grpc_target_with_white_space_around_it_is_refused_at_build(clean_hosts, ambient, endpoint, space):
    for target in (endpoint + space, space + endpoint):
        with pytest.raises(ConfigurationError) as refused:
            build("OTLP_GRPC", target)
        assert refused.value.code == CODE
