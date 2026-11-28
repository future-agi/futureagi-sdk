"""A gRPC target written as an IPv4-mapped loopback address (``[::ffff:127.0.0.1]``, any address of
``::ffff:127.0.0.0/104``) is a loopback target: a socket dials it to 127.0.0.1 on this machine. A plain channel with
the SDK's keys reaches a loopback collector there, as it does for ``[::1]`` and ``127.0.0.1``, with the target bare,
behind ``grpc://`` or behind ``http://``. A mapped address outside 127.0.0.0/8 (``::ffff:198.51.100.1``,
``::ffff:192.0.2.1``) is another host and is refused without ``FI_ALLOW_INSECURE_HTTP=1``.

The channel cases run in a child process with the connect shim of ``test_grpc_ipv6_target_keyed_headers`` (which
sends a connect to 198.51.100.1, or to ``::ffff:198.51.100.1``, to 127.0.0.1) and a listener on 127.0.0.1 and ``::1`` that
counts the bytes of a planted key and secret.
"""

from __future__ import annotations

import secrets

import pytest

from tests.core.test_grpc_ipv6_target_keyed_headers import MODES, PATHS, run_case, shim_library, sink

SHARED_LISTENER_AND_SHIM = (shim_library, sink)  # pytest fixtures of the IPv6 target cases

MAPPED_LOOPBACK_FORMS = ("[::ffff:127.0.0.1]:{port}", "grpc://[::ffff:127.0.0.1]:{port}",
                         "http://[::ffff:127.0.0.1]:{port}")
MAPPED_REMOTE_FORMS = ("[::ffff:198.51.100.1]:{port}", "grpc://[::ffff:198.51.100.1]:{port}", "http://[::ffff:198.51.100.1]:{port}")
KEYED = {"x-api-key": "mk" + "-A-" + secrets.token_hex(8)}  # a planted marker, made per run


@pytest.mark.parametrize("form", MAPPED_LOOPBACK_FORMS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", PATHS)
def test_keyed_headers_reach_a_mapped_loopback_collector_over_a_plain_channel(shim_library, tmp_path, sink, path,
                                                                              mode, form):
    result, seen = run_case(shim_library, tmp_path, sink, path, mode, form.format(port=sink.port))
    observed = (result, seen)
    assert result["refused"] is None and result["insecure"] == [True], observed
    assert seen.plain >= 1 and seen.marker_bytes > 0, observed
    assert seen.connects and set(seen.connects) <= {"::ffff:127.0.0.1", "127.0.0.1"}, observed


@pytest.mark.parametrize("form", MAPPED_REMOTE_FORMS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", PATHS)
def test_keyed_headers_get_no_plain_channel_to_a_mapped_address_outside_loopback(shim_library, tmp_path, sink, path,
                                                                                 mode, form):
    result, seen = run_case(shim_library, tmp_path, sink, path, mode, form.format(port=sink.port))
    observed = (result, seen)
    assert result["configuration_error"] and result["code"] == "insecure_http_origin", observed
    assert result["insecure"] == [], observed
    assert seen.connections == 0 and seen.plain == 0 and seen.marker_bytes == 0, observed
    assert seen.connects == [], observed


# --- the target as read and judged, without a channel -----------------------------------------------------------------


@pytest.mark.parametrize("endpoint", [
    "[::ffff:127.0.0.1]:4317", "grpc://[::ffff:127.0.0.1]:4317", "http://[::ffff:127.0.0.1]:4317",
    "[::ffff:127.0.0.1]", "GRPC://[::FFFF:127.0.0.1]:4317", "[::ffff:127.9.8.7]:4317", "[::ffff:7f00:1]:4317",
    "[0:0:0:0:0:ffff:127.0.0.1]:4317", "foo://[::ffff:127.255.255.254]:4317",
])
def test_a_plain_channel_to_a_mapped_loopback_target_passes(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_loopback_target, grpc_plain_choice

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    require_secure_grpc_target(endpoint, KEYED, insecure=True)
    assert grpc_plain_choice(endpoint, True) is False
    assert grpc_loopback_target(endpoint)


@pytest.mark.parametrize("endpoint", [
    "[::ffff:198.51.100.1]:4317", "grpc://[::ffff:198.51.100.1]:4317", "http://[::ffff:198.51.100.1]:4317",
    "[::ffff:192.0.2.1]:4317", "grpc://[::ffff:192.0.2.1]:4317", "http://[::ffff:192.0.2.1]:4317",
    "[::ffff:128.0.0.1]:4317", "[::ffff:126.255.255.255]:4317", "[::127.0.0.1]:4317", "[::ffff:0:127.0.0.1]:4317",
    "[64:ff9b::127.0.0.1]:4317", "[::ffff:127.0.0.1%lo]:4317", "grpc://[::ffff:127.0.0.1%25lo]:4317",
    "grpc://user@[::ffff:127.0.0.1]:4317",
])
def test_a_plain_channel_with_keyed_headers_to_a_mapped_target_that_is_not_loopback_is_refused(endpoint, monkeypatch):
    from fi._core.http_security import require_secure_grpc_target
    from fi._otlp_headers import grpc_loopback_target, grpc_plain_choice
    from fi.errors import ConfigurationError

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    with pytest.raises(ConfigurationError):
        require_secure_grpc_target(endpoint, KEYED, insecure=True)
    with pytest.raises(ConfigurationError):
        grpc_plain_choice(endpoint, True)
    assert not grpc_loopback_target(endpoint)


@pytest.mark.parametrize("host", ["::ffff:127.0.0.1", "[::ffff:127.0.0.1]", "::ffff:7f00:1"])
def test_the_shared_loopback_table_keeps_its_answer_for_a_mapped_address(host):
    # The platform, sandbox channel and gateway rule is the table shared with the TypeScript client.
    from fi._core.loopback import is_loopback_host

    assert is_loopback_host(host) is False
