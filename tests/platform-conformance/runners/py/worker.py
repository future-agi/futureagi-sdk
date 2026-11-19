"""The Python side of the py runner shell: load the SDK under test by path and answer calls.

    python3 -I -B worker.py --client-py <wheel or source dir> [--binding-module dotted.name] [--allow h1,h2]

The shell (runners/sdk/run.mjs) does case selection, templating and checking once, in Node; this
worker only binds a case's SDK name to the Python SDK. Requests and replies are JSON lines:

    {"id": 1, "op": "call", "client": {...}, "sdk": {"family", "method"}, "args": {...}, "opts": {...}}
    {"id": 1, "value": ...}  or  {"id": 1, "error": {"errorClass", "status", "code", "requestId", ...}}

The egress guard is armed for the whole process BEFORE the binding is imported: the binding receives
guarded httpx transports (no_prod_egress.py, refused before httpx sees the request), and every other
client in the process, one the SDK builds itself included (httpx, urllib, requests, asyncio, an
OTLP/HTTP exporter), goes through socket.getaddrinfo / socket.socket.connect, which
no_prod_egress_process.py checks; importing grpc or pycurl (native networking) is refused. Every trip,
caught by the SDK or not, is in the guard receipt and fails the run. Limits: child processes and other
native code are outside it (README "The egress guard").
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "guards", "no-prod-egress"))

from no_prod_egress import EgressGuard  # noqa: E402
from no_prod_egress_process import install_process_guard  # noqa: E402

DEFAULT_MODULES = ("conformance_binding",)


def load_binding(client_path: str, module_name: str | None):
    sys.path.insert(0, os.path.abspath(client_path))
    candidates = (module_name,) if module_name else DEFAULT_MODULES
    errors = []
    for name in candidates:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            errors.append(f"{name}: {exc}")
            continue
        for fn in ("create_client", "call", "describe_error"):
            if not callable(getattr(module, fn, None)):
                raise SystemExit(f"{name} does not define {fn}()")
        return name, module
    raise SystemExit("no conformance binding found: " + "; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-py", required=True)
    parser.add_argument("--binding-module")
    parser.add_argument("--allow", default="")
    args = parser.parse_args()
    guard = EgressGuard(allow=[h for h in args.allow.split(",") if h])
    process_guard = install_process_guard(
        guard
    )  # before the SDK is imported, so it captures the patched socket
    name, binding = load_binding(args.client_py, args.binding_module)
    package = getattr(binding, "PACKAGE", {"module": name})
    print(
        json.dumps(
            {
                "ready": True,
                "package": {
                    **package,
                    "path": os.path.abspath(args.client_py),
                    "binding": name,
                },
            }
        ),
        flush=True,
    )
    clients: dict[str, object] = {}
    for line in sys.stdin:
        request = json.loads(line)
        rid = request["id"]
        try:
            if request["op"] == "guard":
                reply = {
                    "id": rid,
                    "value": {**guard.receipt(), "process": process_guard.describe()},
                }
            elif request["op"] == "clientCase":
                fn = getattr(binding, "client_case", None)
                reply = {
                    "id": rid,
                    "value": fn(request["spec"], transport=guard.transport())
                    if fn
                    else {"skip": "the binding has no client_case()"},
                }
            else:
                key = json.dumps(request["client"], sort_keys=True)
                if key not in clients:
                    clients[key] = binding.create_client(
                        **request["client"],
                        transport=guard.transport(),
                        async_transport=guard.async_transport(),
                    )
                value = binding.call(
                    clients[key],
                    request["sdk"],
                    request.get("args") or {},
                    **(request.get("opts") or {}),
                )
                reply = {"id": rid, "value": value}
        except Exception as exc:  # the SDK's typed errors are described, never re-raised
            described = binding.describe_error(exc)
            reply = {
                "id": rid,
                "error": {"message": str(exc)[:300], **(described or {})},
            }
        print(json.dumps(reply, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
