"""The plain-HTTP decision and the proxy rule as one function, checked against the rows both clients share
(tests/fixtures/loopback/proxy_env.json) and against the standard library's own bypass rule."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from fi._core.http_security import cpython_env_proxied, env_proxied, plaintext_decision
from fi.sandbox._channel.connect import _port_problem

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "loopback" / "proxy_env.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_the_fixture_matches_its_recorded_digest():
    recorded = FIXTURE.with_name(FIXTURE.name + ".sha256").read_text().split()
    assert recorded == [hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), FIXTURE.name]


def test_the_fixture_has_every_reason():
    assert {row["reason"] for row in ROWS["decisions"]} == set(ROWS["reasons"]) - {"unparsable"}
    assert any(row["proxied"] for row in ROWS["envProxy"]) and not all(row["proxied"] for row in ROWS["envProxy"])


@pytest.mark.parametrize("row", ROWS["envProxy"], ids=lambda row: row["id"])
def test_env_proxy_rows(row):
    assert cpython_env_proxied(row["url"], row["env"]) is row["proxied"]
    assert env_proxied(row["url"], row["env"]) is row["proxied"]


@pytest.mark.parametrize("row", ROWS["libraryEnvProxy"], ids=lambda row: row["id"])
def test_library_env_proxy_rows(row):
    assert cpython_env_proxied(row["url"], row["env"]) is row["proxied"] is False
    assert env_proxied(row["url"], row["env"]) is True


@pytest.mark.parametrize(
    "row", ROWS["decisions"] + ROWS["libraryDecisions"] + ROWS["hostShapes"], ids=lambda row: row["id"]
)
def test_decision_rows(row):
    decision = plaintext_decision(
        row["url"], allow_insecure_http=row["allowInsecureHttp"], environ=row["env"], caller_proxied=row["callerProxied"],
    )
    assert (decision.allowed, decision.reason) == (row["allowed"], row["reason"])


@pytest.mark.parametrize("row", ROWS["channelPorts"], ids=lambda row: row["url"])
def test_channel_port_rows(row):
    problem = _port_problem(row["url"])
    assert (problem is not None) is row["refused"]
    if problem is None:
        assert urlsplit(row["url"]).port == row["port"]


def test_the_decision_is_pure(capsys):
    plaintext_decision("http://example.com", environ={"FI_ALLOW_INSECURE_HTTP": "1"})
    assert capsys.readouterr().err == ""


def test_a_plain_url_that_cannot_be_parsed_is_judged_on_the_host_as_written():
    refused = plaintext_decision("http://h:ab", environ={})
    assert (refused.allowed, refused.reason) == (False, "not_opted_in")
    octal = plaintext_decision("http://0177.0.0.1:8080/", environ={"FI_ALLOW_INSECURE_HTTP": "1"}, proxies_disabled=True)
    assert (octal.allowed, octal.reason) == (False, "ambiguous_host")  # the 0.8.1 rule: the opt-in does not unlock it
    assert plaintext_decision("http://0177.0.0.1/", environ={}).reason == "not_opted_in"


def test_a_url_that_is_not_http_passes():
    assert plaintext_decision("not a url", environ={}).allowed is True
