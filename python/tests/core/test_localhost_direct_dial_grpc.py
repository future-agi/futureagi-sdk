"""A gRPC channel to the name ``localhost`` dials 127.0.0.1 or ``::1``, and a name that resolves to loopback follows the
proxy rules. gRPC resolves names in C, so the resolver replacement here is a preloaded library, as in the oracle
conformance tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

from tests.core._localhost_dial import (  # noqa: F401
    KEY, LOOPBACK_ADDRESSES, PROXY_ENV, SECRET, Sink, proxy, target,
)


# --- the gRPC target -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("endpoint,rebuilt", [
    ("localhost:4317", "127.0.0.1:4317"),
    ("LOCALHOST:4317", "127.0.0.1:4317"),
    ("http://localhost:4317", "http://127.0.0.1:4317"),
    ("https://localhost:4317/path", "https://127.0.0.1:4317/path"),
])
def test_a_grpc_target_named_localhost_dials_a_loopback_address_and_keeps_the_name_for_the_certificate(endpoint, rebuilt):
    from fi._core.loopback import grpc_dial_target

    dialed, options = grpc_dial_target(endpoint)
    assert dialed == rebuilt
    assert dict(options) == {"grpc.default_authority": "localhost:4317", "grpc.ssl_target_name_override": "localhost"}


@pytest.mark.parametrize("endpoint", [
    "127.0.0.1:4317", "[::1]:4317", "localhost.:4317", "app.localhost:4317", "collector.example:4317", "127.1:4317",
    "http://localhost.:4317", "", None,
])
def test_a_grpc_target_that_is_not_the_name_localhost_is_unchanged(endpoint):
    from fi._core.loopback import grpc_dial_target

    assert grpc_dial_target(endpoint) == (endpoint, ())


def test_a_grpc_target_named_localhost_with_user_information_is_unchanged():
    from fi._core.loopback import grpc_dial_target

    assert grpc_dial_target("user@localhost:4317") == ("user@localhost:4317", ())


SHIM = r"""
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <dlfcn.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>

int getaddrinfo(const char *node, const char *service, const struct addrinfo *hints, struct addrinfo **res) {
    static int (*real)(const char *, const char *, const struct addrinfo *, struct addrinfo **);
    if (!real) real = dlsym(RTLD_NEXT, "getaddrinfo");
    if (node && strcasecmp(node, "localhost") == 0) node = "198.51.100.1";
    if (node && strcmp(node, "loop.test") == 0) node = "127.0.0.1";
    return real(node, service, hints, res);
}

static void note(const char *text) {
    const char *log = getenv("FI_SHIM_LOG");
    FILE *f = log ? fopen(log, "a") : NULL;
    if (f) { fputs(text, f); fputc('\n', f); fclose(f); }
}

int connect(int fd, const struct sockaddr *addr, socklen_t len) {
    static int (*real)(int, const struct sockaddr *, socklen_t);
    char text[96] = "";
    struct sockaddr_in a4;
    struct sockaddr_in6 a6;
    if (!real) real = dlsym(RTLD_NEXT, "connect");
    if (addr && addr->sa_family == AF_INET && len >= sizeof(a4)) {
        memcpy(&a4, addr, sizeof(a4));
        inet_ntop(AF_INET, &a4.sin_addr, text, sizeof text);
        note(text);
        if (a4.sin_addr.s_addr == htonl(0xc6336401)) {
            a4.sin_addr.s_addr = htonl(0x7f000001);
            return real(fd, (const struct sockaddr *)&a4, len);
        }
    } else if (addr && addr->sa_family == AF_INET6 && len >= sizeof(a6)) {
        memcpy(&a6, addr, sizeof(a6));
        inet_ntop(AF_INET6, &a6.sin6_addr, text, sizeof text);
        note(text);
        if (IN6_IS_ADDR_V4MAPPED(&a6.sin6_addr) && memcmp(&a6.sin6_addr.s6_addr[12], "\xc6\x33\x64\x01", 4) == 0) {
            memcpy(&a6.sin6_addr.s6_addr[12], "\x7f\x00\x00\x01", 4);
            return real(fd, (const struct sockaddr *)&a6, len);
        }
    }
    return real(fd, addr, len);
}
"""

GRPC_CHILD = r"""
import sys
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from fi.evals.otel._tracer_factories import _create_exporter
from fi.evals.otel.tracer import ExporterConfig, ExporterType

memory = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(memory))
provider.get_tracer("t").start_span("s").end()
exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=sys.argv[1],
                                           headers={"x-api-key": sys.argv[2], "x-secret-key": sys.argv[3]}, timeout_ms=2000))
exporter.export(memory.get_finished_spans())
"""


def _compiler() -> Optional[list[str]]:
    import shutil

    for name in ("gcc", "cc", "clang"):
        found = shutil.which(name)
        if found:
            return [found]
    try:
        import ziglang  # noqa: F401
    except ImportError:
        return None
    return [sys.executable, "-m", "ziglang", "cc"]


# Set to 1 where the resolver shim must build (CI): with no C compiler the shim tests fail rather than skip.
REQUIRE_SHIM_ENV = "FI_REQUIRE_RESOLVER_SHIM"


def shim_compiler() -> list[str]:
    """The command that builds the resolver shim; with none, skip the test, or fail it when ``REQUIRE_SHIM_ENV`` is 1"""
    command = _compiler()
    if command is not None:
        return command
    reason = "no C compiler for the resolver shim (gcc, cc, clang or the ziglang module)"
    if os.environ.get(REQUIRE_SHIM_ENV) == "1":
        pytest.fail(f"{reason}, and {REQUIRE_SHIM_ENV}=1 requires the shim", pytrace=False)
    pytest.skip(reason)


def _without_a_compiler(monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name, *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "ziglang", None)


def test_a_required_resolver_shim_with_no_c_compiler_fails_the_test(monkeypatch):
    from tests.core import test_localhost_direct_dial_grpc as module

    _without_a_compiler(monkeypatch)
    monkeypatch.setenv("FI_REQUIRE_RESOLVER_SHIM", "1")

    assert module._compiler() is None
    with pytest.raises(pytest.fail.Exception, match="FI_REQUIRE_RESOLVER_SHIM"):
        module.shim_compiler()


def test_a_resolver_shim_with_no_c_compiler_skips_the_test_when_not_required(monkeypatch):
    from tests.core import test_localhost_direct_dial_grpc as module

    _without_a_compiler(monkeypatch)
    monkeypatch.delenv("FI_REQUIRE_RESOLVER_SHIM", raising=False)

    with pytest.raises(pytest.skip.Exception, match="no C compiler"):
        module.shim_compiler()


@pytest.fixture(scope="module")
def shim_library(tmp_path_factory) -> Path:
    command = shim_compiler()
    pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    directory = tmp_path_factory.mktemp("localhost_shim")
    (directory / "shim.c").write_text(SHIM)
    library = directory / "shim.so"
    subprocess.run([*command, "-shared", "-fPIC", "-o", str(library), str(directory / "shim.c"), "-ldl"], check=True)
    return library


def _run_grpc(shim_library: Path, endpoint: str, tmp_path: Path, extra: Optional[dict] = None) -> list[str]:
    log = tmp_path / "connects.log"
    log.write_text("")
    env = {k: v for k, v in os.environ.items() if k not in PROXY_ENV}
    env.update(LD_PRELOAD=str(shim_library), FI_SHIM_LOG=str(log), GRPC_DNS_RESOLVER="native",
               PYTHONPATH=str(Path(__file__).resolve().parents[2]), **(extra or {}))
    subprocess.run([sys.executable, "-c", GRPC_CHILD, endpoint, KEY, SECRET], env=env, timeout=60, capture_output=True,
                   cwd=str(tmp_path))
    return [line for line in log.read_text().splitlines() if line]


@pytest.mark.parametrize("with_proxy", [False, True], ids=["no-proxy", "env-proxy"])
def test_a_grpc_channel_to_localhost_dials_loopback_whatever_the_resolver_answers(shim_library, tmp_path, target, proxy, with_proxy):
    extra = {}
    if with_proxy:
        extra = {name: f"http://127.0.0.1:{proxy.port}" for name in ("HTTPS_PROXY", "https_proxy", "GRPC_PROXY", "grpc_proxy")}
    connects = _run_grpc(shim_library, f"localhost:{target.port}", tmp_path, extra)
    assert "198.51.100.1" not in connects, connects
    assert connects and set(connects) <= LOOPBACK_ADDRESSES | {"::ffff:127.0.0.1"}, connects
    assert target.connections >= 1
    assert target.marker_bytes == 0 and proxy.connections == 0 and proxy.marker_bytes == 0
    assert b"localhost" in target.raw  # the certificate name stays as written


def test_a_grpc_channel_to_a_name_that_resolves_to_loopback_goes_through_the_environment_proxy(shim_library, tmp_path, target, proxy):
    extra = {name: f"http://127.0.0.1:{proxy.port}" for name in ("HTTPS_PROXY", "https_proxy", "GRPC_PROXY", "grpc_proxy")}
    _run_grpc(shim_library, f"loop.test:{target.port}", tmp_path, extra)
    assert proxy.connections >= 1 and proxy.first_lines[0].startswith(b"CONNECT loop.test:"), proxy.first_lines
    assert target.connections == 0 and target.marker_bytes == 0 and proxy.marker_bytes == 0
