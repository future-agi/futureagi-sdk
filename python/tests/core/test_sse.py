"""The SSE parser (ported from the Omega runtime tests): any split of the bytes yields
the same frames.

The fuzz cuts one stream at random byte offsets 10,000 times (inside CRLF pairs, inside multi-byte
UTF-8 characters, inside the BOM) and requires the identical frame list every time.
"""

from __future__ import annotations

import random
import unittest

from fi._core.sse import SseFrame, SseParser, decode_frame

STREAM = (
    "﻿"
    ": keepalive\n\n"
    'id: 1\nevent: message_delta\ndata: {"messageId":"m1","delta":"héllo wörld \U0001F600"}\r\n\r\n'
    "event: activity\r\ndata: line one\r\ndata: line two\r\r"
    "data: no id, last id stays 1\n\n"
    'id: 2\ndata: {"type":"status","status":"running"}\n\n'
    "retry: 3000\ndata: x\n\n"
    "data:no space after colon\n\n"
    "event: ignored-no-data\n\n"
    "id: 3\ndata: 漢字とかな\n\n"
    "data: an incomplete final block is dropped"
).encode("utf-8")


def parse(chunks: list[bytes]) -> list[SseFrame]:
    parser = SseParser()
    frames: list[SseFrame] = []
    for chunk in chunks:
        frames.extend(parser.push(chunk))
    frames.extend(parser.end())
    return frames


def split(data: bytes, rng: random.Random) -> list[bytes]:
    cuts = sorted(rng.sample(range(1, len(data)), rng.randint(1, min(40, len(data) - 1))))
    pieces, last = [], 0
    for cut in cuts:
        pieces.append(data[last:cut])
        last = cut
    pieces.append(data[last:])
    return pieces


class Parser(unittest.TestCase):
    def test_reference_frames(self) -> None:
        frames = parse([STREAM])
        self.assertEqual(
            [f.event for f in frames],
            ["message_delta", "activity", "message", "message", "message", "message", "message"],
        )
        self.assertEqual(frames[0].id, "1")
        self.assertIn("\U0001F600", frames[0].data)
        self.assertEqual(frames[1].data, "line one\nline two")
        self.assertIsNone(frames[1].id)
        self.assertEqual(frames[2].last_event_id, "1")
        self.assertIsNone(frames[2].id)
        self.assertEqual(frames[3].id, "2")
        self.assertEqual(frames[4].retry, 3000)
        self.assertEqual(frames[5].data, "no space after colon")
        self.assertEqual(frames[6].data, "漢字とかな")

    def test_fuzz_10000_random_splits_yield_identical_frames(self) -> None:
        reference = parse([STREAM])
        rng = random.Random(20261020)
        for i in range(10_000):
            chunks = split(STREAM, rng)
            self.assertEqual(parse(chunks), reference, f"split #{i}: {[len(c) for c in chunks]}")

    def test_byte_by_byte(self) -> None:
        self.assertEqual(parse([bytes([byte]) for byte in STREAM]), parse([STREAM]))

    def test_comments_are_counted_as_keepalives(self) -> None:
        parser = SseParser()
        parser.push(b": ping\n\n: ping\n\n")
        self.assertEqual(parser.comments, 2)

    def test_an_id_with_nul_is_ignored(self) -> None:
        frames = parse([b"id: a\x00b\ndata: x\n\n"])
        self.assertIsNone(frames[0].id)


class Decode(unittest.TestCase):
    KNOWN = ("message_delta", "status")

    def test_known_event_from_the_event_line(self) -> None:
        event = decode_frame(SseFrame("message_delta", '{"messageId":"m","delta":"a"}', "4", "4"), self.KNOWN)
        self.assertEqual(event, {"messageId": "m", "delta": "a", "type": "message_delta"})

    def test_known_event_from_the_type_field(self) -> None:
        event = decode_frame(SseFrame("message", '{"type":"status","status":"ok"}', None, ""), self.KNOWN)
        self.assertEqual(event["type"], "status")

    def test_unknown_event_type_is_yielded_never_raised(self) -> None:
        event = decode_frame(SseFrame("hologram", '{"a":1}', None, ""), self.KNOWN)
        self.assertEqual(event, {"type": "unknown", "eventType": "hologram", "raw": {"a": 1}})

    def test_non_json_data_is_an_unknown_event(self) -> None:
        event = decode_frame(SseFrame("status", "not json", None, ""), self.KNOWN)
        self.assertEqual(event, {"type": "unknown", "eventType": "status", "raw": "not json"})
