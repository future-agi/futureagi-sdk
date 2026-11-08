"""The Python egress guard trips on production hosts before the inner transport is reached."""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import no_prod_egress as guard_mod  # noqa: E402
from no_prod_egress import (  # noqa: E402
    EgressBlockedError,
    EgressGuard,
    classify_host,
    require_endpoints,
)

try:
    import httpx
except ImportError:  # pragma: no cover - the runner's venv pins httpx
    httpx = None


class ClassifyTests(unittest.TestCase):
    def test_production_hosts_are_refused_even_when_listed(self):
        for host in [
            *guard_mod.NAMED_PRODUCTION_HOSTS,
            "futureagi.com",
            "FutureAGI.com.",
            "x.futureagi.com",
        ]:
            self.assertFalse(classify_host(host, [host])[0], host)
        self.assertFalse(guard_mod.is_production_host("futureagi.com.evil.example"))

    def test_loopback_and_allowlist(self):
        for host in ["127.0.0.1", "localhost", "::1", "[::1]"]:
            self.assertTrue(classify_host(host)[0], host)
        self.assertFalse(classify_host("rig.internal")[0])
        self.assertTrue(classify_host("rig.internal", ["rig.internal"])[0])

    def test_refuses_to_start_when_unset_or_production(self):
        with self.assertRaisesRegex(RuntimeError, "ee is unset"):
            require_endpoints(
                {
                    "gateway": "http://127.0.0.1:1",
                    "ee": None,
                    "exporter": "http://127.0.0.1:2",
                }
            )
        with self.assertRaisesRegex(RuntimeError, "production"):
            require_endpoints(
                {
                    "gateway": "https://api.futureagi.com",
                    "exporter": "http://127.0.0.1:2",
                }
            )


@unittest.skipIf(httpx is None, "httpx is not installed")
class TransportTests(unittest.TestCase):
    def test_trip_before_the_inner_transport(self):
        reached = []
        inner = httpx.MockTransport(
            lambda request: reached.append(request.url.host)
            or httpx.Response(200, text="ok")
        )
        guard = EgressGuard()
        with httpx.Client(transport=guard.transport(inner)) as client:
            for url in [
                "https://api.futureagi.com/x",
                "https://app.futureagi.com/",
                "https://gateway.futureagi.com/y",
            ]:
                with self.assertRaises(EgressBlockedError):
                    client.get(url)
            self.assertEqual(client.get("http://127.0.0.1:9/ok").text, "ok")
        self.assertEqual(reached, ["127.0.0.1"])
        self.assertEqual(len(guard.trips), 3)
        with self.assertRaises(EgressBlockedError):
            guard.assert_not_tripped()

    def test_async_transport(self):
        inner = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))
        guard = EgressGuard()

        async def run():
            async with httpx.AsyncClient(
                transport=guard.async_transport(inner)
            ) as client:
                with self.assertRaises(EgressBlockedError):
                    await client.get("https://api.futureagi.com/")
                return (await client.get("http://localhost/ok")).text

        self.assertEqual(asyncio.run(run()), "ok")
        self.assertTrue(guard.tripped)

    def test_exporter_guard(self):
        exported = []

        class Exporter:
            def export(self, spans):
                exported.append(spans)

        guard = EgressGuard(allow=["collector.rig"])
        guard.wrap_exporter(Exporter(), "http://collector.rig:4318").export(["s"])
        self.assertEqual(exported, [["s"]])
        with self.assertRaises(EgressBlockedError):
            guard.wrap_exporter(Exporter(), "https://api.futureagi.com/tracer")


if __name__ == "__main__":
    unittest.main()
