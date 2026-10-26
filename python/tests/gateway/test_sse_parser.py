"""Tests for SSE parser."""

from __future__ import annotations


def _make_byte_stream(lines: list[str]) -> list[bytes]:
    """Create a byte stream from lines (each line gets \\n appended)."""
    return [("\n".join(lines) + "\n").encode("utf-8")]


def test_parse_single_event() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream(["data: hello", ""])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    assert events[0].data == "hello"


def test_parse_multiple_events() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "data: first",
        "",
        "data: second",
        "",
        "data: third",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 3
    assert events[0].data == "first"
    assert events[1].data == "second"
    assert events[2].data == "third"


def test_parse_done_terminates() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "data: first",
        "",
        "data: [DONE]",
        "",
        "data: should-not-appear",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 2
    assert events[0].data == "first"
    assert events[1].data == "[DONE]"


def test_skip_comment_lines() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        ": this is a comment",
        "data: actual data",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    assert events[0].data == "actual data"


def test_multi_line_data() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "data: line1",
        "data: line2",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    assert events[0].data == "line1\nline2"


def test_event_field() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "event: message",
        "data: hello",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert events[0].event == "message"
    assert events[0].data == "hello"


def test_id_field() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "id: 123",
        "data: hello",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert events[0].id == "123"


def test_retry_field() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "retry: 5000",
        "data: hello",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert events[0].retry == 5000


def test_empty_data_field() -> None:
    from fi.gateway._streaming import SSEParser

    raw = _make_byte_stream([
        "data:",
        "",
    ])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    assert events[0].data == ""


def test_json_data() -> None:
    import json

    from fi.gateway._streaming import SSEParser

    chunk = {"id": "abc", "choices": [{"delta": {"content": "hi"}}]}
    raw = _make_byte_stream([f"data: {json.dumps(chunk)}", ""])
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    parsed = json.loads(events[0].data)  # type: ignore[arg-type]
    assert parsed["id"] == "abc"


def test_flush_remaining_without_trailing_empty_line() -> None:
    from fi.gateway._streaming import SSEParser

    # No trailing empty line — should still flush
    raw = [b"data: orphan\n"]
    events = list(SSEParser(iter(raw)))
    assert len(events) == 1
    assert events[0].data == "orphan"
