"""A header value that holds ``FI_API_KEY`` or ``FI_SECRET_KEY`` from the environment is a key in any encoding the value
can carry it in: a Basic credential in a custom header or in ``Proxy-Authorization`` (any user length, the key as user
or password), the key in another letter case, hex in either case, every byte percent-encoded, base64 at any offset and
base64 of base64. The value is decoded to find the key; the encodings are not listed.

Host names resolve to the loopback address (``rig`` replaces ``getaddrinfo``); the target and the
``CONNECT``-aware proxy sink count connections and marker hits, decoding what they receive the same ways."""

import base64
import re
import urllib.parse

import pytest

from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV
from fi._core.proxy_routing import carries_credentials
from fi.api.auth import HttpClient
from tests.experiments.unit.test_header_key_senders import (  # noqa: F401  (rig is used by name)
    MARKER, outcome, proxied, refused, remote, rig,
)

ODD = MARKER + "q"  # a key whose length leaves one byte over in its last base64 group


def b64(text, encode=base64.b64encode):
    return encode(text.encode() if isinstance(text, str) else text).decode()


def every_byte_quoted(text):
    return "".join(f"%{byte:02X}" for byte in text.encode())


def forms(key):
    """Header values that each carry ``key`` once."""
    values = {f"basic, user of length {n}": "Basic " + b64("user"[:n] + ":" + key) for n in (0, 1, 3, 4)}
    values.update({
        "basic, key as user": "Basic " + b64(key + ":pw"),
        "upper case": key.upper(),
        "hex": key.encode().hex(),
        "upper-case hex": key.encode().hex().upper(),
        "every byte percent-encoded": every_byte_quoted(key),
        "base64 at offset 1": b64("a" + key),
        "base64 at offset 2": b64("ab" + key),
        "url-safe base64 at offset 1, unpadded": b64("a" + key, base64.urlsafe_b64encode).rstrip("="),
        "base64 of base64": b64(b64(key)),
        "base64 inside other text": "pre-" + b64("ab" + key) + "-post",
        "percent-encoded base64": urllib.parse.quote(b64("a" + key), safe=""),
    })
    return values


CASES = {**{name: (MARKER, v) for name, v in forms(MARKER).items()},
         "key as user, length one over a group": (ODD, "Basic " + b64(ODD + ":pw"))}
HEADERS = ["X-Trace", "Proxy-Authorization"]


def _decoded(data, depth=3):
    """``data`` and what it decodes to: percent, hex and base64 (both alphabets, any start offset), nested."""
    found, pending = [data], [(data, 0)]
    while pending:
        blob, level = pending.pop()
        if level == depth:
            continue
        out = [urllib.parse.unquote_to_bytes(blob), urllib.parse.unquote_to_bytes(blob.replace(b"+", b" "))]
        for token in re.findall(rb"[0-9A-Fa-f]{16,}", blob):
            out.extend(bytes.fromhex(token[i:].decode()[: (len(token) - i) // 2 * 2]) for i in (0, 1))
        for pattern, alt in ((rb"[A-Za-z0-9+/]{11,}", None), (rb"[A-Za-z0-9_-]{11,}", b"-_")):
            for token in re.findall(pattern, blob):
                for i in range(4):
                    piece = token[i:][: len(token) - i - ((len(token) - i) % 4 == 1)]
                    out.append(base64.b64decode(piece + b"=" * (-len(piece) % 4), altchars=alt))
        for each in out:
            if each not in found:
                found.append(each)
                pending.append((each, level + 1))
    return found


def hits(sink, key):
    """Marker hits at ``sink``: the key in any letter case in what it received, decoded every way above."""
    needle = key.lower().encode()
    return sum(each.lower().count(needle) for each in _decoded(b"".join(sink.data)))


def client_with(name, value):
    return lambda base, monkeypatch: (HttpClient(base_url=base, default_headers={name: value}), {})


@pytest.mark.parametrize("header", HEADERS)
@pytest.mark.parametrize("case", list(CASES))
def test_a_header_value_holding_the_key_in_any_encoding_is_a_key(monkeypatch, case, header):
    key, value = CASES[case]
    monkeypatch.setenv("FI_API_KEY", key)
    assert carries_credentials({header: value}) is True
    monkeypatch.delenv("FI_API_KEY")
    monkeypatch.setenv("FI_SECRET_KEY", key)
    assert carries_credentials({header: value}) is True


@pytest.mark.parametrize("header", HEADERS)
@pytest.mark.parametrize("case", list(CASES))
def test_the_encoded_key_reaches_neither_the_target_nor_a_proxy(rig, monkeypatch, case, header):
    key, value = CASES[case]
    monkeypatch.setenv("FI_API_KEY", key)
    proxied(rig, monkeypatch)
    error = outcome(client_with(header, value), remote(rig.target), monkeypatch)
    seen = {"target": (rig.target.connections, hits(rig.target, key)), "proxy": (rig.proxy.connections, hits(rig.proxy, key))}
    assert (refused(error), seen) == (True, {"target": (0, 0), "proxy": (0, 0)}), (error, seen)
    assert key not in str(error)


@pytest.mark.parametrize("case", list(CASES))
def test_with_the_opt_in_the_encoded_key_is_delivered_to_the_target_and_counted(rig, monkeypatch, case):
    key, value = CASES[case]
    monkeypatch.setenv("FI_API_KEY", key)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    outcome(client_with("X-Trace", value), remote(rig.target), monkeypatch)
    assert rig.target.connections == 1 and hits(rig.target, key) >= 1
    assert rig.proxy.connections == 0


UNRELATED = {
    "basic with another password": "Basic " + b64("user:another-password-value"),
    "hex of other text": b"some other header text".hex(),
    "base64 of other text": b64("ab" + "unrelated header payload"),
    "percent-encoded other text": every_byte_quoted("unrelated-value"),
    "a request id": "7d3f0a52-4c1e-4b8e-9a41-0c2b5e6f7a81",
    "a traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
}


@pytest.mark.parametrize("value", list(UNRELATED))
def test_a_value_that_decodes_to_other_text_is_not_a_key_and_is_sent(rig, monkeypatch, value):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    monkeypatch.setenv("FI_SECRET_KEY", ODD)
    assert carries_credentials({"X-Trace": UNRELATED[value]}) is False
    error = outcome(client_with("X-Trace", UNRELATED[value]), remote(rig.target), monkeypatch)
    assert not refused(error), error
    assert rig.target.connections == 1 and hits(rig.target, MARKER) == 0


def test_a_short_environment_key_is_not_looked_for_in_decoded_values(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "abcdefg")
    for value in ("ABCDEFG-team", b"abcdefg".hex(), "Basic " + b64("u:abcdefg"), every_byte_quoted("abcdefg")):
        assert carries_credentials({"X-Team": value}) is False
