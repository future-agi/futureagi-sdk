"""Probe assertions and an ephemeral personal-identity loopback fixture."""
import json
import secrets
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Checks:
    def __init__(self):
        self.rows = []

    def run(self, name, action):
        try:
            action()
            self.rows.append({"name": name, "state": "PASS"})
        except Exception as exc:
            # Exception bodies can contain credentials. Preserve the class, not text.
            self.rows.append({"name": name, "state": "FAIL", "reason": type(exc).__name__})

    def skip(self, name, reason):
        self.rows.append({"name": name, "state": "NOT-EVALUATED", "reason": reason})


def demand(value):
    if not value:
        raise AssertionError("Probe invariant failed")


def refused(action, classes):
    try:
        action()
    except Exception as error:
        demand(type(error).__name__ in classes)
    else:
        raise AssertionError("Expected typed refusal")


def member(root, path):
    for part in path.split("."):
        root = getattr(root, part)
    return root


def provision(backend):
    """Explicit session-only mint on the local fixture; never a production issuer."""
    from urllib.request import Request, urlopen
    def post(path, token=None):
        headers = {"Authorization": "Bearer " + token} if token else {}
        with urlopen(Request(backend.url + path, data=b"{}", headers=headers), timeout=5) as response:
            return json.load(response)
    session = post("/__fixture/session")["session"]
    pair = post("/__fixture/personal-keys", session)
    demand(pair["type"] == "user")
    return pair


@contextmanager
def mock_backend():
    class State:
        session = secrets.token_urlsafe(18)
        api = "personal-fixture-" + secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(24)
        requests = []
        minted = False

    state = State()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path == "/__fixture/session":
                return self.reply(200, {"session": state.session})
            if self.path == "/__fixture/personal-keys":
                if self.headers.get("Authorization") != "Bearer " + state.session:
                    return self.reply(403, {})
                state.minted = True
                return self.reply(201, {"api_key": state.api, "secret_key": state.secret, "type": "user"})
            return self.do_GET()

        def do_GET(self):
            headers = {k.lower(): v for k, v in self.headers.items()}
            state.requests.append({"path": self.path, "headers": headers})
            if self.path.startswith("/accounts/keys/"):
                return self.reply(410, {"detail": "Retired route"})
            valid = (state.minted and headers.get("x-api-key") == state.api and
                     headers.get("x-secret-key") == state.secret)
            if not valid:
                return self.reply(403, {"detail": "Personal credentials required"})
            if self.path.startswith("/accounts/user-info/"):
                return self.reply(200, {"id": "fixture-person", "email": "person@example.invalid"})
            return self.reply(200, {"status": "success", "result": [], "data": [], "items": [], "count": 0, "results": []})

        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state.url = f"http://127.0.0.1:{server.server_port}"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
