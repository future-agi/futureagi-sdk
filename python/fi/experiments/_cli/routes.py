"""``futureagi-py doctor``'s server check for experiments: does the server have the routes an uploaded
run needs? One harmless GET per route on an id that cannot exist (nothing is created):

- a JSON answer (404 "not found", 400, 405) means the route exists;
- a non-JSON 404 (the web server's own page) means the route is missing on this server;
- 401 / 403 mean the keys were refused.

The collector is checked separately with GET /tracer/v1/traces (no spans are sent). Its 404,
including JSON, means the route is missing, not a missing object. A GET response cannot prove
that POST export works: doctor says "POST not checked". A missing collector route (HTTP 404) is
a setup problem (exit 3), also listed in doctor --json's problems. Transport exceptions are
inconclusive ("could not check"), as for the platform routes; they do not change doctor's exit code.
"""

from __future__ import annotations

from typing import Any

NIL = "00000000-0000-4000-8000-000000000000"
ROUTES = (
    ("dataset versions (snapshot, pin)", f"/model-hub/datasets/{NIL}/versions/"),
    ("experiment runs (create, ingest)", "/model-hub/experiment-runs/"),
    ("SRV-3 run read", f"/model-hub/experiment-runs/{NIL}/"),
    ("SRV-5 external metrics", f"/model-hub/datasets/{NIL}/external-metrics/"),
    ("hosted eval API (templates)", "/sdk/api/v1/get-evals/"),
)


def classify(status: int, content_type: str) -> str:
    if status in (401, 403):
        return "keys refused"
    if status < 400 or status in (400, 405, 409, 422):
        return "present"
    if status == 404:
        return "present" if "json" in content_type else "MISSING on this server"
    return f"unclear (HTTP {status})"


def route_lines(client: Any) -> list[str]:
    http = client.generated_client.get_httpx_client()
    lines = []
    for label, path in ROUTES:
        try:
            response = http.request("GET", path)
            state = classify(response.status_code, response.headers.get("content-type", ""))
        except Exception as exc:  # a route check never breaks doctor
            state = f"could not check ({type(exc).__name__})"
        lines.append(f"Route      {label:<34} {state}")
    lines.append(_collector_line(http))
    return lines


def _collector_line(http: Any) -> str:
    from fi._cli.doctor import Problem

    path = "/tracer/v1/traces"
    prefix = f"Route      trace collector {path} "
    try:
        response = http.request("GET", path)
    except Exception as exc:
        return prefix + f"could not check ({type(exc).__name__}); trace export may fail"
    status = response.status_code
    if status == 404:
        return Problem(prefix + "MISSING on this server (HTTP 404); trace export needs the collector route")
    if status in (401, 403):
        return Problem(prefix + f"keys refused (HTTP {status})")
    if status >= 500:
        return Problem(prefix + f"unavailable (HTTP {status}); trace export may fail")
    return prefix + f"GET HTTP {status}; POST not checked"


def doctor_route_lines(args: Any) -> list[str]:
    if getattr(args, "offline", False):
        return ["Routes     not checked (--offline)"]
    from fi._credentials import resolve

    creds = resolve()
    if not creds.complete:
        return ["Routes     not checked (no keys; --no-upload runs need none)"]
    from fi.futureagi_client import FutureAGIClient

    return route_lines(FutureAGIClient())


def openai_base_url_lines(args: Any) -> list[str]:
    """``OPENAI_BASE_URL``, when set: one request without a key (any HTTP answer means reachable). An
    unreachable one is a doctor problem (exit 3): judge() and OpenAI-SDK tasks would fail on every row
    (CLI-03). Unset, nothing is sent: the default endpoint is the provider's own."""
    import os
    import re

    from fi._cli.doctor import Problem

    url = os.environ.get("OPENAI_BASE_URL", "").strip()
    if not url:
        return []
    shown = re.sub(r"//[^/@]*@", "//", url)  # never print user:password@
    if getattr(args, "offline", False):
        return [f"OpenAI     OPENAI_BASE_URL={shown} (not checked: --offline)"]
    import httpx

    from fi.errors import describe_transport_error

    try:
        resp = httpx.get(url.rstrip("/") + "/models", timeout=5.0)
    except httpx.TransportError as exc:
        _, reason = describe_transport_error(exc, url)
        return [Problem(f"OpenAI     OPENAI_BASE_URL={shown} is unreachable ({reason}); judge() and OpenAI tasks "
                        "will fail. Fix OPENAI_BASE_URL, or unset it to use the provider's own endpoint")]
    except Exception as exc:  # a malformed URL
        return [Problem(f"OpenAI     OPENAI_BASE_URL={shown} cannot be used ({type(exc).__name__}: {exc})")]
    return [f"OpenAI     OPENAI_BASE_URL={shown} reachable (HTTP {resp.status_code} without a key)"]
