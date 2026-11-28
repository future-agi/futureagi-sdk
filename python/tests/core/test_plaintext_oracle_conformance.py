"""The sealed shared plain-HTTP and proxy rule oracle (tests/fixtures/plaintext-oracle), driven through this SDK.

Every row that applies to the Python HTTP transports is sent through the SDK's own key-carrying client
(``LazyKeyAuth`` on an httpx client, the default transport or a caller's), with the SDK's own marker key and
real loopback listeners: the target, and two CONNECT-aware proxy sinks whose addresses the row's environment
names. The SDK's answer (refused before any byte, or sent; the listener that received the request) is compared
with the row, and a refused row fails on any marker byte at any listener. ``key_bytes_at_sink: 0`` in the fixture
is the expected value, not a measurement. A deliberately unguarded send shows the counter counts.
"""

from __future__ import annotations

import collections
import hashlib
from typing import Optional

import httpx
import pytest
from unittest import mock

from fi._credentials import Credentials
from fi._http import ClientRetryingTransport, LazyKeyAuth
from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import *  # noqa: F401,F403
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)


def test_the_vendored_oracle_is_the_sealed_one():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == GZ_SHA256
    assert hashlib.sha256(RAW).hexdigest() == JSON_SHA256
    assert len(ORACLE["rows"]) == 58787


def test_the_oracle_gives_every_plain_source_and_the_eval_config_transport_the_same_answers():
    """What lets one source and one transport stand for the others: the oracle's own rows say so."""
    answers = collections.defaultdict(set)
    for row in ORACLE["rows"]:
        if row["transport"] in TRANSPORTS and row["source"] != "tls":
            answers[_cells(row)].add((row["decision"], row["error"], row["dialed"]))
    assert answers and all(len(each) == 1 for each in answers.values())


@pytest.fixture(scope="module")
def conformance(sinks):
    """Drive every plain-HTTP row once; later tests read the tally."""
    failures: list[str] = []
    tally: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    seen_sinks_bytes = 0
    for row in _plain_rows():
        for scheme, opt, opt_value, caller in _expand(row):
            if scheme != "http":
                continue
            outcome, dialed, counts = _drive(row, scheme, opt_value, caller, sinks)
            problem = _check(row, outcome, dialed, counts, (scheme, opt, caller))
            tally[row["transport"]]["driven"] += 1
            if is_excepted(row):
                tally[row["transport"]]["ruled_exception"] += 1
            elif problem is None:
                tally[row["transport"]]["matched"] += 1
            elif is_spelling_refusal(row, outcome, counts, dialed):
                tally[row["transport"]]["spelling_081"] += 1
            else:
                failures.append(problem)
            if row["decision"] == "refuse":
                tally[row["transport"]]["refused_driven"] += 1
                seen_sinks_bytes += sum(counts.values())
    return failures, tally, seen_sinks_bytes


# The first test to use the module fixture also pays its setup (about 270 s for 15000 driven rows), which a
# 300 s suite timeout under load turns into a setup error, so these two tests carry their own limit.
@pytest.mark.timeout(1800)
def test_every_plain_http_row_is_answered_as_the_oracle_does(conformance):
    failures, tally, _ = conformance
    by_kind = collections.Counter(f.split(": ", 1)[1].split(",")[0].split(" ")[0] for f in failures)
    print("conformance", {t: dict(c) for t, c in tally.items()}, "failures", len(failures), dict(by_kind))
    assert failures[:25] == []
    counts = tally["http"]
    # Under the opt-in the Python SDK refuses the six ambiguous-spelling groups (wnl_127_1, wnl_decimal, wnl_hex, wnl_octal, wnl_localhost_dot, wnl_127_dot) that the shared oracle sends, as in 0.8.1.
    assert counts["matched"] + counts["ruled_exception"] + counts["spelling_081"] == counts["driven"]
    assert counts["driven"] > 12000 and counts["refused_driven"] > 10000
    # Only rows without TLS for the host with an @ after the authority count as exceptions.
    assert counts["ruled_exception"] == 96


@pytest.mark.timeout(1800)
def test_no_marker_byte_reaches_any_sink_for_a_refused_row(conformance):
    _, tally, marker_bytes = conformance
    assert tally["http"]["refused_driven"] > 1000
    assert marker_bytes == 0


def test_the_counter_counts_when_the_guard_is_bypassed(sinks):
    """A deliberately unguarded send of a row the SDK refuses (plain HTTP to a Future AGI host, resolved to this
    machine) puts marker bytes on the target's counter, so a zero elsewhere is a measurement."""
    for each in sinks.values():
        each.reset()
    url = f"http://api.futureagi.com:{sinks['target'].port}/"
    creds = Credentials(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=url, keys_source="argument", base_url_source="argument")
    with mock.patch("fi._http.check_http_security", lambda *a, **k: None):
        with httpx.Client(auth=LazyKeyAuth(lambda: creds), transport=ClientRetryingTransport(retries=0), timeout=1.5) as client:
            client.get(url)
    assert sinks["target"].marker_bytes > 0
    for each in sinks.values():
        each.reset()
    assert _send(url, "none", sinks) == "refused:insecure_futureagi_http"
    assert all(each.marker_bytes == 0 for each in sinks.values())


@pytest.fixture(scope="module")
def tls_conformance():
    """Rows with a TLS source (and the shape rows that hold for either scheme): the decision before any byte."""
    from fi._core.http_security import check_http_security

    failures, driven = [], 0
    for row in _tls_rows():
        host = HOSTS[row["host"]]
        for scheme, opt, opt_value, caller in _expand(row):
            if scheme != "https":
                continue
            url = f"https://{host['authority'].replace('{T}', '4443')}{host['path']}"
            driven += 1
            try:
                check_http_security(url, "keys", environ={})  # type: ignore[arg-type]
                outcome = "sent"
            except ConfigurationError as exc:
                outcome = "refused:" + _oracle_error(str(exc))
            except Exception as exc:
                outcome = f"error:{type(exc).__name__}"
            want = "sent" if row["decision"] == "build" else "refused:" + row["error"]
            if outcome != want:
                failures.append(f"{row_id(row)} {scheme}: SDK {outcome}, oracle {want}")
    return failures, driven


def test_https_rows_follow_the_oracle(tls_conformance):
    failures, driven = tls_conformance
    print("tls rows driven", driven, "failures", len(failures))
    assert driven > 100
    assert failures[:25] == []
