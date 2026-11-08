"""Registry-only installation proxy and loopback-only runtime audit guard."""
import ipaddress
import json
import select
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REGISTRIES = frozenset(("pypi.org", "files.pythonhosted.org", "registry.npmjs.org"))


def loopback(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(str(host).strip("[]")).is_loopback
    except ValueError:
        return False


class RuntimeGuard:
    def __init__(self):
        self.denied = []
        self.allowed = 0

    def check(self, host):
        if loopback(host):
            self.allowed += 1
            return
        self.denied.append({"host": str(host), "phase": "runtime"})
        raise PermissionError("Consumer network guard refused a non-loopback destination")

    def install(self):
        def audit(event, args):
            if event == "socket.getaddrinfo":
                self.check(args[0])
            elif event in ("socket.connect", "socket.sendto"):
                sock, address = args[0], args[-1]
                if sock.family in (socket.AF_INET, socket.AF_INET6):
                    self.check(address[0])
        sys.addaudithook(audit)

    def result(self):
        return {"denied_count": len(self.denied), "denied": self.denied, "loopback_count": self.allowed}


class RegistryProxy:
    """Only TLS registry tunnels. No credential handling or request-body logging."""
    def __init__(self):
        self.events = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_CONNECT(self):
                host, sep, port = self.path.rpartition(":")
                accepted = bool(sep) and port == "443" and host in REGISTRIES
                owner.events.append({"host": host, "allowed": accepted})
                if not accepted:
                    self.send_error(403, "Only public package registries are allowed")
                    return
                try:
                    with socket.create_connection((host, 443), timeout=30) as remote:
                        self.send_response(200)
                        self.end_headers()
                        peers = (self.connection, remote)
                        while True:
                            ready, _, _ = select.select(peers, [], [], 90)
                            if not ready:
                                return
                            for source in ready:
                                data = source.recv(65536)
                                if not data:
                                    return
                                (remote if source is self.connection else self.connection).sendall(data)
                except OSError:
                    return

            def do_GET(self):
                owner.events.append({"host": "non-CONNECT", "allowed": False})
                self.send_error(403)

            do_POST = do_GET

        self.server = ThreadingHTTPServer(("0.0.0.0", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    @property
    def port(self):
        return self.server.server_port

    def result(self):
        return {"denied_count": sum(not e["allowed"] for e in self.events), "events": self.events}
