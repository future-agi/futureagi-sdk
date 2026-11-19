"""The process-wide guard trips for clients the SDK builds itself, before any DNS query or connect."""

import asyncio
import http.server
import importlib
import os
import socket
import sys
import threading
import unittest
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from no_prod_egress import EgressBlockedError, EgressGuard  # noqa: E402
from no_prod_egress_process import (  # noqa: E402
    NativeNetworkingRefused,
    install_process_guard,
)

try:
    import httpx
except ImportError:  # pragma: no cover - the runner's venv pins httpx
    httpx = None


class CountingResolver:
    """Stands in for the real getaddrinfo, so a test proves no lookup left the process."""

    def __init__(self, real, fake=None):
        self.real = real
        self.fake = fake or {}
        self.calls = []

    def __call__(self, host, port, *args, **kwargs):
        self.calls.append(host)
        name = host.decode() if isinstance(host, bytes) else host
        if name in self.fake:
            return [
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    (self.fake[name], port or 0),
                )
            ]
        return self.real(host, port, *args, **kwargs)


class ProcessGuardTests(unittest.TestCase):
    def setUp(self):
        self.real_getaddrinfo = socket.getaddrinfo
        self.resolver = CountingResolver(
            self.real_getaddrinfo, {"rig.internal": "10.9.8.7"}
        )
        socket.getaddrinfo = (
            self.resolver
        )  # the guard captures this as the inner lookup
        self.guard = EgressGuard(allow=["rig.internal"])
        self.process = install_process_guard(self.guard)

    def tearDown(self):
        self.process.uninstall()
        self.assertIs(
            socket.getaddrinfo, self.resolver, "uninstall puts the lookup back"
        )
        socket.getaddrinfo = self.real_getaddrinfo
        self.assertNotIn(
            "connect", vars(socket.socket), "uninstall removes the class patch it added"
        )

    def hosts(self):
        return [t["host"] for t in self.guard.trips]

    def test_a_raw_socket_trips_by_name_and_by_address(self):
        with self.assertRaises(EgressBlockedError):
            socket.create_connection(("api.futureagi.com", 443), timeout=1)
        with self.assertRaises(EgressBlockedError):
            socket.create_connection(
                ("203.0.113.9", 9), timeout=1
            )  # TEST-NET-3: an address, no lookup
        sock = socket.socket()
        try:
            with self.assertRaises(EgressBlockedError):
                sock.connect(("gateway.futureagi.com", 443))
            with self.assertRaises(EgressBlockedError):
                sock.connect_ex(("198.51.100.7", 9))
        finally:
            sock.close()
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            with self.assertRaises(EgressBlockedError):
                udp.sendto(b"x", ("192.0.2.53", 53))
        finally:
            udp.close()
        self.assertEqual(
            self.hosts(),
            [
                "api.futureagi.com",
                "203.0.113.9",
                "gateway.futureagi.com",
                "198.51.100.7",
                "192.0.2.53",
            ],
        )
        self.assertEqual(
            self.resolver.calls, [], "a refused name or address is never looked up"
        )

    def test_an_address_an_allowed_name_resolved_to_is_allowed(self):
        socket.getaddrinfo("rig.internal", 80)
        self.process.admit_address(("10.9.8.7", 80), "test")
        with self.assertRaises(EgressBlockedError):
            self.process.admit_address(("10.9.8.8", 80), "test")
        self.process.admit_address("/tmp/x.sock", "test")  # AF_UNIX: local
        self.assertEqual(self.hosts(), ["10.9.8.8"])

    def test_urllib_raises_the_guard_error_not_a_urlerror(self):
        for url in ["http://bypass-probe2.invalid:9/", "https://app.futureagi.com/"]:
            with self.assertRaises(EgressBlockedError):
                urllib.request.urlopen(url, timeout=2)
        self.assertEqual(self.hosts(), ["bypass-probe2.invalid", "app.futureagi.com"])
        self.assertEqual(self.resolver.calls, [])

    @unittest.skipIf(httpx is None, "httpx is not installed")
    def test_an_sdks_own_httpx_client_trips(self):
        with httpx.Client(timeout=2, trust_env=False) as client:
            for url in [
                "http://bypass-probe.invalid:9/",
                "https://api.futureagi.com/tracer/v1/traces",
            ]:
                with self.assertRaises(EgressBlockedError):
                    client.get(url)
        self.assertEqual(self.hosts(), ["bypass-probe.invalid", "api.futureagi.com"])
        self.assertEqual(self.resolver.calls, [])

    @unittest.skipIf(httpx is None, "httpx is not installed")
    def test_async_clients_trip_through_the_event_loop_lookup(self):
        async def run():
            with self.assertRaises(EgressBlockedError):
                await asyncio.open_connection("bypass-async.invalid", 9)
            async with httpx.AsyncClient(timeout=2, trust_env=False) as client:
                with self.assertRaises(EgressBlockedError):
                    await client.get("https://gateway.futureagi.com/x")

        asyncio.run(run())
        self.assertEqual(
            self.hosts(), ["bypass-async.invalid", "gateway.futureagi.com"]
        )

    def test_a_swallowed_trip_is_still_recorded(self):
        try:
            urllib.request.urlopen("http://swallowed.invalid/", timeout=1)
        except Exception:  # an SDK that catches everything
            pass
        self.assertTrue(self.guard.tripped)
        with self.assertRaises(EgressBlockedError):
            self.guard.assert_not_tripped()

    def test_native_networking_modules_are_refused_at_import(self):
        for name in ["grpc", "grpc.experimental", "pycurl"]:
            sys.modules.pop(name, None)
            with self.assertRaises(NativeNetworkingRefused) as caught:
                importlib.import_module(name)
            self.assertIsInstance(
                caught.exception, ImportError
            )  # an optional import degrades
        self.assertEqual(
            self.process.describe()["refusedImports"], ["grpc", "grpc", "pycurl"]
        )
        self.assertEqual({t["via"] for t in self.guard.trips}, {"import"})

    def test_loopback_still_works(self):
        class Ok(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Ok)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/"
            self.assertEqual(urllib.request.urlopen(url, timeout=5).read(), b"ok")
            self.assertEqual(
                urllib.request.urlopen(
                    url.replace("127.0.0.1", "localhost"), timeout=5
                ).read(),
                b"ok",
            )
            if httpx is not None:
                with httpx.Client(trust_env=False) as client:
                    self.assertEqual(client.get(url).text, "ok")
        finally:
            server.shutdown()
            server.server_close()
        self.assertFalse(self.guard.tripped, self.guard.trips)


if __name__ == "__main__":
    unittest.main()
