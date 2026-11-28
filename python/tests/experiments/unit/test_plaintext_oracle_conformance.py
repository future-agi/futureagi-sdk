"""The sealed shared oracle for the plain-transport rule, driven through this SDK's own transports.

``fixtures/plaintext-rule-oracle.json.gz`` is the vendored oracle (58,787 rows). The
test asserts both of its sha256 values, then drives every row that applies to this SDK's transports through the SDK's
own code and compares the SDK's answer with the row: refuse or build, the error code, and the route the first
connection took.

* ``http``: the OTLP HTTP exporter for Future AGI (``ExporterType.FUTUREAGI``) with the SDK's keys from the environment.
* ``grpc``: the OTLP gRPC exporter (``ExporterType.OTLP_GRPC``) with the SDK's key headers.
* ``eval-config``: the evaluation-configuration request of ``fi.evals.Evaluator``.

The SDK builds these transports itself, so the rows whose caller supplies a client (``client_with_proxy``,
``uninspectable_transport``) apply to ``eval-config`` only, the one request that takes a caller's session.

The oracle's ``key_bytes_at_sink: 0`` for a refused row is the expected value, not a measurement. Here the keys are
measured: the probe sends with the SDK's own marker key and secret to loopback listeners (the target and two sinks that
answer ``CONNECT``) that count the bytes they receive, and the test fails on any marker byte at any listener for a
refused row, and at a proxy sink for any row. The last test shows that the counters work: with the opt-in decision
replaced by one that allows everything, the marker bytes reach the target.

Error codes: the oracle's ``disputed_authority`` and ``empty_authority`` are this SDK's ``insecure_http_origin``.
One code per situation: the codes of the shared senders decide, and the oracle's decisions are kept and mapped to them
(``SDK_CODES``). The oracle's refuse or build decision is compared as it is. Over TLS, a loopback host is reached
directly whatever the proxy settings say, loopback only (the host as written is an address in 127.0.0.0/8, ``::1`` or
``localhost``); the oracle's route for those rows is read as ``target``. A name that only resolves to loopback keeps the
oracle's route.

The SDK differs from the oracle for ``s1_at_in_path`` rows without TLS: the SDK rejects a target with ``@`` in
its path with ``insecure_http_origin`` because some parsers read the ``@`` as user information. The oracle reads
it as part of the path. TLS rows for the same host must match the oracle.

NO_PROXY texts: the oracle names its patterns (``exact``, ``bare``, ``dot_suffix``, ``host_port``, ``cidr``) and does not
give their text, so the probe reconstructs them to reproduce the libraries' recorded facts. A row that uses one of these
reconstructed texts is a derived row and is tallied apart from the rows whose environment the oracle states in full. A
derived row that differs fails like any other.
"""

import collections
import gzip
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

import pytest

from tests.core.test_localhost_direct_dial_grpc import shim_compiler

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
ORACLE_GZ = FIXTURES / "plaintext-rule-oracle.json.gz"
GZ_SHA256 = "bb75798b5c34c68e428ca9b31a17c8df33bfdede43844dd36ff728f70552d1eb"
JSON_SHA256 = "c2072ae9e74dc80543e10fabaf54da26554bf12d3033c7bbe46067cf8aac4f1e"
PROBE = "tests.experiments.unit.oracle_probe"
PYTHON_ROOT = pathlib.Path(__file__).resolve().parents[3]
TRANSPORTS = ("http", "grpc", "eval-config")
CODES = {"disputed_authority": "insecure_http_origin", "empty_authority": "insecure_http_origin"}
# One code per situation: the codes of the shared senders decide (the table of scripts/compat/keyed_sender_equality.py
# against 0.7.1), and the oracle's decisions are kept. The oracle code, read through ``CODES``, maps to the SDK code of
# the same situation. Keyed on (transport, oracle code); an oracle code that is not listed must match as it is.
SDK_CODES = {
    # a plain target of another host without the opt-in
    ("http", "insecure_self_hosted_target"): "insecure_http_origin",
    ("grpc", "insecure_self_hosted_target"): "insecure_http_origin",
    ("eval-config", "insecure_self_hosted_target"): "insecure_http_origin",
    # a plain target on a Future AGI host
    ("http", "insecure_futureagi_http"): "INSECURE_HTTP_REFUSED",
    ("grpc", "insecure_futureagi_grpc"): "INSECURE_HTTP_REFUSED",
    ("eval-config", "insecure_futureagi_http"): "INSECURE_HTTP_REFUSED",
    # a request that a proxy would carry
    ("eval-config", "proxied"): "KEYED_PROXY_REFUSED",
}
# Classes where the SDK refuses and the oracle builds: none. The table of the equality script lists no stricter
# refusal for these transports.
STRICTER = {}


def sdk_code(transport, code):
    """The SDK's code for the situation the oracle names with ``code``."""
    code = CODES.get(code, code)
    return SDK_CODES.get((transport, code), code)
WORKERS = max(2, min(24, (os.cpu_count() or 4) - 2))
PROBE_SECONDS = 1800
# Whichever test first asks the shared measurement for a transport waits for all of that transport's rows (the
# eval-config rows take 250 to 750 s on a loaded machine), so a 300 s suite timeout would stop it in the middle. Each
# test here carries a limit above the probe's own deadline; every row is still driven and checked.
pytestmark = pytest.mark.timeout(PROBE_SECONDS + 300)
SHIM = r"""
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <dlfcn.h>
#include <netdb.h>
#include <netinet/in.h>
#include <string.h>
#include <sys/socket.h>

int getaddrinfo(const char *node, const char *service, const struct addrinfo *hints, struct addrinfo **res) {
    static int (*real)(const char *, const char *, const struct addrinfo *, struct addrinfo **);
    struct in_addr v4;
    struct in6_addr v6;
    if (!real) real = dlsym(RTLD_NEXT, "getaddrinfo");
    if (node && !inet_pton(AF_INET, node, &v4) && !inet_pton(AF_INET6, node, &v6)) node = "127.0.0.1";
    return real(node, service, hints, res);
}

/* The oracle's private address maps to the local listener. */
int connect(int fd, const struct sockaddr *addr, socklen_t len) {
    static int (*real)(int, const struct sockaddr *, socklen_t);
    struct sockaddr_in local;
    struct sockaddr_in6 mapped;
    if (!real) real = dlsym(RTLD_NEXT, "connect");
    if (addr && addr->sa_family == AF_INET && len >= sizeof(local)) {
        memcpy(&local, addr, sizeof(local));
        if (local.sin_addr.s_addr == htonl(0x0a000001)) {
            local.sin_addr.s_addr = htonl(0x7f000001);
            return real(fd, (const struct sockaddr *)&local, len);
        }
    }
    if (addr && addr->sa_family == AF_INET6 && len >= sizeof(mapped)) {
        memcpy(&mapped, addr, sizeof(mapped));
        if (IN6_IS_ADDR_V4MAPPED(&mapped.sin6_addr) && memcmp(&mapped.sin6_addr.s6_addr[12], "\x0a\x00\x00\x01", 4) == 0) {
            memcpy(&mapped.sin6_addr.s6_addr[12], "\x7f\x00\x00\x01", 4);
            return real(fd, (const struct sockaddr *)&mapped, len);
        }
    }
    return real(fd, addr, len);
}
"""


@pytest.fixture(scope="module")
def shim(tmp_path_factory):
    command = shim_compiler()
    directory = tmp_path_factory.mktemp("oracle_shim")
    source = directory / "shim.c"
    source.write_text(SHIM)
    library = directory / "shim.so"
    subprocess.run([*command, "-shared", "-fPIC", "-o", str(library), str(source), "-ldl"], check=True)
    return library


def load_oracle():
    with gzip.open(ORACLE_GZ, "rt") as handle:
        return json.load(handle)


ORACLE = load_oracle()
ROWS = ORACLE["rows"]
HOSTS = ORACLE["dimensions"]["hosts"]


def applies(transport, row):
    """The SDK builds the OTLP exporters itself; only the evaluation request takes a caller's session."""
    if row["transport"] != transport:
        return False
    return transport == "eval-config" or row["caller"] in ("none", "*")


EXCEPTION_DESCRIPTION = "at sign after authority without TLS"
DERIVED_NO_PROXY = ("exact", "bare", "dot_suffix", "host_port", "cidr")


def is_ruled_exception(row):
    """The comparison allows a difference only for non-TLS rows with the s1_at_in_path host."""
    return row["host"] == "s1_at_in_path" and row["source"] != "tls"


def is_derived(row):
    """The row's environment holds a ``NO_PROXY`` text that the probe reconstructed (see the module text)."""
    return row["no_proxy"] in DERIVED_NO_PROXY


APPLICABLE = {transport: [i for i, row in enumerate(ROWS) if applies(transport, row)] for transport in TRANSPORTS}
EXCEPTIONS = {transport: [i for i in ids if is_ruled_exception(ROWS[i])] for transport, ids in APPLICABLE.items()}


LIBRARY = {"http": "requests", "grpc": "grpcio", "eval-config": "requests"}


def is_unmeasured(row):
    """A TLS row that builds whose ``dialed`` the oracle did not measure for this SDK's library: its facts hold no
    entry for it (the gRPC cells of ``s1_at_in_path``), so ``dialed: proxy`` stands for "unknown counts as proxied" and
    is not a route that was seen. Its decision and code are still compared; its route is not."""
    return (row["decision"] == "build" and row["tls"] and row["caller"] in ("none", "*")
            and any(LIBRARY[row["transport"]] not in ORACLE["facts"][key] for key in row["fact_keys"]))


def is_literal_loopback_row(row):
    """A row whose host, as written, is an address in 127.0.0.0/8, ``::1`` or the name ``localhost``. Such a TLS row is
    dialed direct: the oracle's proxy route for it is read as ``target``. A name that only resolves to loopback
    (``wnl_*``) is not one: it keeps the oracle's route."""
    return row["host"].startswith("lo_")


def expected(row):
    """What the row says the SDK answers. A row that builds over TLS names, in ``proxied_by``, the sending libraries
    whose own routing sends the connection through the environment's proxy (``dialed`` is the union over them), so
    this SDK's route follows its own library: ``requests`` for the HTTP exporter and the evaluation request, ``grpcio``
    for the gRPC exporter. A caller's own client dials its own proxy whatever the environment says."""
    if row["decision"] == "refuse":
        return {"decision": "refuse", "code": sdk_code(row["transport"], row["error"]), "route": None}
    route = {"target": "target", "proxy": "proxy"}[row["dialed"]]
    if row["tls"] and row["caller"] in ("none", "*"):
        route = "proxy" if LIBRARY[row["transport"]] in row["proxied_by"] else "target"
        if is_literal_loopback_row(row):
            route = "target"  # direct, loopback only: the host as written is a loopback literal or localhost
    return {"decision": "build", "code": None, "route": route}


def run_probe(shim, transport, ids, tmp, *extra):
    environment = {**os.environ, "LD_PRELOAD": str(shim), "PYTHONPATH": str(PYTHON_ROOT)}
    children = []
    for index in range(WORKERS):
        chunk = [{"id": i} for i in ids[index::WORKERS]]
        if not chunk:
            continue
        out, err = tmp / f"{transport}-{index}.out", tmp / f"{transport}-{index}.err"
        with out.open("w") as out_file, err.open("w") as err_file:
            child = subprocess.Popen([sys.executable, "-m", PROBE, transport, *extra], stdin=subprocess.PIPE,
                                     stdout=out_file, stderr=err_file, text=True, cwd=PYTHON_ROOT, env=environment)
        child.stdin.write(json.dumps(chunk))
        child.stdin.close()
        children.append((child, out, err))
    return children


def collect(children):
    found = {}
    deadline = time.monotonic() + PROBE_SECONDS
    for child, out, err in children:
        child.wait(max(1, deadline - time.monotonic()))
        assert child.returncode == 0, err.read_text()[-2000:]
        for line in out.read_text().splitlines():
            if line.startswith("{"):
                item = json.loads(line)
                found[item["id"]] = item
    return found


@pytest.fixture(scope="module")
def measured(shim, tmp_path_factory, request):
    """Every applicable row of each selected transport, measured. The children of the transports that the selected
    tests ask for start together, when the first test asks; a transport asked for later starts then."""
    tmp = tmp_path_factory.mktemp("oracle_rows")
    selected = {item.callspec.params.get("transport") for item in request.session.items
                if getattr(item, "module", None) is request.module and hasattr(item, "callspec")}
    running = {transport: run_probe(shim, transport, ids, tmp)
               for transport, ids in APPLICABLE.items() if transport in selected}
    found = {}

    def get(transport):
        if transport not in running:
            running[transport] = run_probe(shim, transport, APPLICABLE[transport], tmp)
        if transport not in found:
            found[transport] = collect(running[transport])
        return found[transport]

    yield get
    for children in running.values():
        for child, _out, _err in children:
            if child.poll() is None:
                child.kill()


def test_the_vendored_oracle_is_the_sealed_one():
    assert hashlib.sha256(ORACLE_GZ.read_bytes()).hexdigest() == GZ_SHA256
    assert hashlib.sha256(gzip.decompress(ORACLE_GZ.read_bytes())).hexdigest() == JSON_SHA256
    assert len(ROWS) == 58787


def test_the_ruled_exception_holds_plain_cells_of_one_host_only():
    # The exception covers one host without TLS, with a specific row count for each transport.
    assert {ROWS[i]["host"] for ids in EXCEPTIONS.values() for i in ids} == {"s1_at_in_path"}
    assert all(ROWS[i]["source"] != "tls" and ROWS[i]["tls"] is not True for ids in EXCEPTIONS.values() for i in ids)
    assert {transport: len(ids) for transport, ids in EXCEPTIONS.items()} == {"http": 96, "grpc": 96, "eval-config": 144}
    tls_cells = {transport: len([i for i in ids if ROWS[i]["host"] == "s1_at_in_path" and ROWS[i]["source"] == "tls"])
                 for transport, ids in APPLICABLE.items()}
    assert tls_cells == {"http": 8, "grpc": 8, "eval-config": 12}


def test_the_loopback_tls_rows_read_as_direct_are_the_literal_hosts_whose_oracle_route_is_the_proxy():
    """The rows whose oracle route is ``proxy`` and that this SDK dials direct, loopback only (the literal hosts)."""
    read = {transport: [i for i, row in enumerate(ROWS) if applies(transport, row) and row["decision"] == "build"
                        and row["tls"] and row["caller"] in ("none", "*") and is_literal_loopback_row(row)
                        and LIBRARY[row["transport"]] in row["proxied_by"]]
            for transport in TRANSPORTS}
    assert {transport: len(ids) for transport, ids in read.items()} == {"http": 52, "grpc": 96, "eval-config": 52}
    assert {ROWS[i]["host"] for ids in read.values() for i in ids} <= {"lo_127", "lo_localhost", "lo_upper", "lo_v6"}
    assert all(expected(ROWS[i])["route"] == "target" for ids in read.values() for i in ids)


def test_a_name_that_resolves_to_loopback_keeps_the_oracle_route():
    """A name that is not a loopback literal as written (it only resolves to loopback) keeps the proxy rules: the
    expected route of its TLS rows is the proxy for the libraries the oracle says use it."""
    names = [i for i, row in enumerate(ROWS) if row["host"].startswith("wnl_") and row["decision"] == "build"
             and row["tls"] and row["caller"] in ("none", "*") and applies(row["transport"], row)
             and LIBRARY[row["transport"]] in row["proxied_by"]]
    assert names and all(expected(ROWS[i])["route"] == "proxy" for i in names)


def test_the_rows_compared_without_a_route_are_the_unmeasured_grpc_cells():
    ids = [i for i, row in enumerate(ROWS) if applies(row["transport"], row) and is_unmeasured(row)]
    assert len(ids) == 8 and {(ROWS[i]["transport"], ROWS[i]["host"], ROWS[i]["source"]) for i in ids} == {
        ("grpc", "s1_at_in_path", "tls")}, ids


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_the_sdk_refuses_every_ruled_cell_as_ambiguous_with_no_marker_byte(measured, transport):
    got = measured(transport)
    code = sdk_code(transport, "insecure_http_origin")
    wrong = [i for i in EXCEPTIONS[transport]
             if (got[i]["decision"], got[i]["code"]) != ("refuse", code)
             or any(got[i]["marker_bytes"].values())]
    assert not wrong, wrong[:5]


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_every_applicable_row_was_driven(measured, transport):
    assert set(measured(transport)) == set(APPLICABLE[transport])
    assert {item["decision"] for item in measured(transport).values()} <= {"build", "refuse"}


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_the_sdk_answers_every_row_as_the_oracle_does(measured, transport):
    got = measured(transport)
    counts = collections.Counter()
    mismatches = []
    for i in APPLICABLE[transport]:
        row, item = ROWS[i], got[i]
        counts["driven"] += 1
        if is_ruled_exception(row):
            counts["ruled_exception"] += 1
            continue
        want = expected(row)
        if is_unmeasured(row):
            counts["unmeasured_route"] += 1
            want = {**want, "route": None}
            item = {**item, "route": None}
        if {"decision": item["decision"], "code": item["code"], "route": item["route"] if want["route"] else None} == want:
            counts["derived" if is_derived(row) else "matched"] += 1
        else:
            mismatches.append((i, "derived" if is_derived(row) else "stated", row["host"], row["source"], row["opt_in"],
                               row["env"], row["no_proxy"], row["caller"], want,
                               {k: item[k] for k in ("decision", "code", "route")}))
    print(f"\nconformance {transport} ({EXCEPTION_DESCRIPTION}): driven {counts['driven']} matched {counts['matched']} "
          f"derived {counts['derived']} ruled_exception {counts['ruled_exception']} "
          f"(of the matched and derived rows, {counts['unmeasured_route']} compared without a route)")
    assert counts["driven"] == len(APPLICABLE[transport])
    assert counts["driven"] == counts["matched"] + counts["derived"] + counts["ruled_exception"] + len(mismatches)
    assert not mismatches, f"{len(mismatches)} rows differ, first ones: {mismatches[:12]}"


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_a_refused_row_puts_no_marker_byte_at_any_listener(measured, transport):
    got = measured(transport)
    leaked = [i for i in APPLICABLE[transport]
              if ROWS[i]["decision"] == "refuse" and any(got[i]["marker_bytes"].values())]
    assert not leaked, f"{len(leaked)} refused rows sent marker bytes, first: {[(i, got[i]) for i in leaked[:5]]}"


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_no_row_puts_a_marker_byte_at_a_proxy_sink(measured, transport):
    got = measured(transport)
    sent = [i for i in APPLICABLE[transport] if got[i]["marker_bytes"]["A"] or got[i]["marker_bytes"]["B"]]
    assert not sent, f"{len(sent)} rows sent marker bytes to a proxy, first: {[(i, ROWS[i]['host'], got[i]) for i in sent[:5]]}"


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_a_plain_row_that_builds_sends_its_keys_to_the_target(measured, transport):
    got = measured(transport)
    plain = [i for i in APPLICABLE[transport]
             if ROWS[i]["decision"] == "build" and ROWS[i]["tls"] is False and ROWS[i]["transport"] == transport
             and not is_ruled_exception(ROWS[i])]
    silent = [i for i in plain if not got[i]["marker_bytes"]["T"]]
    # gRPC may not send headers within the probe window; HTTP sends its headers within that window.
    assert len(silent) <= (len(plain) // 4 if transport == "grpc" else 0), silent[:5]


# A refused self-managed row, with and without a proxy in the environment: what the counters read once the opt-in
# decision allows everything.
UNGUARDED = {
    transport: [i for i in APPLICABLE[transport]
                if ROWS[i]["decision"] == "refuse" and ROWS[i]["error"] == "insecure_self_hosted_target"
                and ROWS[i]["host"] == "self_collector" and ROWS[i]["opt_in"] == "unset"
                and ROWS[i]["no_proxy"] == "none" and ROWS[i]["source"] == "http_scheme"
                and ROWS[i]["env"] in ("none", "HTTP_PROXY")][:2]
    for transport in TRANSPORTS
}


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_the_counters_see_the_marker_when_the_send_is_not_guarded(shim, tmp_path, transport):
    ids = UNGUARDED[transport]
    assert ids
    with tempfile.TemporaryDirectory() as directory:
        got = collect(run_probe(shim, transport, ids, pathlib.Path(directory), "--unguarded"))
    for i in ids:
        assert got[i]["decision"] == "build"
        assert sum(got[i]["marker_bytes"].values()) > 0, got[i]
