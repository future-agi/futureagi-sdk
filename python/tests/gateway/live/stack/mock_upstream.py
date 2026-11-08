"""OpenAI-compatible mock upstream for the gateway live suites.

The gateway under test (agentcc-gateway at the recorded source) is configured with this
server as its only provider, so no provider key and no network leave the VM.
Standard library only; run it with ``python3 -I mock_upstream.py --port N --log F``.

Behaviour is picked per request by a tag in the last user message,
``[[mock:<scenario>]]``, so a test's prompt says what the upstream does. The
blocklist word the gateway's guardrail matches (``MOCK_BLOCK_WORD``) only ever
appears in an ANSWER: the keyword guardrail also reads request messages, so a
prompt must never carry it.

Every request is recorded (method, path, headers, parsed body); the provider
key the gateway sends is recorded only as the first 12 hex digits of its
sha256. ``GET /__mock/requests?since=N`` returns the records after seq N.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BLOCK_WORD = os.environ.get("MOCK_BLOCK_WORD", "kumquatforbidden")
CHUNK_ID = "chatcmpl-sdk101"  # the ids of tests/fixtures/gateway/stream-error-frames.json
CREATED = 1761177600
FILLER = " " + "lorem ipsum dolor sit amet " * 3  # 82 characters: past check_interval 64
TAG = re.compile(r"\[\[mock:([A-Za-z0-9:_-]+)\]\]")
JSON_ANSWERS = {"json": {"answer": 42, "unit": "none"}, "color-json": {"color": "blue", "hex": "#0000ff"},
                "count-json": {"count": 42}}

_records: list[dict] = []
_lock = threading.Lock()
_log_path: str | None = None


def _hash12(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _record(handler: "Handler", body: object, raw_len: int) -> None:
    headers = {}
    for k, v in handler.headers.items():
        k = k.lower()
        if k == "authorization":
            token = v.split(" ", 1)[1] if " " in v else v
            headers[k] = f"<sha256:{_hash12(token)}>"
        else:
            headers[k] = v
    with _lock:
        rec = {"seq": len(_records) + 1, "t": round(time.time(), 3), "method": handler.command,
               "path": handler.path, "headers": headers, "body": body, "body_bytes": raw_len}
        _records.append(rec)
        if _log_path:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, sort_keys=True) + "\n")


def _scenario(body: object) -> str:
    """The [[mock:...]] tag of the last user message (chat) or of the input (responses)."""
    text = ""
    if isinstance(body, dict):
        msgs = body.get("messages")
        if isinstance(msgs, list):
            for m in reversed(msgs):
                if isinstance(m, dict) and m.get("role") == "user":
                    text = json.dumps(m.get("content"))
                    break
        if not text and "input" in body:
            text = json.dumps(body["input"])
        if not text and "prompt" in body:
            text = json.dumps(body["prompt"])
    m = TAG.search(text)
    return m.group(1) if m else "default"


def _chunk(model: str, delta: dict, finish: str | None = None, usage: dict | None = None) -> dict:
    c = {"id": CHUNK_ID, "object": "chat.completion.chunk", "created": CREATED, "model": model,
         "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
    if usage is not None:
        c["usage"] = usage
    return c


def _usage(prompt: int = 9, completion: int = 2) -> dict:
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}


def chat_stream_frames(model: str, scenario: str) -> tuple[list, float]:
    """(frames, stall seconds after the frames). A frame is a dict or the string [DONE]."""
    role = {"role": "assistant"}
    if scenario == "block-mid":  # mid-stream check: blocked after "Hello world"
        return [_chunk(model, {**role, "content": "Hello"}), _chunk(model, {"content": " world"}),
                _chunk(model, {"content": FILLER + BLOCK_WORD}), _chunk(model, {}, "stop", _usage()), "[DONE]"], 0
    if scenario == "block-finish":  # under check_interval: only the Finish check sees the word
        return [_chunk(model, {**role, "content": "Hello " + BLOCK_WORD}), _chunk(model, {}, "stop"), "[DONE]"], 0
    if scenario == "block-first":  # the first chunk alone passes check_interval
        return [_chunk(model, {**role, "content": BLOCK_WORD + FILLER}), _chunk(model, {}, "stop", _usage()),
                "[DONE]"], 0
    if scenario == "stall":  # a cut by the gateway's deadline after the first chunk
        return [_chunk(model, {**role, "content": "Partial"})], 8.0
    if scenario.startswith("say:") or scenario in JSON_ANSWERS:
        text = answer_text(scenario)
        return [_chunk(model, {**role, "content": text}), _chunk(model, {}, "stop", _usage()), "[DONE]"], 0
    if scenario == "usage-chunk":  # the fixture's usage case: usage on its own choices-[] chunk
        usage_only = {"id": CHUNK_ID, "object": "chat.completion.chunk", "created": CREATED, "model": model,
                      "choices": [], "usage": _usage(9, 1)}
        return [_chunk(model, {**role, "content": "Hello"}), _chunk(model, {}, "stop"), usage_only, "[DONE]"], 0
    if scenario == "no-usage":
        return [_chunk(model, {**role, "content": "Hello"}), _chunk(model, {"content": " world"}),
                _chunk(model, {}, "stop"), "[DONE]"], 0
    # default: the fixture's normal_stream, with usage on the finish chunk (the gateway's
    # stream usage contract)
    return [_chunk(model, {**role, "content": "Hello"}), _chunk(model, {"content": " world"}),
            _chunk(model, {}, "stop", _usage()), "[DONE]"], 0


def answer_text(scenario: str) -> str:
    """The whole answer of a non-stream scenario (``say:<word>`` answers <word>)."""
    if scenario.startswith("say:"):
        return scenario[4:]
    if scenario in JSON_ANSWERS:
        return json.dumps(JSON_ANSWERS[scenario])
    return {"block-mid": "Hello world " + BLOCK_WORD, "block-finish": "Hello " + BLOCK_WORD,
            "block-first": BLOCK_WORD}.get(scenario, "PONG from mock")


def chat_json(model: str, scenario: str) -> dict:
    content = answer_text(scenario)
    return {"id": "chatcmpl-mock-1", "object": "chat.completion", "created": CREATED, "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": _usage(9, 3)}


def responses_events(model: str, scenario: str) -> list[tuple[str, dict]]:
    base = {"id": "resp_mock", "object": "response", "created_at": CREATED, "model": model}
    words = ["Hi", " there"] if not scenario.startswith("block") else ["Hi ", BLOCK_WORD]
    ev = [("response.created", {"type": "response.created", "sequence_number": 0,
                                "response": {**base, "status": "in_progress", "output": []}})]
    for i, w in enumerate(words):
        ev.append(("response.output_text.delta", {"type": "response.output_text.delta", "sequence_number": i + 1,
                                                  "item_id": "msg_1", "output_index": 0, "content_index": 0,
                                                  "delta": w}))
        if scenario == "resp-error":  # the upstream's own error event, after one delta
            ev.append(("error", {"type": "error", "sequence_number": 2, "code": "mock_upstream_error",
                                 "message": "the mock upstream failed mid-stream", "param": None}))
            return ev
    text = "".join(words)
    ev.append(("response.output_text.done", {"type": "response.output_text.done", "sequence_number": 3,
                                             "item_id": "msg_1", "output_index": 0, "content_index": 0, "text": text}))
    ev.append(("response.completed", {"type": "response.completed", "sequence_number": 4,
                                      "response": responses_json(model, text)}))
    return ev


def responses_json(model: str, text: str = "Hi there") -> dict:
    return {"id": "resp_mock", "object": "response", "created_at": CREATED, "model": model, "status": "completed",
            "output": [{"type": "message", "id": "msg_1", "status": "completed", "role": "assistant",
                        "content": [{"type": "output_text", "text": text, "annotations": []}]}],
            "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}


MODELS = ["gpt-4o-mini", "mock-slow", "mock-fails", "text-embedding-3-small", "dall-e-3", "tts-1", "whisper-1"]
# Every request for this model is answered 503, so the gateway's failover moves it down
# the org's model fallback chain (stack_ctl.py org-config, org-fallback).
FAILING_MODEL = "mock-fails"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:  # quiet; records are the log
        return

    def _send_json(self, status: int, obj: object, extra: dict | None = None) -> None:
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _start_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _write(self, text: str) -> None:
        self.wfile.write(text.encode())
        self.wfile.flush()

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/__mock/requests":
            since = int(parse_qs(url.query).get("since", ["0"])[0])
            with _lock:
                out = [r for r in _records if r["seq"] > since]
            self._send_json(200, out)
            return
        _record(self, None, 0)
        if url.path == "/v1/models":
            self._send_json(200, {"object": "list", "data": [{"id": m, "object": "model", "created": CREATED,
                                                              "owned_by": "mock"} for m in MODELS]})
            return
        self._send_json(404, {"error": {"message": f"mock: no route {url.path}", "type": "invalid_request_error",
                                        "code": "not_found"}})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        body: object = None
        if "json" in ctype and raw:
            try:
                body = json.loads(raw)
            except ValueError:
                body = {"_unparsed": raw[:200].decode(errors="replace")}
        elif raw:
            body = {"_multipart_bytes": len(raw), "_content_type": ctype.split(";")[0]}
        _record(self, body, len(raw))
        path = urlparse(self.path).path
        b = body if isinstance(body, dict) else {}
        model = str(b.get("model") or "gpt-4o-mini")
        scenario = _scenario(b)
        if model == FAILING_MODEL:
            self._send_json(503, {"error": {"message": "mock upstream: this model always fails", "type": "mock_error",
                                            "code": "mock_503", "param": None}})
            return
        if scenario.startswith("status:"):
            code = int(scenario.split(":", 1)[1])
            self._send_json(code, {"error": {"message": f"mock upstream answered {code}", "type": "mock_error",
                                             "code": f"mock_{code}", "param": None}})
            return
        if path == "/v1/chat/completions":
            if b.get("stream"):
                frames, stall = chat_stream_frames(model, scenario)
                self._start_sse()
                for f in frames:
                    self._write(f"data: {f if isinstance(f, str) else json.dumps(f)}\n\n")
                    time.sleep(0.02)
                if stall:
                    time.sleep(stall)
                return
            self._send_json(200, chat_json(model, scenario))
        elif path == "/v1/completions":
            if b.get("stream"):
                self._start_sse()
                for text, fin in (("Hello", None), (" world", "stop")):
                    self._write("data: " + json.dumps({"id": "cmpl-mock", "object": "text_completion",
                                                       "created": CREATED, "model": model,
                                                       "choices": [{"index": 0, "text": text,
                                                                    "finish_reason": fin}]}) + "\n\n")
                self._write("data: [DONE]\n\n")
                return
            self._send_json(200, {"id": "cmpl-mock", "object": "text_completion", "created": CREATED, "model": model,
                                  "choices": [{"index": 0, "text": "Hello world", "finish_reason": "stop"}],
                                  "usage": _usage(4, 2)})
        elif path == "/v1/embeddings":
            n = len(b["input"]) if isinstance(b.get("input"), list) else 1
            self._send_json(200, {"object": "list", "model": model, "usage": {"prompt_tokens": 2, "total_tokens": 2},
                                  "data": [{"object": "embedding", "index": i, "embedding": [0.1, 0.2, 0.3]}
                                           for i in range(n)]})
        elif path == "/v1/responses":
            if b.get("stream"):
                self._start_sse()
                for name, data in responses_events(model, scenario):
                    self._write(f"event: {name}\ndata: {json.dumps(data)}\n\n")
                    time.sleep(0.02)
                return
            self._send_json(200, responses_json(model, "Hi " + BLOCK_WORD if scenario.startswith("block")
                                                else "Hi there"))
        elif path == "/v1/images/generations":
            self._send_json(200, {"created": CREATED, "data": [{"b64_json": "aGVsbG8=", "revised_prompt": "mock"}]})
        elif path == "/v1/audio/speech":
            data = b"ID3mock-audio-bytes"
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path in ("/v1/audio/transcriptions", "/v1/audio/translations"):
            self._send_json(200, {"text": "hello from the mock"})
        else:
            self._send_json(404, {"error": {"message": f"mock: no route {path}", "type": "invalid_request_error",
                                            "code": "not_found"}})


def main() -> None:
    global _log_path
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()
    _log_path = args.log
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
