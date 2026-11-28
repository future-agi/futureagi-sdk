"""Child process for ``test_plaintext_oracle_conformance``: sends with the SDK's own marker keys, row by row.

Run as ``python -m tests.experiments.unit.oracle_probe <transport> [--unguarded]`` with a resolver shim that maps
every host name to the loopback address (``LD_PRELOAD``), and the rows of the sealed oracle as JSON on stdin (a list of
``{"id", "row"}`` objects). It prints one JSON object per row.

For each row the probe starts three loopback listeners: the target (``{T}``) and two sinks that answer a ``CONNECT``
(``{A}``, ``{B}``). It sets the row's environment and drives the SDK's own transport (the OTLP HTTP exporter, the OTLP
gRPC exporter, or the evaluation-configuration request) with a marker key and secret. Each listener counts the bytes
it receives and whether they hold a marker. Nothing leaves the machine and no real host is named.

``--unguarded`` replaces the SDK's plain-http decision (the shared rule of ``fi._core.http_security`` and the OTLP
opt-in step) with one that allows everything (a test-only bypass), to show that the counters see the marker bytes when
the guard does not stop the send.
"""

import contextlib
import gzip
import json
import os
import socket
import sys
import threading
import types
import time

KEY = b"fi-oracle-marker-key-7c1d9e"
SECRET = b"fi-oracle-marker-secret-4b82aa"
MARKERS = (KEY, SECRET)
SETTINGS = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"
OK = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Type: application/json\r\n\r\n{}"
ORACLE = os.path.join(os.path.dirname(__file__), "fixtures", "plaintext-rule-oracle.json.gz")

CODES = {"disputed_authority": "insecure_http_origin", "empty_authority": "insecure_http_origin"}


class Sink:
    """A loopback listener that counts what it receives. With ``connect_aware`` it opens a tunnel for ``CONNECT``."""

    def __init__(self, connect_aware, redirect=None, reply=None):
        self.connect_aware = connect_aware
        self.reply = reply  # answer every request with these bytes
        self.redirect = redirect  # answer every request with a 302 to this URL
        self.data = []
        self.connections = 0
        self.first_at = None
        self.stop = threading.Event()
        self.socks = []
        self.socks = self.bind_both()
        self.port = self.socks[0].getsockname()[1]
        for sock in self.socks:
            sock.listen(16)
            sock.settimeout(0.1)
            threading.Thread(target=self.serve, args=(sock,), daemon=True).start()

    @staticmethod
    def bind_both():
        """One port on ``127.0.0.1`` and on ``::1`` together (another process may hold the port on one of them);
        only ``127.0.0.1`` when the machine has no ``::1``."""
        for _ in range(50):
            v4 = socket.socket()
            v4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            v4.bind(("127.0.0.1", 0))
            try:
                v6 = socket.socket(socket.AF_INET6)
                v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                v6.bind(("::1", v4.getsockname()[1]))
            except OSError:
                v4.close()
                continue
            return [v4, v6]
        v4 = socket.socket()
        v4.bind(("127.0.0.1", 0))
        return [v4]

    def serve(self, sock):
        while not self.stop.is_set():
            try:
                conn, _ = sock.accept()
            except OSError:
                continue
            self.connections += 1
            self.first_at = self.first_at or time.monotonic()
            threading.Thread(target=self.talk, args=(conn,), daemon=True).start()

    def talk(self, conn):
        conn.settimeout(0.2)
        data, answered = b"", False
        deadline = time.monotonic() + 1.2
        while time.monotonic() < deadline and len(data) < 65536 and not self.stop.is_set():
            try:
                chunk = conn.recv(4096)
            except TimeoutError:
                continue
            except OSError:
                break
            if not chunk:
                break
            data += chunk
            self.data.append(chunk)
            if data.startswith(b"CONNECT ") and self.connect_aware and b"\r\n\r\n" in data:
                data = data.split(b"\r\n\r\n", 1)[1]
                with contextlib.suppress(OSError):
                    conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            if data.startswith(b"PRI ") and not answered:
                answered = True
                with contextlib.suppress(OSError):
                    conn.sendall(SETTINGS)
            elif data[:1] == b"\x16":
                break
            elif b"\r\n\r\n" in data and data.split(b" ", 1)[0] in (b"POST", b"GET", b"PUT") and not answered:
                answered = True
                reply = self.reply or OK if self.redirect is None else (
                    f"HTTP/1.1 302 Found\r\nLocation: {self.redirect}\r\nContent-Length: 0\r\n\r\n".encode())
                with contextlib.suppress(OSError):
                    conn.sendall(reply)
        with contextlib.suppress(OSError):
            conn.close()

    @property
    def marker_bytes(self):
        blob = b"".join(self.data)
        return sum(blob.count(marker) for marker in MARKERS)

    def close(self):
        self.stop.set()
        for sock in self.socks:
            with contextlib.suppress(OSError):
                sock.close()


def no_proxy_value(kind, authority):
    """The ``NO_PROXY`` value for one of the oracle's pattern names. The oracle names the patterns and not their
    text, so the values are reconstructed to give the libraries' facts the oracle recorded: ``exact`` and ``bare``
    are the host as written (no brackets for an IPv6 address), ``dot_suffix`` the last two labels behind a dot (an
    address behind a dot as it is), ``host_port`` the host with the port, ``cidr`` two address ranges."""
    if authority.startswith("["):
        host, port = authority[1:authority.index("]")], authority.rsplit(":", 1)[1]
    else:
        host, port = authority.rsplit(":", 1) if ":" in authority else (authority, "")
    labels = host.split(".")
    numeric = all(label.isdigit() or not label for label in labels)
    suffix = "." + (host if numeric or len(labels) < 2 else ".".join(labels[-2:]))
    return {"exact": host, "bare": host, "dot_suffix": suffix, "star": "*", "host_port": f"{host}:{port}",
            "cidr": "127.0.0.0/8,10.0.0.0/8", "empty_both": ""}[kind]


def reset_environment(row, dims, ports, authority):
    for name in list(os.environ):
        lowered = name.lower()
        if name.startswith(("OTEL_", "FI_", "GRPC_")) or lowered in (
                "http_proxy", "https_proxy", "no_proxy", "grpc_proxy", "no_grpc_proxy", "all_proxy"):
            del os.environ[name]
    os.environ.update({"FI_API_KEY": KEY.decode(), "FI_SECRET_KEY": SECRET.decode(),
                       "OTEL_EXPORTER_OTLP_TIMEOUT": "1", "GRPC_DNS_RESOLVER": "native",
                       "FI_LOGIN_FILE": "/nonexistent/login.json"})
    value = dims["opt_in"][row["opt_in"]] if row["opt_in"] in dims["opt_in"] else None
    if value is not None:
        os.environ["FI_ALLOW_INSECURE_HTTP"] = value
    for name, text in dims["env_values"][row["env"]].items():
        os.environ[name] = text.replace("{A}", str(ports["A"])).replace("{B}", str(ports["B"]))
    if row["no_proxy"] != "none":
        value = no_proxy_value(row["no_proxy"], authority)
        os.environ["NO_PROXY"] = value
        if row["no_proxy"] == "empty_both":
            os.environ["no_proxy"] = value
    if row["source"] == "otel_insecure_env":
        os.environ["OTEL_EXPORTER_OTLP_INSECURE"] = "true"


def endpoint_for(transport, row, host, port):
    authority = host["authority"].replace("{T}", str(port))
    path = host["path"]
    tail = "" if path == "/" else path
    if transport == "grpc":
        if row["source"] == "http_scheme":
            return f"http://{authority}{tail}", authority
        return f"{authority}{tail}", authority
    scheme = "https" if row["source"] == "tls" else "http"
    return f"{scheme}://{authority}{path}", authority


def caller_session(kind, ports):
    """A caller-supplied client for the evaluation-configuration request."""
    import requests
    import requests.adapters
    from requests_futures.sessions import FuturesSession

    from fi.utils.executor import BoundedExecutor

    session = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1))
    if kind == "client_with_proxy":
        session.proxies = {"http": f"http://127.0.0.1:{ports['A']}", "https": f"http://127.0.0.1:{ports['A']}"}
    else:
        class Opaque(requests.adapters.HTTPAdapter):
            """An adapter the SDK cannot inspect: it routes every request through its own proxy."""

            def send(self, request, **kwargs):
                kwargs["proxies"] = {"http": f"http://127.0.0.1:{ports['B']}", "https": f"http://127.0.0.1:{ports['B']}"}
                return super().send(request, **kwargs)

        session.mount("http://", Opaque())
        session.mount("https://", Opaque())
    return session


def drive(transport, row, host, ports, endpoint, result):
    """Build the SDK's transport for the row and send once. Fills ``decision`` and ``code`` of ``result``."""
    from fi.errors import ConfigurationError

    done = threading.Event()
    failure = []

    def send(call):
        try:
            call()
        except Exception as error:  # noqa: BLE001 - the send may fail on the wire; only what reached a sink counts
            failure.append(error)
        finally:
            done.set()

    call = None
    exporter = None
    try:
        if transport == "eval-config":
            from fi.evals.evaluator import Evaluator

            arguments = {}
            if row["caller"] in ("client_with_proxy", "uninspectable_transport"):
                arguments["session"] = caller_session(row["caller"], ports)
            client = Evaluator(fi_api_key=KEY.decode(), fi_secret_key=SECRET.decode(), fi_base_url=endpoint, **arguments)
            call = lambda: client._configure_evaluations(  # noqa: E731
                "template", {"input": "x"}, "other", "check", span_id="0" * 16, trace_id="0" * 32)
        elif transport == "http":
            from fi.evals.otel._tracer_factories import _create_exporter
            from fi.evals.otel.config import ExporterConfig, ExporterType

            exporter = _create_exporter(ExporterConfig(type=ExporterType.FUTUREAGI, endpoint=endpoint, timeout_ms=1000))
            call = lambda: export_through(exporter)  # noqa: E731
        else:
            from fi.evals.otel._tracer_factories import _create_exporter
            from fi.evals.otel.config import ExporterConfig, ExporterType

            insecure = {"tls": False, "insecure_argument": True}.get(row["source"])
            exporter = _create_exporter(ExporterConfig(
                type=ExporterType.OTLP_GRPC, endpoint=endpoint, insecure=insecure, timeout_ms=1000,
                headers={"x-api-key": KEY.decode(), "x-secret-key": SECRET.decode()}))
            call = lambda: export_through(exporter)  # noqa: E731
    except ConfigurationError as refused:
        result.update(decision="refuse", code=refused.code)
        return
    except Exception as error:  # noqa: BLE001
        result.update(decision="error", code=type(error).__name__)
        return
    thread = threading.Thread(target=send, args=(call,), daemon=True)
    thread.start()
    # The first connection decides the route; the rest of the exchange only has to finish or time out.
    started = time.monotonic()
    while time.monotonic() - started < 5.0 and not done.is_set():
        time.sleep(0.02)
        if any(sink.connections for sink in ports["sinks"].values()) and time.monotonic() - started > 0.15:
            break
    time.sleep(0.05)
    if exporter is not None:
        # Shut down the exporter so its retries do not reach a later row's listener.
        with contextlib.suppress(Exception):
            exporter.shutdown()
    thread.join(1.5)
    if failure and isinstance(failure[0], ConfigurationError):
        # The evaluation request is decided when it is sent.
        result.update(decision="refuse", code=failure[0].code)
    else:
        result.update(decision="build", code=None)


def export_through(exporter):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.get_tracer("oracle").start_span("one").end()
    provider.shutdown()


def measure(transport, index, row, oracle):
    dims = oracle["dimensions"]
    host = dims["hosts"][row["host"]]
    sinks = {"T": Sink(False), "A": Sink(True), "B": Sink(True)}
    ports = {name: sink.port for name, sink in sinks.items()}
    ports["sinks"] = sinks
    result = {"id": index}
    try:
        endpoint, authority = endpoint_for(transport, row, host, ports["T"])
        reset_environment(row, dims, ports, authority)
        drive(transport, row, host, ports, endpoint, result)
        time.sleep(0.05)
    finally:
        for sink in sinks.values():
            sink.close()
    first = min((s.first_at, name) for name, s in sinks.items() if s.first_at)[1] if any(
        s.first_at for s in sinks.values()) else None
    result["route"] = {None: None, "T": "target", "A": "proxy", "B": "proxy"}[first]
    result["marker_bytes"] = {name: sink.marker_bytes for name, sink in sinks.items()}
    result["connections"] = {name: sink.connections for name, sink in sinks.items()}
    return result


def main():
    transport = sys.argv[1]
    if "--unguarded" in sys.argv:
        # The shared rule (``fi._core.http_security``) decides every plain-http send, and the OTLP header checks keep
        # their own opt-in step: both are replaced by one that allows everything.
        from fi import _otlp_headers
        from fi._core import http_security

        _otlp_headers._require_plain_opt_in = lambda *args, **kwargs: None
        http_security.insecure_http_allowed = lambda *args, **kwargs: True
        http_security.plaintext_decision = lambda *args, **kwargs: http_security.PlaintextDecision(True, "opted_in")
    # The retry wait of the evaluation request is not part of what is measured.
    import fi.api.auth as auth

    auth.time = types.SimpleNamespace(sleep=lambda seconds: None)
    with gzip.open(ORACLE, "rt") as handle:
        oracle = json.load(handle)
    for item in json.load(sys.stdin):
        print(json.dumps(measure(transport, item["id"], oracle["rows"][item["id"]], oracle)), flush=True)


if __name__ == "__main__":
    main()
