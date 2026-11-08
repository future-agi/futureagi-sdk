"""Cloud-run regression and fallibility checks for the consumer harness."""
import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifacts import absence_checks, names_safe
from catalog import applies, catalog, legs, SURFACES
from matrix import build, state
from network import RegistryProxy, RuntimeGuard, loopback
from probe_common import mock_backend
from run import effective_policy


def policy():
    return effective_policy({"states": {name: {"py": "OFF", "ts": "OFF"} for name in SURFACES},
                             "python_entries": ["fi:FutureAGIClient"], "node_entries": ["."]})


class MatrixTests(unittest.TestCase):
    def test_every_namespace_has_three_distinct_leg_variants(self):
        self.assertEqual(len(catalog()), 20)
        entries = legs()
        self.assertEqual(len(entries), 60)
        self.assertEqual(len({e["id"] for e in entries}), 60)
        for entry in entries:
            self.assertEqual(entry["if_absent"], "NOT-EVALUATED")
            self.assertEqual(entry["gate_kind"], "absence" if entry["variant"] == "absence" else "capability")
            self.assertIn("served:", entry["applies_when"])
            self.assertIn("admitted:", entry["applies_when"])
        self.assertEqual({r["authoritative_journey"] for r in catalog() if "authoritative_journey" in r}, {"J23", "J30"})

    def test_unbound_is_never_a_pass(self):
        rows = build({}, policy(), {}, {"py": [], "ts": []}, ["N00"], {"denied_count": 0})
        self.assertTrue(all(r["state"] == "NOT-EVALUATED" for r in rows))

    def test_unknown_binding_grammar_is_rejected(self):
        with self.assertRaises(ValueError):
            applies("env:enabled", {})
        self.assertFalse(applies("served:datasets & admitted:sdk", {"served": ["datasets"]}))

    def test_failure_and_missing_evidence_dominate_pass(self):
        self.assertEqual(state([]), "NOT-EVALUATED")
        self.assertEqual(state([{"state": "PASS"}, {"state": "NOT-EVALUATED"}]), "NOT-EVALUATED")
        self.assertEqual(state([{"state": "PASS"}, {"state": "FAIL"}]), "FAIL")

    def test_egress_contaminates_an_otherwise_green_install(self):
        probes = {f"py-{v}-{extra}": {"checks": [{"name": "install.import", "state": "PASS"}]}
                  for v in ("3.10", "3.12") for extra in ("base", "evals", "tracing")}
        binding = {"served": ["sdk-artifacts"], "admitted": ["sdk"]}
        green = build(binding, policy(), probes, {"py": [], "ts": []}, ["N00"], {"denied_count": 0})
        red = build(binding, policy(), probes, {"py": [], "ts": []}, ["N00"], {"denied_count": 1})
        self.assertEqual(green[0]["state"], "PASS")
        self.assertEqual(red[0]["state"], "FAIL")

    def test_missing_required_runtime_never_aggregates_to_pass(self):
        probes = {"py-3.12-base": {"checks": [{"name": "install.import", "state": "PASS"}]}}
        rows = build({"served": ["sdk-artifacts"], "admitted": ["sdk"]}, policy(), probes,
                     {"py": [], "ts": []}, ["N00"], {"denied_count": 0})
        self.assertEqual(rows[0]["state"], "NOT-EVALUATED")

    def test_missing_config_after_install_failure_remains_unevaluated(self):
        probes = {"ts-20": {"checks": [{"name": "config.default-client", "state": "PASS"}]},
                  "ts-22": {"checks": [{"name": "install.dependencies", "state": "FAIL"}]}}
        rows = build({"served": ["sdk-config"], "admitted": ["sdk"]}, policy(), probes,
                     {"py": [], "ts": []}, ["N01"], {"denied_count": 0})
        self.assertEqual(next(r["state"] for r in rows if r["id"] == "N01" and r["variant"] == "ts"), "NOT-EVALUATED")

    def test_served_backend_does_not_promote_a_scaffold(self):
        binding = {"served": ["datasets"], "admitted": ["sdk"]}
        rows = build(binding, policy(), {}, {"py": [], "ts": []}, ["N02"], {"denied_count": 0})
        self.assertTrue(all(r["state"] == "NOT-EVALUATED" for r in rows if r["id"] == "N02"))

    def test_absence_does_not_promote_capability(self):
        binding = {"served": ["sdk-artifacts"], "admitted": ["sdk"]}
        p = policy()
        inventory = {"py": [], "ts": [], "package": {"exports": {}}, "docs": ""}
        archive = {lang: absence_checks(inventory, p, lang) for lang in ("py", "ts")}
        rows = build(binding, p, {}, archive, ["N00"], {"denied_count": 0})
        self.assertTrue(all(r["state"] == "NOT-EVALUATED" for r in rows if r["id"] == "N02"))

    def test_hidden_bytes_and_exports_fail_even_without_import(self):
        inventory = {"py": ["fi/gateway/_client.py"], "ts": ["package/dist/esm/gateway/client.js"],
                     "package": {"exports": {"./gateway": {}}}, "docs": ""}
        for lang in ("py", "ts"):
            rows = absence_checks(inventory, policy(), lang)
            self.assertEqual(next(r["state"] for r in rows if r["name"] == "absence.gateway.archive"), "FAIL")
        self.assertEqual(next(r["state"] for r in rows if r["name"] == "absence.gateway.export-map"), "FAIL")

    def test_documentation_is_not_silently_omitted(self):
        inventory = {"py": [], "ts": [], "package": {}, "docs": "from fi.gateway import AgentCC"}
        p = policy()
        self.assertEqual(next(r["state"] for r in absence_checks(inventory, p, "py") if r["name"] == "absence.gateway.docs"), "NOT-EVALUATED")
        p["docs_complete"] = True
        self.assertEqual(next(r["state"] for r in absence_checks(inventory, p, "py") if r["name"] == "absence.gateway.docs"), "FAIL")

    def test_archive_traversal_and_duplicates_are_refused(self):
        for paths in (["../outside"], ["/absolute"], ["a", "a"], ["a\\b"]):
            with self.assertRaises(ValueError):
                names_safe(paths)

    def test_policy_requires_all_languages_explicitly(self):
        with self.assertRaises(ValueError):
            effective_policy({"states": {}})

    def test_registry_proxy_refuses_without_upstream_contact(self):
        with RegistryProxy() as proxy:
            for host in ("api.futureagi.com", "api.openai.com", "metadata.google.internal", "127.0.0.1"):
                with socket.create_connection(("127.0.0.1", proxy.port)) as connection:
                    connection.sendall(f"CONNECT {host}:443 HTTP/1.0\r\n\r\n".encode())
                    self.assertIn(b"403", connection.recv(1024))
            self.assertEqual(proxy.result()["denied_count"], 4)

    def test_runtime_guard_counts_before_dns_or_socket(self):
        guard = RuntimeGuard()
        for host in ("api.futureagi.com", "api.openai.com", "169.254.169.254", "localhost.example"):
            with self.assertRaises(PermissionError):
                guard.check(host)
        self.assertEqual(guard.result()["denied_count"], 4)
        self.assertTrue(loopback("::1"))
        self.assertTrue(loopback("127.0.0.1"))
        self.assertFalse(loopback("127.0.0.1.example"))

    def test_python_socket_hook_rejects_real_call_before_send(self):
        code = "import sys,socket;sys.path.insert(0,sys.argv[1]);from network import RuntimeGuard;g=RuntimeGuard();g.install()\ntry: socket.create_connection(('203.0.113.1',443))\nexcept PermissionError: pass\nassert g.result()['denied_count']==1"
        subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).parent)], check=True)

    def test_missing_observer_fails_attempted_cells(self):
        rows = build({'served': ['sdk-artifacts'], 'admitted': ['sdk']}, policy(),
                     {'ts-20': {'checks': [{'name': 'install.control', 'state': 'PASS'}]}},
                     {'py': [], 'ts': []}, ['N00'], {'denied_count': 0, 'complete': False})
        self.assertEqual(next(r['state'] for r in rows if r['id'] == 'N00' and r['variant'] == 'ts'), 'FAIL')

    def test_syscall_accounting_includes_failed_and_batched_destinations(self):
        from container_network import summarize
        lines = [
            '101 connect(4, {sa_family=AF_INET, sin_port=htons(8000), sin_addr=inet_addr("172.18.0.1")}, 16) = 0\n',
            '102 sendmmsg(4, [{msg_name={sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("203.0.113.1")}}, {msg_name={sa_family=AF_INET6, sin6_port=htons(53), inet_pton(AF_INET6, "2001:db8::1", &sin6_addr)}}], 2, 0) = -1 ENETUNREACH\n',
            '103 connect(4, {sa_family=AF_INET, sin_port=htons(8000), sin_addr=inet_addr("172.18.0.1")}, 16 <unfinished ...>\n',
            '104 sendto(4, "", 1, 0, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("127.0.0.11")}, 16) = -1 EINVAL\n',
            '105 connect(4, {sa_family=AF_INET, sin_port=htons(43210), sin_addr=inet_addr("127.0.0.1")}, 16) = 0\n',
        ]
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'network.trace'
            trace.write_text(''.join(lines))
            result = summarize(trace, len(lines[0]), ('172.18.0.1', 8000))
        self.assertTrue(result['complete'])
        self.assertEqual(result['denied_count'], 4)
        self.assertEqual(result['allowed_count'], 2)
        self.assertTrue(all(r['phase'] == 'runtime' for r in result['denied']))

    def test_session_only_personal_fixture_issuer(self):
        with mock_backend() as backend:
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(backend.url + "/__fixture/personal-keys", data=b"{}"))
            self.assertEqual(error.exception.code, 403)
            session = json.load(urlopen(Request(backend.url + "/__fixture/session", data=b"{}")))["session"]
            pair = json.load(urlopen(Request(backend.url + "/__fixture/personal-keys", data=b"{}", headers={"Authorization": "Bearer " + session})))
            self.assertEqual(pair["type"], "user")
            self.assertTrue(backend.minted)
            self.assertFalse(backend.requests)


if __name__ == "__main__":
    unittest.main()
