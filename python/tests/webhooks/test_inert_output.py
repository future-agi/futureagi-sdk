"""WT-15c, the CLI part: receiver and tenant text prints as inert text.

An HTML or ``javascript:`` echo stays plain text (a terminal never runs it). Every character that could rewrite what a
terminal shows (ANSI escapes, CR and line separators, zero-width and bidi characters) is printed as ``\\uXXXX`` in
every human-readable line: tables, ``get``, ``delivery --attempts``, ``test``, ``create`` and the error line. The API
strips most of them from what it stores, so these tests serve them raw from a stub to prove the CLI's own escaping."""

from __future__ import annotations

import json
import re

import pytest

from fi.webhooks import _api
from fi.webhooks._text import inert, is_live

from ._stub import ok
from .test_cli import EP, SECRET, run, stub  # noqa: F401  (the stub fixture)

ESC, CSI, RLO, LRI, ALM, ZWSP, LS, BOM = "\x1b", "\x9b", "\u202e", "\u2066", "\u061c", "\u200b", "\u2028", "\ufeff"
HOSTILE = f"{ESC}[2J<script>alert(1)</script> javascript:alert(1)\r{CSI}31m{RLO}lmth.exe{LRI}{ALM}{ZWSP}{LS}{BOM}"
LIVE = (ESC, CSI, RLO, LRI, ALM, ZWSP, LS, BOM, "\r")

# FA's own strip set for stored receiver text (futureagi/webhooks/core/attempt.py, ``_INERT``, S9): C0 controls except
# tab and newline, DEL, C1, ALM, LRM, RLM, the bidi embeddings and overrides, and the isolates.
SERVER_SET = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]")


def _clean(text: str) -> bool:
    return not any(ch in text for ch in LIVE)


def test_every_character_the_api_strips_is_escaped_too():
    stripped = [chr(c) for c in range(0x10000) if SERVER_SET.match(chr(c))]
    assert len(stripped) == 9 + 21 + 33 + 1 + 2 + 5 + 4
    assert [ch for ch in stripped if not is_live(ord(ch))] == []
    assert all(inert(ch) == f"\\u{ord(ch):04x}" for ch in stripped)


@pytest.mark.parametrize("ch", ["\t", "\n", "\r", ESC, "\x7f", CSI, "\x85", ALM, ZWSP, "\u200d", "\u200e",
                                LS, "\u2029", "\u202a", RLO, "\u2060", LRI, "\u2069", BOM])
def test_each_live_class_prints_as_an_escape(ch):
    assert inert(f"a{ch}b") == f"a\\u{ord(ch):04x}b"


@pytest.mark.parametrize("text", ["<b>hi</b>", "javascript:alert(1)", "é ü ß", "日本語", "\U0001f600", "a  b", "{\"k\": 1}"])
def test_printable_text_is_unchanged(text):
    assert inert(text) == text


def test_cut_and_none():
    assert inert(None) == ""
    assert inert("x" * 10, 4) == "xxxx…"
    assert inert(RLO * 3, 2) == "\\u202e\\u202e…"
    assert inert(42) == "42"


def test_delivery_attempts_table_and_get_print_hostile_text_inertly(stub, capsys):  # noqa: F811
    ep = {**EP, "name": f"ops{RLO}gpj.exe", "description": HOSTILE}
    stub.on("GET", "/webhooks/endpoints/", ok({"results": [ep]}))
    stub.on("GET", "/webhooks/endpoints/whep_01/", ok(ep))
    attempt = {"n": 1, "started_at": "2026-10-23T00:00:00Z", "trigger": "auto", "outcome": "http_error",
               "response_status": 500, "duration_ms": 12, "response_body_excerpt": HOSTILE, "error_detail": HOSTILE}
    stub.on("GET", "/webhooks/deliveries/dlv_01/", ok({
        "id": "dlv_01", "event_type": f"prompt.label.changed{RLO}", "event_id": "evt_1", "status": "failed",
        "attempts_count": 1, "seq": 7, "is_test": False, "attempts": [attempt]}))
    for argv in (("list",), ("get", "whep_01"), ("delivery", "dlv_01", "--attempts")):
        assert run(*argv) == 0, argv
        out, err = capsys.readouterr()
        assert _clean(out + err), (argv, out + err)
        assert "\\u202e" in out, (argv, out)
    run("delivery", "dlv_01", "--attempts")
    out = capsys.readouterr().out
    assert "<script>alert(1)</script> javascript:alert(1)" in out and "\\u001b[2J" in out and "\\u009b31m" in out
    assert out.count("\n") == 4  # the header line, the attempt line, response and detail: no forged lines


def test_test_and_create_print_hostile_text_inertly(stub, capsys, tmp_path):  # noqa: F811
    stub.on("POST", "/webhooks/endpoints/whep_01/test/", ok({
        "event_id": "evt_test_1", "delivery_id": f"dlv_t{ESC}[1A", "status_code": 200, "outcome": "success",
        "latency_ms": 9, "response_excerpt": HOSTILE}))
    assert run("test", "whep_01", "--event", "prompt.label.changed") == 0
    out, err = capsys.readouterr()
    assert _clean(out + err) and "<script>alert(1)</script>" in out and "\\u202e" in out
    created = {**EP, "name": f"n{RLO}x"}
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": created, "secret": SECRET,
                                                "warnings": [{"code": "W", "message": f"w{ESC}]0;title{BOM}"}]}, 201))
    assert run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.label.changed",
               "--secret-out", str(tmp_path / "s")) == 0
    out, err = capsys.readouterr()
    assert _clean(out + err) and "\\u202e" in err and "\\u001b]0;title\\ufeff" in err


def test_create_echoes_the_event_arguments_inertly_and_prints_a_checked_secret(stub, capsys, tmp_path):  # noqa: F811
    """S3: ``Created ... for <events>`` joins the user's ``--event`` values, and the secret line prints the server's
    secret; the first goes through ``inert()``, the second is printed only after ``secret_key()`` accepted it."""
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    hostile = f"prompt.label.changed{RLO}{ESC}[2J{LS}"
    assert run("create", "--url", "https://hooks.acme.ai/fi", "--event", hostile, "--show-secret") == 0
    out, err = capsys.readouterr()
    assert _clean(out + err) and "for prompt.label.changed\\u202e\\u001b[2J\\u2028" in err
    assert out == SECRET + "\n"
    bad = f"whsec_{ESC}[31m" + "A" * 32
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": bad, "warnings": []}, 201))
    assert run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.*", "--show-secret") == 3
    out, err = capsys.readouterr()
    assert _clean(out + err) and out == "" and "A" * 32 not in err


def test_no_source_file_of_the_slice_carries_a_raw_invisible_or_bidi_character():
    """S1: such characters are written as escapes, so GitHub shows no hidden-Unicode warning and nothing reads like
    Trojan Source. Any ``is_live`` character other than tab and newline counts (BOM, bidi, zero-width, C0, C1)."""
    from pathlib import Path

    py = Path(__file__).resolve().parents[2]
    ts = py.parent / "typescript" / "futureagi" / "src" / "webhooks"
    files = [*(py / "fi" / "webhooks").rglob("*.py"), *(py / "futureagi-webhooks").rglob("*.py"),
             *Path(__file__).resolve().parent.rglob("*.py"), *ts.rglob("*.ts")]
    assert len(files) > 20
    found = {str(f.relative_to(py.parent)): sorted({f"U+{ord(c):04X}" for c in f.read_text(encoding="utf-8")
                                                    if is_live(ord(c)) and c not in "\t\n"})
             for f in files}
    assert {k: v for k, v in found.items() if v} == {}


def test_a_refusal_prints_one_inert_error_line(stub, capsys):  # noqa: F811
    stub.on("GET", "/webhooks/endpoints/whep_01/", (400, {"status": False, "code": f"WEBHOOK_X{ESC}[0m",
                                                          "message": f"bad{RLO}\r\nforged: line", "attr": f"u{LS}rl"}))
    assert run("get", "whep_01") == 3
    out, err = capsys.readouterr()
    assert _clean(out + err) and err.count("\n") == 1 and "\\u000d\\u000aforged: line" in err
    assert run("get", "whep_01", "--json") == 3
    msg = json.loads(capsys.readouterr().out)["error"]["message"]
    assert _clean(msg)


def test_the_library_error_keeps_the_raw_detail_and_an_inert_message():
    err = _api.error(400, {"code": "WEBHOOK_URL_INVALID", "message": f"bad{RLO}url\r", "attr": "url"})
    assert _clean(str(err)) and str(err) == "WEBHOOK_URL_INVALID: bad\\u202eurl\\u000d (url) [HTTP 400]"
    assert err.detail == f"bad{RLO}url\r" and err.code == "WEBHOOK_URL_INVALID" and err.attr == "url"


class _Terminal:
    """A stdin that is a terminal and answers ``y`` to the one confirmation question."""

    def isatty(self):
        return True

    def readline(self):
        return "y\n"


def test_every_other_human_line_escapes_what_the_server_sent(stub, capsys, monkeypatch, tmp_path):  # noqa: F811
    """Ids, statuses, counts, tails and times come from the server too: a hostile server cannot put a live character
    into any line the CLI prints (update, enable, enable --resume, disable, rotate-secret, revoke-previous-secret,
    the delete question, delete, redeliver one and many, the bulk count and question, events --schema)."""
    h = f"x{ESC}[2J{RLO}{LS}{BOM}"
    hostile_ep = {**EP, "id": f"whep{h}", "name": f"n{h}", "status": f"enabled{h}"}
    stub.on("PATCH", "/webhooks/endpoints/whep_01/", ok(hostile_ep))
    stub.on("POST", "/webhooks/endpoints/whep_01/enable/", ok(hostile_ep))
    stub.on("POST", "/webhooks/endpoints/whep_01/disable/", ok(hostile_ep))
    stub.on("POST", "/webhooks/endpoints/whep_01/resume/", ok({"mode": "send", "sent": h, "skipped": h,
                                                                "past_max_age": h, "backlog_capped": 0}))
    stub.on("POST", "/webhooks/endpoints/whep_01/rotate-secret/", ok({
        "secret": SECRET, "id": "whk_2", "tail": SECRET[-4:], "previous": {"tail": h, "expires_at": h},
        "revoked_tails": [h]}))
    stub.on("POST", "/webhooks/endpoints/whep_01/revoke-previous-secret/", ok({"revoked_tails": [h]}))
    stub.on("GET", "/webhooks/endpoints/whep_01/", ok(hostile_ep))
    stub.on("DELETE", "/webhooks/endpoints/whep_01/", ok({"cancelled_deliveries": h}))
    stub.on("POST", "/webhooks/deliveries/dlv_1/redeliver/", ok({"delivery_id": f"dlv{h}", "attempt": h}, 202))
    stub.on("POST", "/webhooks/deliveries/redeliver/", ok({"count": h, "queued": h, "expired": h, "dry_run": False}))
    stub.on("GET", "/webhooks/event-types/", ok({"results": [{"type": f"prompt.label.changed{h}", "schema": {}}]}))
    monkeypatch.setattr("sys.stdin", _Terminal())
    for argv in (("update", "whep_01", "--name", "n2"), ("enable", "whep_01"), ("enable", "whep_01", "--resume", "send"),
                 ("disable", "whep_01"), ("rotate-secret", "whep_01", "--secret-out", str(tmp_path / "s")),
                 ("revoke-previous-secret", "whep_01"), ("delete", "whep_01"), ("redeliver", "dlv_1"),
                 ("redeliver", "--endpoint", "whep_01", "--status", "failed", "--dry-run"),
                 ("redeliver", "--endpoint", "whep_01", "--status", "failed")):
        assert run(*argv) == 0, argv
        out, err = capsys.readouterr()
        assert _clean(out + err), (argv, out + err)
        assert "\\u202e" in out + err, (argv, out + err)
    assert run("events", "--schema", "nope") == 2
    out, err = capsys.readouterr()
    assert _clean(out + err) and "\\u202e" in err
