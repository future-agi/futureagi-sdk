"""The client's request specs against the webhooks OpenAPI contract of the Future AGI API.

``contract/webhooks-openapi.json`` is the webhooks part of the platform's generated OpenAPI (swagger 2.0) at
future-agi the recorded source, unchanged (sha256 pinned below).
Every operation must have exactly one client call, and every call must use a declared path, method, query parameter
and body field, so a contract change fails here before it fails a user. (The SDK writes these paths by hand until
the platform's committed ``swagger.json`` carries the webhooks routes and the SDK regenerates from it.)
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from fi.webhooks import _api

HERE = Path(__file__).resolve().parent / "contract" / "webhooks-openapi.json"
SHA256 = "fee37d031c002ba2439425ed37f4f511d680e7700abc0379f948f40dfd05f800"
SPEC = json.loads(HERE.read_bytes())
METHODS = ("get", "post", "put", "patch", "delete")


def _calls():
    full = {
        "url": "https://h.acme.ai/x", "subscriptions": [], "name": "n", "description": "d", "headers": {},
        "payload_mode": "thin", "include_people_names": True, "accepts_run_targeting": False, "timeout_ms": 5000,
        "rate_limit_per_s": 1, "max_in_flight": 1, "max_age_s": 3600, "secret": "s", "workspace_id": None,
    }
    update = {k: v for k, v in full.items() if k not in ("secret", "workspace_id")}
    return [
        _api.list_endpoints(workspace="w", event_type="prompt.*", status="enabled", kind="http"),
        _api.create_endpoint(full),
        _api.get_endpoint("e"),
        _api.update_endpoint("e", update),
        _api.delete_endpoint("e"),
        _api.toggle("e", True, "r"),
        _api.toggle("e", False, "r"),
        _api.resume("e", "send"),
        _api.rotate_secret("e", "1h", "whsec_x"),
        _api.revoke_previous_secret("e"),
        _api.test("e", "prompt.label.changed"),
        _api.list_deliveries(status="failed", event_type="prompt.label.changed", event="evt", subject="prompt:p",
                             since="2026-10-01T00:00:00Z", until="2026-10-02T00:00:00Z", seq_from=1, seq_to=2,
                             include_body=True, cursor="c", limit=5),
        _api.list_deliveries(endpoint="e", status="failed", limit=5),
        _api.get_delivery("d"),
        _api.redeliver("d"),
        _api.redeliver_many(endpoint="e", status="failed", event_type="prompt.label.changed", since="24h",
                            until="1h", dry_run=True),
        _api.list_events(type="prompt.label.changed", subject="prompt:p", since="24h", until="1h", cursor="c",
                         limit=5),
        _api.event_types(),
        _api.egress_ips(),
        _api.preview({"event_type": "prompt.label.changed", "payload_mode": "thin", "include_people_names": True,
                      "headers": {}}),
        _api.get_policy(),
        _api.put_policy({"allowed_hosts": [], "members_can_manage": True, "full_payload_allowed": False,
                         "log_retention_days": 30, "max_endpoints_per_workspace": 50}),
        _api.get_policy("w"),
        _api.put_policy({"allowed_hosts": [], "members_can_manage": True}, "w"),
    ]


def _match(path: str):
    for template, item in SPEC["paths"].items():
        pattern = "^" + re.sub(r"\{[^}]+\}", "[^/]+", template) + "$"
        if re.match(pattern, path):
            return template, item
    return None, None


def _body_schema(op):
    for p in op.get("parameters", []):
        if p.get("in") == "body":
            ref = p["schema"]["$ref"].rsplit("/", 1)[1]
            return SPEC["definitions"][ref]
    return None


def test_the_vendored_contract_is_unchanged():
    assert hashlib.sha256(HERE.read_bytes()).hexdigest() == SHA256


def test_every_call_uses_a_declared_operation_query_and_body():
    used = set()
    for call in _calls():
        template, item = _match(call.path)
        assert template, f"{call.method} {call.path} is not in the contract"
        op = item.get(call.method.lower())
        assert op, f"{call.method} {template} is not in the contract"
        used.add((call.method.lower(), template))
        declared = {p["name"] for p in op.get("parameters", []) + item.get("parameters", []) if p.get("in") == "query"}
        assert set(call.params) <= declared, (template, set(call.params) - declared)
        schema = _body_schema(op)
        if call.json is not None and schema is not None:
            assert set(call.json) <= set(schema.get("properties", {})), (template, set(call.json) - set(schema["properties"]))
            missing = set(schema.get("required", [])) - set(call.json)
            assert not missing or call.method == "PATCH", (template, missing)
        ok_codes = {int(c) for c in op["responses"] if c.isdigit()}
        assert set(call.ok) & ok_codes, (template, call.ok, ok_codes)
    every = {(m, t) for t, item in SPEC["paths"].items() for m in item if m in METHODS}
    assert used == every and len(every) == 24


def test_the_create_and_test_answers_the_client_reads_are_in_the_contract():
    d = SPEC["definitions"]
    assert set(d["EndpointCreatedOut"]["required"]) == {"endpoint", "secret", "warnings"}
    assert {"event_id", "delivery_id"} <= set(d["TestOut"]["required"])
    assert {"status_code", "outcome", "latency_ms", "response_excerpt"} <= set(d["TestOut"]["properties"])
    assert {"secret", "tail", "previous", "revoked_tails"} <= set(d["RotateOut"]["required"])
    assert set(d["DeliveryPageOut"]["required"]) == {"results", "next_cursor"}
    assert {"attempts", "request_headers"} <= set(d["DeliveryDetailOut"]["required"])
    assert {"count", "queued", "expired", "dry_run"} == set(d["BulkRedeliverOut"]["required"])
