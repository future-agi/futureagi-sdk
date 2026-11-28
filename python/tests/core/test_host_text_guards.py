"""Two checks on the text of a URL that no sender-level test reaches on its own: an IPv4 address written with
non-ASCII dots is refused where the platform origin is parsed, and the text of a plain-http URL that carries
whitespace or a control character is judged by the host-shape check itself."""

from __future__ import annotations

import pytest

from fi._core import origins
from fi._core.http_security import _host_shape_problem
from fi.errors import PlatformNotConfiguredError

DOTS = {"ideographic": "。", "fullwidth": "．", "halfwidth": "｡"}


@pytest.mark.parametrize("kind", sorted(DOTS))
@pytest.mark.parametrize("scheme", ["http", "https"])
def test_an_ipv4_address_written_with_non_ascii_dots_is_refused(kind, scheme):
    dot = DOTS[kind]
    with pytest.raises(PlatformNotConfiguredError) as info:
        origins.parse_origin(f"{scheme}://127{dot}0{dot}0{dot}1:8080/omega/api")
    assert "ASCII dots" in str(info.value)
    assert info.value.code == "invalid_platform_url"


@pytest.mark.parametrize("kind", sorted(DOTS))
def test_a_mixed_ascii_and_non_ascii_dot_ipv4_address_is_refused(kind):
    with pytest.raises(PlatformNotConfiguredError, match="ASCII dots"):
        origins.parse_origin(f"http://10.0{DOTS[kind]}0.1")


def test_a_name_written_with_non_ascii_dots_is_not_read_as_an_address():
    origins.parse_origin("https://api。futureagi。com/omega/api")


def test_an_ipv4_address_written_with_ascii_dots_is_accepted():
    assert origins.parse_origin("http://127.0.0.1:8080").host == "127.0.0.1"


@pytest.mark.parametrize(
    "text",
    [
        " http://example.test/",
        "http://example.test/ ",
        "http://exam\tple.test/",
        "http://example.test/\n",
        "http://example.test/\x00",
        "\thttp://example.test/",
    ],
)
def test_the_host_shape_check_names_whitespace_and_control_characters(text):
    assert _host_shape_problem(text, None) == "has whitespace around it or a control character"


def test_the_host_shape_check_passes_a_plain_url():
    assert _host_shape_problem("http://example.test/", None) is None
