"""A real HTTP server on 127.0.0.1 that answers like the webhooks API for the CLI tests: it records every request
(method, path, query, JSON body, headers) and answers from a route table. It stands in for the API only in unit tests; the
live end-to-end run drives the CLI against the platform itself."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import parse_qs, urlsplit

Route = Tuple[int, Any]
HANGUP = "hangup"  # a route answer: read the request, then close the connection without a response


class Stub:
    def __init__(self) -> None:
        self.routes: Dict[Tuple[str, str], Any] = {}
        self.seen: List[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:  # quiet
                pass

            def _serve(self) -> None:
                url = urlsplit(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                req = {
                    "method": self.command,
                    "path": url.path,
                    "query": {k: v[0] for k, v in parse_qs(url.query).items()},
                    "body": json.loads(raw) if raw else None,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                }
                stub.seen.append(req)
                answer = stub.routes.get((self.command, url.path))
                if answer == HANGUP:
                    self.close_connection = True
                    return
                if answer is None:
                    status, payload = 404, {"status": False, "code": "WEBHOOK_NOT_FOUND", "message": "not found"}
                elif callable(answer):
                    status, payload = answer(req)
                else:
                    status, payload = answer
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = _serve

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "Stub":
        self.thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.server.shutdown()
        self.server.server_close()

    def on(self, method: str, path: str, answer: "Route | Callable[[dict], Route]") -> None:
        self.routes[(method, path)] = answer

    def calls(self, method: str, path: str) -> List[dict]:
        return [r for r in self.seen if r["method"] == method and r["path"] == path]


def ok(result: Any, status: int = 200) -> Route:
    return status, {"status": True, "result": result}


def refuse(status: int, code: str, attr: str = None) -> Route:  # type: ignore[assignment]
    body = {"status": False, "type": "validation_error", "code": code, "message": f"{code} message",
            "detail": f"{code} message", "error": f"{code} message", "result": f"{code} message"}
    if attr:
        body["attr"] = attr
    return status, body
