"""An endpoint of only white space is refused as ambiguous; an empty endpoint is no endpoint.

The check reads the host of an endpoint. White space in the path is outside it: the host is read from the authority.
"""

import pytest

from fi import _otlp_headers
from fi.errors import ConfigurationError


@pytest.mark.parametrize("endpoint", [" ", "   ", "\t", "\n", " \t\r\n", " ", " "])
def test_an_endpoint_of_only_white_space_is_ambiguous(endpoint):
    assert _otlp_headers.is_ambiguous_endpoint(endpoint) is True
    assert _otlp_headers.is_ambiguous_endpoint(endpoint, tls=True) is True


@pytest.mark.parametrize("endpoint", [" ", "   ", "\t"])
def test_an_endpoint_of_only_white_space_is_refused_with_the_ambiguous_code(endpoint):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_ambiguous_endpoint(endpoint)
    assert refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("endpoint", ["", None])
def test_an_empty_endpoint_is_no_endpoint(endpoint):
    assert _otlp_headers.is_ambiguous_endpoint(endpoint) is False
    _otlp_headers.refuse_ambiguous_endpoint(endpoint)
