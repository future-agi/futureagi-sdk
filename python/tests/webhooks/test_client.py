"""The webhooks client against the REST contract (unit level: an ``httpx.MockTransport`` stands in for the API).

The end-to-end proof drives the CLI against the platform; these tests pin what each method sends (method, path, query, body),
how answers are unwrapped and how refusals are raised, for the sync and the async client alike."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from fi.errors import FutureAGIAPIError, NotFoundError, PermissionDeniedError, RateLimitError
from fi.webhooks import AsyncWebhooks, Endpoint, Rotation, TestResult, Webhooks

BASE = "http://fa.test"
EP = {
    "id": "whep_01",
    "kind": "http",
    "name": "hooks.acme.ai",
    "status": "enabled",
    "url_host": "hooks.acme.ai",
    "url": "https://hooks.acme.ai/fi",
    "subscriptions": [{"event_type": "prompt.label.changed", "filters": {}}],
    "health": None,
}
SECRET = "whsec_AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="


class Fake:
    """Records every request; answers from a route table ``(method, path) -> (status, body, headers)``."""

    def __init__(self, routes):
        self.routes = routes
        self.seen = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        self.seen.append((request.method, request.url.path, dict(request.url.params), body, request.headers))
        status, payload, headers = self.routes[(request.method, request.url.path)]
        if callable(payload):
            status, payload = payload(len(self.seen))
        return httpx.Response(status, json=payload, headers=headers or {})


def ok(result, status=200):
    return status, {"status": True, "result": result}, None


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "k-test")
    monkeypatch.setenv("FI_SECRET_KEY", "s-test")
    monkeypatch.setenv("FI_BASE_URL", BASE)
    monkeypatch.delenv("FI_WORKSPACE_ID", raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")


def client(fake, **kw):
    return Webhooks(transport=httpx.MockTransport(fake), retries=2, **kw)


def test_create_sends_the_contract_body_and_returns_the_secret_once(env):
    fake = Fake({("POST", "/webhooks/endpoints/"): ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201)})
    with client(fake) as wh:
        ep = wh.endpoints.create(
            url="https://hooks.acme.ai/fi",
            events=["prompt.label.changed"],
            filters={"prompt.label.changed": {"label_names": ["Production"], "actions": ["moved", "assigned"]}},
            headers={"X-Env": "${NOT_EXPANDED}"},
            payload="thin",
            timeout_s=10,
            max_age="24h",
        )
    method, path, params, body, headers = fake.seen[0]
    assert (method, path) == ("POST", "/webhooks/endpoints/")
    assert body == {
        "url": "https://hooks.acme.ai/fi",
        "name": "hooks.acme.ai",
        "subscriptions": [{"event_type": "prompt.label.changed",
                           "filters": {"label_names": ["Production"], "actions": ["moved", "assigned"]}}],
        "headers": {"X-Env": "${NOT_EXPANDED}"},
        "payload_mode": "thin",
        "timeout_ms": 10000,
        "max_age_s": 86400,
    }
    assert headers["x-api-key"] == "k-test" and headers["x-secret-key"] == "s-test"
    assert isinstance(ep, Endpoint) and ep.id == "whep_01" and ep.secret == SECRET and ep["warnings"] == []
    assert SECRET not in repr(ep) and ep.secret[-4:] in repr(ep)


def test_create_org_wide_and_workspace(env):
    fake = Fake({("POST", "/webhooks/endpoints/"): ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201)})
    with client(fake) as wh:
        wh.endpoints.create(url="https://h.acme.ai/x", events=["prompt.*"], org_wide=True, name="n")
        wh.endpoints.create(url="https://h.acme.ai/x", events=["prompt.*"], workspace_id="ws-1", name="n")
        wh.endpoints.create(url="https://h.acme.ai/x", events=["prompt.*"], name="n")
    assert fake.seen[0][3]["workspace_id"] is None
    assert fake.seen[1][3]["workspace_id"] == "ws-1"
    assert "workspace_id" not in fake.seen[2][3]


def test_reads_and_the_list_query(env):
    fake = Fake({
        ("GET", "/webhooks/endpoints/"): ok({"results": [EP]}),
        ("GET", "/webhooks/endpoints/whep_01/"): ok(EP),
        ("GET", "/webhooks/endpoints/whep_01/deliveries/"): ok({"results": [], "next_cursor": None}),
        ("GET", "/webhooks/deliveries/dlv_1/"): ok({"id": "dlv_1", "attempts": []}),
        ("GET", "/webhooks/events/"): ok({"results": [], "next_cursor": "c2"}),
        ("GET", "/webhooks/event-types/"): ok({"results": [], "groups": [], "shared_schemas": {}}),
    })
    with client(fake) as wh:
        eps = wh.endpoints.list(event_type="prompt.label.changed", status="enabled")
        assert [e.id for e in eps] == ["whep_01"] and isinstance(eps[0], Endpoint)
        assert wh.endpoints.get("whep_01").url_host == "hooks.acme.ai"
        page = wh.deliveries.list(endpoint="whep_01", status="failed", since="2026-10-22T00:00:00Z", seq_from=42,
                                  seq_to=42, limit=5)
        assert page.results == [] and page.has_more is False
        assert wh.deliveries.get("dlv_1").attempts == []
        assert "attempts" not in wh.deliveries.get("dlv_1", attempts=False)
        assert wh.events.list(type="deployment.run.failed", since="24h").next_cursor == "c2"
        assert wh.event_types()["groups"] == []
    assert fake.seen[0][2] == {"event_type": "prompt.label.changed", "status": "enabled"}
    assert fake.seen[2][2] == {"status": "failed", "since": "2026-10-22T00:00:00Z", "seq_from": "42",
                               "seq_to": "42", "limit": "5"}
    import datetime as dt

    since = dt.datetime.fromisoformat(fake.seen[5][2]["since"].replace("Z", "+00:00"))
    ago = dt.datetime.now(dt.timezone.utc) - since
    assert dt.timedelta(hours=23, minutes=59) < ago < dt.timedelta(hours=24, minutes=1)
    assert fake.seen[5][2]["type"] == "deployment.run.failed"


def test_operations_paths_and_bodies(env):
    fake = Fake({
        ("POST", "/webhooks/endpoints/whep_01/enable/"): ok(EP),
        ("POST", "/webhooks/endpoints/whep_01/resume/"): ok({"mode": "send", "sent": 3, "skipped": 0,
                                                               "past_max_age": 0, "backlog_capped": 0}),
        ("POST", "/webhooks/endpoints/whep_01/disable/"): ok({**EP, "status": "disabled_manual"}),
        ("POST", "/webhooks/endpoints/whep_01/rotate-secret/"): ok({"secret": SECRET, "id": "whk_2", "tail": "Hh8=",
                                                                     "previous": {"tail": "AAAA", "expires_at": "x"},
                                                                     "revoked_tails": []}),
        ("POST", "/webhooks/endpoints/whep_01/revoke-previous-secret/"): ok({"revoked_tails": ["AAAA"]}),
        ("PATCH", "/webhooks/endpoints/whep_01/"): ok(EP),
        ("DELETE", "/webhooks/endpoints/whep_01/"): ok({"deleted": True, "id": "whep_01", "cancelled_deliveries": 2}),
        ("POST", "/webhooks/deliveries/dlv_1/redeliver/"): ok({"delivery_id": "dlv_1", "queued": True, "attempt": 2},
                                                              202),
        ("POST", "/webhooks/deliveries/redeliver/"): ok({"count": 25, "queued": 0, "expired": 0, "dry_run": True}),
    })
    with client(fake) as wh:
        assert wh.endpoints.enable("whep_01", resume="send").sent == 3
        assert wh.endpoints.disable("whep_01", reason="maintenance").status == "disabled_manual"
        rot = wh.endpoints.rotate_secret("whep_01", overlap="24h")
        assert isinstance(rot, Rotation) and rot.previous_tail == "AAAA" and rot.previous_expires_at == "x"
        assert wh.endpoints.revoke_previous_secret("whep_01").revoked_tails == ["AAAA"]
        wh.endpoints.update("whep_01", timeout_s=10, clear_headers=True)
        assert wh.endpoints.delete("whep_01").cancelled_deliveries == 2
        assert wh.deliveries.redeliver("dlv_1").attempt == 2
        assert wh.deliveries.redeliver_many(endpoint="whep_01", status="failed", dry_run=True).count == 25
    bodies = {(m, p): b for m, p, _, b, _ in fake.seen}
    assert bodies[("POST", "/webhooks/endpoints/whep_01/enable/")] == {}
    assert bodies[("POST", "/webhooks/endpoints/whep_01/resume/")] == {"mode": "send"}
    assert bodies[("POST", "/webhooks/endpoints/whep_01/disable/")] == {"reason": "maintenance"}
    assert bodies[("POST", "/webhooks/endpoints/whep_01/rotate-secret/")] == {"overlap_seconds": 86400}
    assert bodies[("PATCH", "/webhooks/endpoints/whep_01/")] == {"timeout_ms": 10000, "headers": None}
    assert bodies[("POST", "/webhooks/deliveries/redeliver/")] == {"endpoint": "whep_01", "status": "failed",
                                                                    "dry_run": True}


def test_rotate_overlap_bounds_and_update_guards(env):
    with client(Fake({})) as wh:
        with pytest.raises(ValueError):
            wh.endpoints.rotate_secret("whep_01", overlap="8d")
        with pytest.raises(ValueError):
            wh.endpoints.update("whep_01")
        with pytest.raises(ValueError):
            wh.endpoints.update("whep_01", headers={"A": "b"}, clear_headers=True)
        with pytest.raises(ValueError):
            wh.endpoints.get("../policy")


def test_test_delivery_settled_and_pending(env):
    settled = {"event_id": "evt_test_1", "delivery_id": "dlv_t", "status_code": 500, "outcome": "http_error",
               "latency_ms": 12, "response_excerpt": "boom"}
    fake = Fake({("POST", "/webhooks/endpoints/whep_01/test/"):
                 (0, lambda n: (200, {"status": True, "result": settled}) if n == 1 else
                  (202, {"status": True, "result": {"event_id": "evt_test_2", "delivery_id": "dlv_u"}}), None)})
    with client(fake) as wh:
        r = wh.endpoints.test("whep_01", event_type="prompt.label.changed")
        assert isinstance(r, TestResult) and r.settled and not r.ok and r.status_code == 500
        r2 = wh.endpoints.test("whep_01", event_type="prompt.label.changed")
        assert not r2.settled and r2.delivery_id == "dlv_u"
    assert fake.seen[0][3] == {"event_type": "prompt.label.changed"}


def test_refusals_carry_the_webhook_code_and_the_status_class(env):
    def refuse(status, code, attr=None, headers=None):
        body = {"status": False, "type": "validation_error", "code": code, "message": f"{code} text",
                "detail": f"{code} text", "error": f"{code} text", "result": f"{code} text"}
        if attr:
            body["attr"] = attr
        return status, body, headers

    fake = Fake({
        ("POST", "/webhooks/endpoints/"): refuse(400, "WEBHOOK_URL_UNSAFE_ADDRESS", "url"),
        ("GET", "/webhooks/endpoints/whep_x/"): refuse(404, "WEBHOOK_NOT_FOUND"),
        ("POST", "/webhooks/endpoints/whep_01/disable/"): refuse(403, "WEBHOOK_FORBIDDEN"),
        ("POST", "/webhooks/endpoints/whep_01/test/"): refuse(429, "WEBHOOK_TEST_RATE_LIMITED", None,
                                                               {"Retry-After": "0"}),
    })
    with client(fake) as wh:
        with pytest.raises(FutureAGIAPIError) as err:
            wh.endpoints.create(url="https://169.254.169.254/", events=["prompt.*"], name="m")
        assert err.value.status_code == 400 and err.value.code == "WEBHOOK_URL_UNSAFE_ADDRESS"
        assert err.value.attr == "url" and str(err.value).startswith("WEBHOOK_URL_UNSAFE_ADDRESS: ")
        assert "(url) [HTTP 400]" in str(err.value)
        with pytest.raises(NotFoundError) as nf:
            wh.endpoints.get("whep_x")
        assert nf.value.code == "WEBHOOK_NOT_FOUND"
        with pytest.raises(PermissionDeniedError):
            wh.endpoints.disable("whep_01")
        with pytest.raises(RateLimitError) as rl:
            wh.endpoints.test("whep_01", event_type="prompt.label.changed")
        assert rl.value.code == "WEBHOOK_TEST_RATE_LIMITED"
    # the create was sent once (a write), the 429 test three times (429 retries on every method; retries=2)
    assert [p for _, p, *_ in fake.seen].count("/webhooks/endpoints/") == 1
    assert [p for _, p, *_ in fake.seen].count("/webhooks/endpoints/whep_01/test/") == 3


def test_a_write_is_not_retried_after_a_5xx_but_a_read_is(env):
    fake = Fake({
        ("POST", "/webhooks/endpoints/"): (503, {"status": False, "message": "busy"}, None),
        ("GET", "/webhooks/endpoints/"): (0, lambda n: (503, {"m": "busy"}) if n < 4 else
                                          (200, {"status": True, "result": {"results": []}}), None),
    })
    wh = Webhooks(transport=httpx.MockTransport(fake), retries=2)
    wh._http._transport.backoff_base_s = 0  # no sleeps in the unit test
    with pytest.raises(FutureAGIAPIError) as err:
        wh.endpoints.create(url="https://h.acme.ai/x", events=["prompt.*"], name="n")
    assert err.value.status_code == 503 and len(fake.seen) == 1
    assert wh.endpoints.list() == [] and len(fake.seen) == 4


def test_redirects_are_never_followed(env):
    fake = Fake({("GET", "/webhooks/endpoints/"): (302, {}, {"Location": "http://elsewhere.test/steal"})})
    with client(fake) as wh, pytest.raises(FutureAGIAPIError) as err:
        wh.endpoints.list()
    assert err.value.status_code == 302 and len(fake.seen) == 1


def test_workspace_header_from_argument_and_saved_keys_rule(env, monkeypatch):
    fake = Fake({("GET", "/webhooks/endpoints/"): ok({"results": []})})
    with client(fake, workspace_id="ws-9") as wh:
        wh.endpoints.list()
    assert fake.seen[0][4]["x-workspace-id"] == "ws-9"
    monkeypatch.delenv("FI_API_KEY")
    monkeypatch.delenv("FI_SECRET_KEY")
    from fi.errors import AuthError

    with client(Fake({})) as wh, pytest.raises(AuthError):
        wh.endpoints.list()


def test_async_client_has_the_same_surface(env):
    fake = Fake({
        ("GET", "/webhooks/endpoints/"): ok({"results": [EP]}),
        ("POST", "/webhooks/endpoints/whep_01/enable/"): ok(EP),
        ("POST", "/webhooks/endpoints/whep_01/resume/"): ok({"mode": "skip", "sent": 0, "skipped": 4,
                                                               "past_max_age": 0, "backlog_capped": 0}),
    })

    async def run():
        async with AsyncWebhooks(transport=httpx.MockTransport(fake)) as wh:
            eps = await wh.endpoints.list()
            out = await wh.endpoints.enable("whep_01", resume="skip")
            return eps, out

    eps, out = asyncio.run(run())
    assert eps[0].id == "whep_01" and out.skipped == 4
    assert [(m, p) for m, p, *_ in fake.seen] == [("GET", "/webhooks/endpoints/"),
                                                  ("POST", "/webhooks/endpoints/whep_01/enable/"),
                                                  ("POST", "/webhooks/endpoints/whep_01/resume/")]


def test_every_contract_operation_has_a_client_method():
    """The 24 operations of the webhooks OpenAPI contract (19 paths) map to client calls."""
    from fi.webhooks import _api

    calls = [
        _api.list_endpoints(), _api.create_endpoint({}), _api.get_endpoint("e"), _api.update_endpoint("e", {}),
        _api.delete_endpoint("e"), _api.toggle("e", True, None), _api.toggle("e", False, None),
        _api.resume("e", "send"), _api.rotate_secret("e", None, None), _api.revoke_previous_secret("e"),
        _api.test("e", "t"), _api.list_deliveries(), _api.list_deliveries(endpoint="e"), _api.get_delivery("d"),
        _api.redeliver("d"), _api.redeliver_many(endpoint="e", status="failed"), _api.list_events(),
        _api.event_types(), _api.egress_ips(), _api.preview({}), _api.get_policy(), _api.put_policy({}),
        _api.get_policy("w"), _api.put_policy({}, "w"),
    ]
    ops = {(c.method, c.path.replace("/e/", "/{endpoint_id}/").replace("/d/", "/{delivery_id}/")
            .replace("/w/", "/{workspace_id}/")) for c in calls}
    assert len(ops) == 24
