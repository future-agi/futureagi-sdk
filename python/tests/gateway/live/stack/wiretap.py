"""A recording reverse proxy in front of the gateway.

The live suites point a client at this tap when a test asserts what the SDK
itself puts on the wire (headers, body, no ``stream_options``, no FI key pair,
the stock OpenAI SDK's ``OpenAI-Organization``). Every request is recorded and
forwarded unchanged to the gateway; the answer streams back as it arrives
(``read1``), so SSE works through the tap. Bearer tokens are recorded only as the
first 12 hex digits of their sha256.

    python3 -I wiretap.py --port 8091 --target 127.0.0.1:8090 --log F

``GET /__tap/requests?since=N`` returns the records after seq N.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOP = {"connection", "keep-alive", "proxy-connection", "transfer-encoding", "te", "trailer", "upgrade", "host",
       "content-length"}
_records: list[dict] = []
_lock = threading.Lock()
_target = ("127.0.0.1", 8090)
_log_path: str | None = None


def _hash12(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


class Tap(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _records_route(self) -> bool:
        url = urlparse(self.path)
        if url.path != "/__tap/requests":
            return False
        since = int(parse_qs(url.query).get("since", ["0"])[0])
        with _lock:
            data = json.dumps([r for r in _records if r["seq"] > since]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True

    def _proxy(self) -> None:
        if self.command == "GET" and self._records_route():
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        headers = {}
        for k, v in self.headers.items():
            lk = k.lower()
            if lk == "authorization":
                token = v.split(" ", 1)[1] if " " in v else v
                headers[lk] = f"<sha256:{_hash12(token)}>"
            else:
                headers[lk] = v
        body: object = None
        if raw and "json" in self.headers.get("Content-Type", ""):
            try:
                body = json.loads(raw)
            except ValueError:
                body = {"_unparsed_bytes": len(raw)}
        elif raw:
            body = {"_bytes": len(raw), "_content_type": self.headers.get("Content-Type", "").split(";")[0]}
        with _lock:
            rec = {"seq": len(_records) + 1, "t": round(time.time(), 3), "method": self.command, "path": self.path,
                   "headers": headers, "header_names": [k for k in self.headers.keys()], "body": body}
            _records.append(rec)
            if _log_path:
                with open(_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, sort_keys=True) + "\n")
        conn = http.client.HTTPConnection(*_target, timeout=120)
        fwd = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        if raw:
            fwd["Content-Length"] = str(len(raw))
        conn.request(self.command, self.path, body=raw or None, headers=fwd)
        resp = conn.getresponse()
        self.send_response(resp.status, resp.reason)
        for k, v in resp.getheaders():
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        while True:
            chunk = resp.read1(65536)
            if not chunk:
                break
            self.wfile.write(chunk)
            self.wfile.flush()
        conn.close()

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _proxy


def main() -> None:
    global _target, _log_path
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--target", default="127.0.0.1:8090")
    ap.add_argument("--log", default=None)
    args = ap.parse_args()
    host, port = args.target.rsplit(":", 1)
    _target = (host, int(port))
    _log_path = args.log
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Tap)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
