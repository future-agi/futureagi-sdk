"""A keyed judgement reads each header value for a key once.

``require_secure_credential_headers`` and ``require_endpoint_with_keys`` judge whether a request's headers carry a key
and, on a refusal that rests only on a value longer than 64 KiB, open the message with the note that names that limit.
The note is built only for a refusal and reuses what the first pass read: a value up to 64 KiB is handed to the scanner
at most once per judgement, and an allowed send whose first value is over the limit scans no other value.

The scanner is counted by a wrapper around ``holds_key`` (no wall-clock timing). Keys and values are made at run time;
no request is sent."""

import base64
import os
import secrets
from collections import Counter

import pytest

from fi._core import header_key_scan, proxy_routing
from fi._core.http_security import require_endpoint_with_keys, require_secure_credential_headers
from fi.errors import ConfigurationError
from tests.core.test_header_key_scan_size_cap import PROXY_NAMES

CAP = 64 * 1024
MB1 = 1024 * 1024
SIZE_WORDS = ("65,536", "64 KiB")


def random_value(size):
    return base64.b64encode(os.urandom(size)).decode("ascii")[:size]


@pytest.fixture
def key(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_ALLOW_INSECURE_HTTP") + PROXY_NAMES:
        monkeypatch.delenv(name, raising=False)
    made = "mk" + "-A-" + secrets.token_hex(8)
    monkeypatch.setenv("FI_API_KEY", made)
    return made


@pytest.fixture
def scans(monkeypatch):
    """How many times each value up to the cap was handed to the scanner."""
    counted = Counter()
    real = header_key_scan.holds_key

    def counting(text, keys):
        if len(text) <= CAP:
            counted[text] += 1
        return real(text, keys)

    monkeypatch.setattr(header_key_scan, "holds_key", counting)
    monkeypatch.setattr(proxy_routing, "holds_key", counting)
    return counted


def mixed(big_first):
    """One 1 MB value and four values of 64 KiB, none holding a key."""
    small = {f"X-Part-{n}": random_value(CAP) for n in range(4)}
    big = {"X-Big": random_value(MB1)}
    return ({**big, **small} if big_first else {**small, **big}), list(small.values())


def test_an_allowed_send_scans_each_value_at_most_once(key, scans):
    for big_first in (True, False):
        scans.clear()
        headers, small = mixed(big_first)
        require_secure_credential_headers("https://collector.example.test/v1/traces", headers)
        per_value = [scans[value] for value in small]
        assert per_value == ([0] * 4 if big_first else [1] * 4), (big_first, per_value)


def test_a_refusal_resting_on_the_cap_scans_each_value_once_and_names_the_cap(key, scans):
    for big_first in (True, False):
        scans.clear()
        headers, small = mixed(big_first)
        with pytest.raises(ConfigurationError) as caught:
            require_secure_credential_headers("http://plain.example.test/v1/traces", headers)
        assert caught.value.code == "insecure_http_origin"
        assert all(word in str(caught.value) for word in SIZE_WORDS), str(caught.value)
        per_value = [scans[value] for value in small]
        assert per_value == [1] * 4, (big_first, per_value)


def test_an_empty_endpoint_refusal_scans_each_value_once_and_names_the_cap(key, scans):
    for big_first in (True, False):
        scans.clear()
        headers, small = mixed(big_first)
        with pytest.raises(ConfigurationError) as caught:
            require_endpoint_with_keys("", headers)
        assert all(word in str(caught.value) for word in SIZE_WORDS), str(caught.value)
        per_value = [scans[value] for value in small]
        assert per_value == [1] * 4, (big_first, per_value)


def test_a_refusal_for_a_found_key_scans_each_value_once_and_does_not_name_the_cap(key, scans):
    found = random_value(CAP - 64) + key
    headers = {"X-Part-0": random_value(CAP), "X-Found": found, "X-Big": random_value(MB1)}
    with pytest.raises(ConfigurationError) as caught:
        require_secure_credential_headers("http://plain.example.test/v1/traces", headers)
    assert not any(word in str(caught.value) for word in SIZE_WORDS), str(caught.value)
    assert key not in str(caught.value)
    assert [scans[headers["X-Part-0"]], scans[found]] == [1, 1]
